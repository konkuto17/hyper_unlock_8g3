"""
Universal Hardware-Assisted Offline Bypass Orchestrator for Snapdragon 8 Gen 3 (SM8650) & 8 Gen 2 (SM8550).
Derived from research and PoC by Kernix (@Linuxoid-cn).
Implements strict anti-brick pre-flight checks, verified GPT backups, and safe restoration.
"""
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .backup import BackupManager
from .device import Fastboot, IncompatibleDeviceError, UnlockError
from .profiles import DeviceProfile, get_profile


def parse_flash_script(rom_dir: Path) -> List[List[str]]:
    """Parse fastboot commands from an official flash_all.bat script."""
    flash_bat = rom_dir / "flash_all.bat"
    if not flash_bat.is_file():
        raise UnlockError(f"Official ROM flash_all.bat not found in: {rom_dir}")

    commands = []
    for raw_line in flash_bat.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        match = re.match(r"fastboot %\* (flash|erase|set_active|reboot)(?:\s+([^|&]+?))?(?:\s*\|\|.*)?$", line)
        if not match:
            continue
        action, tail = match.groups()
        tokens = tail.split() if tail else []

        if action == "flash":
            if len(tokens) != 2 or not ("images" in tokens[1].lower()):
                raise UnlockError(f"Unrecognized flash syntax: {line}")
            img_rel = tokens[1].replace("%~dp0", "").replace("\\", "/").lstrip("/")
            img_path = (rom_dir / img_rel).resolve()
            if not img_path.is_file():
                raise UnlockError(f"Missing required ROM image file: {img_path}")
            tokens[1] = str(img_path)

        if any(x.lower() in ("frp", "lock", "unlock_critical") for x in tokens):
            continue

        commands.append([action, *tokens])

    filtered = [c for c in commands if len(c) < 2 or c[1] not in ("crclist", "sparsecrclist")]
    if not filtered or filtered[-1][0] != "reboot":
        raise UnlockError("Incomplete official ROM flash script.")
    return filtered


