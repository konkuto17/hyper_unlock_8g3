"""Official Xiaomi Server Unlock Client."""
import hashlib
import json
import re
import secrets
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .device import Fastboot, UnlockError
from .protocol import send_signed_request

DATA_CENTERS = {
    "China": "https://unlock.update.miui.com",
    "Singapore": "https://unlock.update.intl.miui.com",
    "India": "https://in-unlock.update.intl.miui.com",
    "Russia": "https://ru-unlock.update.intl.miui.com",
    "Europe": "https://eu-unlock.update.intl.miui.com",
}

EUROPE_REGIONS = set(
    "AT BE BG HR CY CZ DK EE FI FR DE EL HU IS IE IT LV LI LT LU MT NL NO PL PT RO SK SI ES SE UK GB".split()
)


def choose_zone(region: Optional[str]) -> str:
    """Choose appropriate data center zone based on account region."""
    if not region:
        return "Singapore"
    region = region.upper()
    if region in ("CN", "IN", "RU"):
        return {"CN": "China", "IN": "India", "RU": "Russia"}[region]
    if region in EUROPE_REGIONS:
        return "Europe"
    return "Singapore"


def check_response(result: Dict[str, Any]) -> Dict[str, Any]:
    """Check Xiaomi API response for errors and diagnostic codes."""
    if not isinstance(result, dict):
        raise UnlockError("Invalid server response format.")
    if "error" in result:
        raise UnlockError(f"Xiaomi API: {result['error']}")
    if result.get("code") != 0:
        summary = {
            k: result[k]
            for k in ("code", "descEN", "description", "desc", "waitTime", "waitHours")
            if k in result
        }
        hint = ""
        code = result.get("code")
        if code == 20045:
            hint = (
                "\n[Code 20045]: Account registration region and phone sales region do not match.\n"
                "Changing --zone only selects a data center; it does not change account "
                "registration or phone sales region.\n"
                "-> Tip: For China mainland Snapdragon 8 Gen 3 devices, use offline bypass mode: 'uv run python main.py offline'"
            )
        elif code == 20036:
            wait_hours = (
                result.get("data", {}).get("waitHour")
                or result.get("waitHours")
                or result.get("waitTime")
                or "N/A"
            )
            hint = f"\n[Code 20036]: Xiaomi requires a waiting period. Please wait {wait_hours} hours."
        raise UnlockError("Xiaomi Server rejected unlock request: " + json.dumps(summary, ensure_ascii=False) + hint)
    return result


class OfficialUnlockClient:
    """Orchestrates official unlock signature requests via Xiaomi Account servers."""

    def __init__(self, fb: Fastboot, zone: str = "Singapore"):
        self.fb = fb
        self.zone = zone
        self.domain = DATA_CENTERS.get(zone, DATA_CENTERS["Singapore"])

    def request_signature(self, service: Dict[str, Any], product: str) -> bytes:
        """Request signed unlock ticket from Xiaomi server."""
        cookies = service.get("cookies", {})
        security = service.get("servicedata", {})
        ssecurity = security.get("ssecurity")
        user_id = cookies.get("userId")
        device_id = security.get("deviceId", "")

        if not ssecurity or not user_id:
            raise UnlockError("Service session is missing userId or ssecurity; please log in again.")

        def send(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
            resp = send_signed_request(
                path=path,
                params_raw=body,
                domain=self.domain,
                ssecurity=ssecurity,
                cookies=cookies,
            )
            return check_response(resp)

        # Step 1: Request fresh nonce
        rand_str = "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(16))
        nonce_resp = send("/api/v2/nonce", {"r": rand_str})
        nonce = nonce_resp.get("nonce")
        if not isinstance(nonce, str) or not nonce:
            raise UnlockError("Server returned invalid or empty nonce.")

        # Step 2: Query device clear status
        send("/api/v2/unlock/device/clear", {
            "appId": "1",
            "data": {"product": product},
            "nonce": nonce,
        })

        # Step 3: Fetch token from fastboot
        token = self.fb.token()
        pcid = hashlib.md5(device_id.encode()).hexdigest() if device_id else ""

        result = send("/api/v3/ahaUnlock", {
            "appId": "1",
            "nonce": nonce,
            "data": {
                "clientId": "2",
                "clientVersion": "7.6.727.43",
                "deviceInfo": {
                    "boardVersion": "",
                    "deviceName": "",
                    "product": product,
                    "socId": "",
                },
                "deviceToken": token,
                "language": "en",
                "operate": "unlock",
                "pcId": pcid,
                "region": "",
                "uid": user_id,
            },
        })

        encoded = result.get("encryptData")
        if not isinstance(encoded, str) or not re.fullmatch(r"(?:[0-9a-fA-F]{2})+", encoded) or len(encoded) > 131072:
            raise UnlockError("Server returned invalid or empty encryptData signature.")

        return bytes.fromhex(encoded)

    def unlock(self, signature: bytes) -> bool:
        """Stage signature and send unlock command to device."""
        filename = None
        try:
            with tempfile.NamedTemporaryFile(prefix="hyperunlock-sig-", suffix=".bin", delete=False) as handle:
                filename = handle.name
                handle.write(signature)

            self.fb.run("stage", filename, timeout=60)
            self.fb.run("oem", "unlock", timeout=120)

            status = self.fb.inspect()
            return status.get("unlocked") == "yes"
        finally:
            if filename:
                Path(filename).unlink(missing_ok=True)
