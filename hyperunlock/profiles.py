"""Device profiles and compatibility database for Snapdragon 8 Gen 3 (SM8650) and 8 Gen 2 (SM8550)."""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class DeviceProfile:
    codename: str
    commercial_name: str
    soc: str
    items_folder: str
    payload_name: str = "8gen3-Ennea.img"
    max_patch_date: Optional[str] = None  # None means unconstrained (or 8G3 standard)
    description: str = ""


# Supported Snapdragon Devices Database (SM8650 and SM8550)
SUPPORTED_DEVICES: Dict[str, DeviceProfile] = {
    # --- Snapdragon 8 Gen 3 (SM8650) Flagships ---
    "aurora": DeviceProfile(
        codename="aurora",
        commercial_name="Xiaomi 14 Ultra",
        soc="SM8650",
        items_folder="Xiaomi14ultra",
        payload_name="8gen3-Ennea.img",
        description="Snapdragon 8 Gen 3 flagship with Leica Quad Camera (Live Verified)",
    ),
    "houji": DeviceProfile(
        codename="houji",
        commercial_name="Xiaomi 14",
        soc="SM8650",
        items_folder="Xiaomi14",
        payload_name="8gen3-Ennea.img",
        description="Snapdragon 8 Gen 3 compact flagship",
    ),
    "shennong": DeviceProfile(
        codename="shennong",
        commercial_name="Xiaomi 14 Pro",
        soc="SM8650",
        items_folder="Xiaomi14pro",
        payload_name="8gen3-Ennea.img",
        description="Snapdragon 8 Gen 3 Pro flagship",
    ),
    "manet": DeviceProfile(
        codename="manet",
        commercial_name="Redmi K70 Pro",
        soc="SM8650",
        items_folder="Redmik70pro",
        payload_name="8gen3-Ennea.img",
        description="Snapdragon 8 Gen 3 performance flagship",
    ),
    "zorn": DeviceProfile(
        codename="zorn",
        commercial_name="Redmi K80",
        soc="SM8650",
        items_folder="Redmik80",
        payload_name="8gen3-Ennea.img",
        description="Snapdragon 8 Gen 3 next-gen performance device",
    ),
    "ruyi": DeviceProfile(
        codename="ruyi",
        commercial_name="Xiaomi MIX Flip",
        soc="SM8650",
        items_folder="Xiaomimixflip",
        payload_name="8gen3-Ennea.img",
        description="Snapdragon 8 Gen 3 vertical clamshell foldable",
    ),
    "goku": DeviceProfile(
        codename="goku",
        commercial_name="Xiaomi MIX Fold 4",
        soc="SM8650",
        items_folder="Xiaomimixfold4",
        payload_name="8gen3-Ennea.img",
        description="Snapdragon 8 Gen 3 ultra-thin horizontal foldable",
    ),

    # --- Snapdragon 8 Gen 2 (SM8550) Devices ---
    "sheng": DeviceProfile(
        codename="sheng",
        commercial_name="Xiaomi Pad 6S Pro",
        soc="SM8550",
        items_folder="Xiaomipad6spro",
        payload_name="8550-Ennea.img",
        max_patch_date="2026-02-01",
        description="Snapdragon 8 Gen 2 flagship productivity tablet",
    ),
    "fuxi": DeviceProfile(
        codename="fuxi",
        commercial_name="Xiaomi 13",
        soc="SM8550",
        items_folder="Xiaomi13",
        payload_name="8550-Ennea.img",
        max_patch_date="2026-02-01",
        description="Snapdragon 8 Gen 2 compact flagship",
    ),
    "nuwa": DeviceProfile(
        codename="nuwa",
        commercial_name="Xiaomi 13 Pro",
        soc="SM8550",
        items_folder="Xiaomi13pro",
        payload_name="8550-Ennea.img",
        max_patch_date="2026-02-01",
        description="Snapdragon 8 Gen 2 Pro flagship with 1-inch sensor",
    ),
    "ishtar": DeviceProfile(
        codename="ishtar",
        commercial_name="Xiaomi 13 Ultra",
        soc="SM8550",
        items_folder="Xiaomi13ultra",
        payload_name="8550-Ennea.img",
        max_patch_date="2026-02-01",
        description="Snapdragon 8 Gen 2 Ultra camera flagship",
    ),
    "socrates": DeviceProfile(
        codename="socrates",
        commercial_name="Redmi K60 Pro",
        soc="SM8550",
        items_folder="Redmik60pro",
        payload_name="8550-Ennea.img",
        max_patch_date="2026-02-01",
        description="Snapdragon 8 Gen 2 flagship killer",
    ),
    "vermeer": DeviceProfile(
        codename="vermeer",
        commercial_name="Redmi K70",
        soc="SM8550",
        items_folder="Redmik70",
        payload_name="8550-Ennea.img",
        max_patch_date="2026-02-01",
        description="Snapdragon 8 Gen 2 value flagship",
    ),
}


def get_profile(codename: str) -> Optional[DeviceProfile]:
    """Retrieve device profile by Fastboot product/codename (case-insensitive)."""
    if not codename:
        return None
    cleaned = codename.strip().lower()
    # Strip common suffixes like _global or _pro
    base = cleaned.split("_")[0]
    return SUPPORTED_DEVICES.get(cleaned) or SUPPORTED_DEVICES.get(base)


def is_supported(codename: str) -> bool:
    """Check if codename is in the supported device database."""
    return get_profile(codename) is not None


def list_profiles(soc: Optional[str] = None) -> List[DeviceProfile]:
    """Return list of supported device profiles, optionally filtered by SoC."""
    if soc:
        return [p for p in SUPPORTED_DEVICES.values() if p.soc.upper() == soc.upper()]
    return list(SUPPORTED_DEVICES.values())
