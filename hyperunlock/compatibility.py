"""Read-only Android assessment. Recognition is not permission to flash."""
import argparse
from datetime import date
import json
from pathlib import Path

from .device import ADB, UnlockError

SOURCE = "https://github.com/Linuxoid-cn/Mi8G2-Unlocker"
PATCH_LIMIT = date(2026, 2, 1)
PROPERTIES = (
    "ro.product.model", "ro.product.device", "ro.soc.model",
    "ro.build.version.incremental", "ro.build.version.security_patch",
    "ro.boot.flash.locked", "ro.boot.verifiedbootstate",
)


def assess(properties):
    result = {
        "properties": properties,
        "offline_unlock_enabled": False,
        "source": SOURCE,
        "upstream_patch_limit": PATCH_LIMIT.isoformat(),
    }
    if properties.get("ro.product.device") != "sheng" or properties.get("ro.soc.model") != "SM8550":
        result.update(status="unrecognized", reason="This assessment only covers sheng / SM8550.")
        return result
    try:
        patch = date.fromisoformat(properties.get("ro.build.version.security_patch", ""))
    except (ValueError, TypeError):
        result.update(status="unknown_patch", reason="A valid device security patch date is required.")
        return result
    if patch > PATCH_LIMIT:
        result.update(status="blocked_patch", reason="Installed patch exceeds Mi8G2's published compatibility limit.")
    else:
        result.update(status="needs_validation", reason="Patch date passes only one prerequisite; firmware, live backups and SM8550 assets still need verification.")
    return result


def inspect_android(serial=None):
    adb = ADB()
    code, output = adb.run("devices")
    if code:
        raise UnlockError(output.strip())
    devices = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 2:
            devices[parts[0]] = parts[1]
    if serial is None:
        if len(devices) != 1:
            raise UnlockError("Connect exactly one Android device or specify --serial.")
        serial = next(iter(devices))
    if devices.get(serial) != "device":
        raise UnlockError("Selected device is absent, offline, or awaiting USB debugging authorization.")
    adb.serial = serial
    properties = {}
    for name in PROPERTIES:
        code, output = adb.run("shell", "getprop", name)
        if code:
            raise UnlockError(f"Cannot read {name}: {output.strip()}")
        properties[name] = output.strip()
    return assess(properties)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = inspect_android(args.serial)
    except UnlockError as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