class OfflineBypassEngine:
    """Manages the full end-to-end SM8650 and SM8550 unlock and restoration lifecycle."""

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path(__file__).parent.parent
        self.items_dir = self.root_dir / "items"
        self.payload_dir = self.root_dir / "payload"
        self.backup_mgr = BackupManager(self.root_dir / "backups")

    def get_payload_path(self, profile: DeviceProfile) -> Path:
        """Resolve model-specific payload path (8gen3-Ennea.img or 8550-Ennea.img)."""
        payload = self.payload_dir / profile.payload_name
        if not payload.is_file():
            raise UnlockError(f"Universal payload missing at: {payload}")
        return payload

    def get_gpt_files(self, profile: DeviceProfile) -> Tuple[Path, Path]:
        """Resolve unlock and stock GPT binaries for target device profile."""
        dev_items = self.items_dir / profile.items_folder
        if not dev_items.is_dir():
            raise UnlockError(f"GPT items directory missing for {profile.commercial_name}: {dev_items}")

        # Search for either naming convention
        unlock_gpt = dev_items / "blgpt_both4.bin"
        if not unlock_gpt.is_file():
            unlock_gpt = dev_items / "unlockgpt_both4.bin"
        if not unlock_gpt.is_file():
            raise UnlockError(f"Missing unlock GPT binary in {dev_items}")

        stock_gpt = dev_items / "gpt_both4.bin"
        if not stock_gpt.is_file():
            raise UnlockError(f"Missing stock GPT binary in {dev_items}")

        return unlock_gpt, stock_gpt

    def get_device_profile(self, fb: Fastboot) -> Tuple[DeviceProfile, Dict[str, str]]:
        """Verify device compatibility and return its profile."""
        info = fb.inspect()
        product = info.get("product")
        if not product:
            raise UnlockError("Unable to identify connected device product string.")

        profile = get_profile(product)
        if not profile:
            raise IncompatibleDeviceError(
                f"Device '{product}' is not in the Snapdragon 8 Gen 3 / 8 Gen 2 database.\n"
                "Refusing to execute bypass to prevent hard brick."
            )

        if info.get("is-userspace") == "yes":
            raise UnlockError("Device is in fastbootd (userspace). Please reboot into native bootloader Fastboot.")

        return profile, info

    def verify_rom_directory(self, rom_dir: Path, expected_anti: str = "1") -> List[List[str]]:
        """Validate official Fastboot ROM folder and verify anti-rollback."""
        commands = parse_flash_script(rom_dir)
        anti_txt = rom_dir / "images" / "anti_version.txt"
        if anti_txt.is_file():
            anti_val = anti_txt.read_text().strip()
            if anti_val and int(anti_val) < int(expected_anti):
                raise UnlockError(
                    f"Anti-rollback conflict: ROM anti-version ({anti_val}) is lower than device anti ({expected_anti}).\n"
                    "Flashing this ROM will brick the device!"
                )
        return commands

    def execute_commands(
        self,
        fb: Fastboot,
        commands: List[List[str]],
        callback: Optional[Callable[[int, int, List[str]], None]] = None,
    ) -> None:
        """Execute sequence of fastboot commands with live progress reporting."""
        total = len(commands)
        for idx, cmd in enumerate(commands, 1):
            if callback:
                callback(idx, total, cmd)
            code, output = fb.run(*cmd, checked=False, timeout=900)
            if code != 0 or "FAILED" in output:
                raise UnlockError(f"Execution failed at step [{idx}/{total}] ({' '.join(cmd)}):\n{output.strip()}")

    def run_stage_payload(
        self,
        fb: Fastboot,
        profile: DeviceProfile,
        progress_cb: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Stage 1: Flash custom GPT and boot Ennea unlock payload."""
        unlock_gpt, stock_gpt = self.get_gpt_files(profile)
        payload_file = self.get_payload_path(profile)

        # Step A: Mandatory Backup
        if progress_cb:
            progress_cb("Creating pre-flash backup of partition:4...")
        serial = fb.serial or "unknown_device"
        self.backup_mgr.create_gpt_backup(fb, serial, stock_gpt)

        # Step B: Flash Unlock GPT
        if progress_cb:
            progress_cb(f"Flashing custom LUN4 partition table ({unlock_gpt.name})...")
        fb.run("flash", "partition:4", str(unlock_gpt.resolve()), checked=True)

        # Step C: Boot Ennea Payload
        if progress_cb:
            progress_cb(f"Booting {profile.soc} Ennea payload ({payload_file.name})...")
        fb.run("boot", str(payload_file.resolve()), checked=True)

    def run_stage_restore(
        self,
        fb: Fastboot,
        profile: DeviceProfile,
        rom_dir: Path,
        progress_cb: Optional[Callable[[str], None]] = None,
        cmd_cb: Optional[Callable[[int, int, List[str]], None]] = None,
    ) -> None:
        """Stage 2: Restore stock GPT and flash full official ROM."""
        info = fb.inspect()
        if info.get("unlocked") != "yes":
            raise UnlockError("Device bootloader is not in unlocked state. Payload may have failed.")

        # Step A: Restore Stock GPT
        _, stock_gpt = self.get_gpt_files(profile)
        if progress_cb:
            progress_cb(f"Restoring stock partition:4 GPT ({stock_gpt.name})...")
        self.backup_mgr.restore_gpt(fb, stock_gpt)

        # Step B: Validate and flash official ROM
        if progress_cb:
            progress_cb("Validating official Fastboot ROM package...")
        commands = self.verify_rom_directory(rom_dir, expected_anti=info.get("anti", "1"))

        if progress_cb:
            progress_cb(f"Flashing official firmware ({len(commands)} components)...")
        self.execute_commands(fb, commands, callback=cmd_cb)
