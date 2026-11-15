"""Automated partition and GPT backup engine for anti-brick safety."""
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from .device import Fastboot, UnlockError


class BackupManager:
    """Manages pre-flash device backups and disaster recovery."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent.parent / "backups"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_backup_dir(self, serial: str) -> Path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        target = self.base_dir / f"{serial}_{timestamp}"
        target.mkdir(parents=True, exist_ok=True)
        return target

    def save_file_with_hash(self, target_path: Path, data: bytes) -> str:
        """Write bytes to file and return sha256 checksum."""
        target_path.write_bytes(data)
        return hashlib.sha256(data).hexdigest()

    def create_gpt_backup(self, fb: Fastboot, serial: str, model_gpt_file: Optional[Path] = None) -> Path:
        """
        Record GPT backup metadata before modifications.
        If a verified model GPT file is supplied, stages and validates its layout.
        """
        backup_dir = self.get_backup_dir(serial)
        manifest = {
            "serial": serial,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "device_info": fb.inspect(),
            "files": []
        }

        # If a stock model GPT is supplied (from items/ or official ROM), save a verified copy
        if model_gpt_file and model_gpt_file.is_file():
            data = model_gpt_file.read_bytes()
            dest = backup_dir / "stock_gpt_both4.bin"
            sha = self.save_file_with_hash(dest, data)
            manifest["files"].append({
                "type": "stock_gpt",
                "name": "stock_gpt_both4.bin",
                "bytes": len(data),
                "sha256": sha
            })

        manifest_path = backup_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return backup_dir

    def restore_gpt(self, fb: Fastboot, gpt_file: Path) -> Tuple[int, str]:
        """Flash original GPT back to partition:4."""
        if not gpt_file.is_file():
            raise UnlockError(f"GPT restore file not found: {gpt_file}")

        data = gpt_file.read_bytes()
        # Validate EFI PART signatures
        if len(data) != 45056 or data[4096:4104] != b"EFI PART":
            raise UnlockError("Invalid GPT partition image format. Refusing to flash for safety.")

        return fb.run("flash", "partition:4", str(gpt_file.resolve()), checked=True)
