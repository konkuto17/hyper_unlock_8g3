"""Device abstraction for Fastboot and ADB communication with robust error checking."""
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class UnlockError(Exception):
    """Base exception for all HyperUnlock errors."""
    pass


class DeviceNotFoundError(UnlockError):
    """Raised when no compatible Fastboot/ADB device is connected."""
    pass


class IncompatibleDeviceError(UnlockError):
    """Raised when a connected device does not match supported profiles."""
    pass


def parse_var(output: str, name: str) -> str:
    """Parse Fastboot getvar output format: '(bootloader) name: value' or 'name: value'."""
    pattern = rf"^(?:\(bootloader\)\s*)?{re.escape(name)}:\s*(.*?)\s*$"
    matches = re.findall(pattern, output, re.MULTILINE | re.IGNORECASE)
    return matches[-1].strip() if matches else ""


class Fastboot:
    """Encapsulates Fastboot binary calls with timeout and retry controls."""

    def __init__(self, executable: Optional[str] = None, serial: Optional[str] = None):
        candidates = [
            executable,
            shutil.which("fastboot"),
            r"C:\Binaries\platform-tools\fastboot.exe",
            str(Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "fastboot.exe"),
            str(Path(__file__).parent.parent / "platform-tools" / "fastboot.exe"),
        ]
        self.executable = next((str(Path(p).resolve()) for p in candidates if p and Path(p).is_file()), None)
        if not self.executable:
            raise UnlockError("Fastboot executable not found. Please install Android Platform-Tools and add to PATH.")
        self.serial = serial

    def run(self, *args: str, checked: bool = True, timeout: int = 30) -> Tuple[int, str]:
        """Execute a fastboot command with arguments."""
        cmd = [self.executable]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout)
        except subprocess.TimeoutExpired:
            raise UnlockError(f"Fastboot command timed out after {timeout}s: {' '.join(cmd)}") from None
        except Exception as e:
            raise UnlockError(f"Failed to execute fastboot: {e}") from e

        output = (res.stdout or "") + "\n" + (res.stderr or "")
        if checked and (res.returncode != 0 or "FAILED" in output):
            raise UnlockError(f"Fastboot command failed ({' '.join(args)}):\n{output.strip()}")
        return res.returncode, output

    def getvar(self, name: str) -> str:
        """Read a single fastboot variable."""
        _, output = self.run("getvar", name, checked=False)
        return parse_var(output, name)

    def token(self) -> str:
        """Read device unlock token from bootloader."""
        for command in (("getvar", "token"), ("oem", "get_token")):
            code, output = self.run(*command, checked=False)
            token = parse_var(output, "token")
            if code == 0 and token and "FAILED" not in output:
                if len(token) > 32768 or any(c.isspace() for c in token):
                    raise UnlockError("Unexpected device token format.")
                return token
        raise UnlockError("Could not retrieve bootloader token from device.")

    def inspect(self) -> Dict[str, str]:
        """Query primary device variables."""
        _, output = self.run("getvar", "all", checked=False, timeout=10)
        # Fallback to individual variables if getvar all fails or is truncated
        product = parse_var(output, "product") or self.getvar("product")
        unlocked = parse_var(output, "unlocked") or self.getvar("unlocked")
        secure = parse_var(output, "secure") or self.getvar("secure")
        current_slot = parse_var(output, "current-slot") or self.getvar("current-slot")
        anti = parse_var(output, "anti") or self.getvar("anti")
        is_userspace = parse_var(output, "is-userspace") or self.getvar("is-userspace")

        return {
            "product": product,
            "unlocked": unlocked,
            "secure": secure,
            "current-slot": current_slot,
            "anti": anti,
            "is-userspace": is_userspace,
        }

    @classmethod
    def list_devices(cls, executable: Optional[str] = None) -> List[str]:
        """List serial numbers of all connected fastboot devices."""
        fb = cls(executable=executable)
        code, output = fb.run("devices", checked=False)
        devices = []
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "fastboot":
                devices.append(parts[0])
        return devices

    def wait_for_device(self, timeout: int = 60, interval: int = 2) -> bool:
        """Wait until device enumerates in fastboot."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            devices = self.list_devices(self.executable)
            if self.serial:
                if self.serial in devices:
                    return True
            elif devices:
                self.serial = devices[0]
                return True
            time.sleep(interval)
        return False


class ADB:
    """Helper for ADB communication while Android is running."""

    def __init__(self, executable: Optional[str] = None, serial: Optional[str] = None):
        candidates = [
            executable,
            shutil.which("adb"),
            r"C:\Binaries\platform-tools\adb.exe",
            str(Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe"),
        ]
        self.executable = next((str(Path(p).resolve()) for p in candidates if p and Path(p).is_file()), None)
        self.serial = serial

    def run(self, *args: str, timeout: int = 30) -> Tuple[int, str]:
        if not self.executable:
            raise UnlockError("ADB executable not found.")
        cmd = [self.executable]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)

        res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout)
        output = (res.stdout or "") + "\n" + (res.stderr or "")
        return res.returncode, output

    def reboot_bootloader(self) -> None:
        """Reboot device into Fastboot bootloader."""
        self.run("reboot", "bootloader")
