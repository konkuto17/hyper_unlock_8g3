import unittest
from unittest.mock import patch

from hyperunlock.compatibility import assess, inspect_android
from hyperunlock.device import UnlockError
from hyperunlock.profiles import get_profile


class CompatibilityTests(unittest.TestCase):
    def test_july_firmware_blocked(self):
        report = assess({"ro.product.device": "sheng", "ro.soc.model": "SM8550", "ro.build.version.security_patch": "2026-07-01"})
        self.assertEqual(report["status"], "blocked_patch")
        self.assertFalse(report["offline_unlock_enabled"])

    def test_old_patch_does_not_authorize_flash(self):
        for value in ("2026-02-01", "2025-12-01", "", "invalid"):
            report = assess({"ro.product.device": "sheng", "ro.soc.model": "SM8550", "ro.build.version.security_patch": value})
            self.assertFalse(report["offline_unlock_enabled"])

    def test_sheng_never_uses_8g3_profile(self):
        profile = get_profile("sheng")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.soc, "SM8550")
        self.assertNotEqual(profile.soc, "SM8650")

    @patch("hyperunlock.compatibility.ADB")
    def test_multiple_devices_require_selection(self, adb):
        adb.return_value.run.return_value = (0, "List of devices attached\na device\nb unauthorized\n")
        with self.assertRaises(UnlockError):
            inspect_android()
        adb.return_value.run.assert_called_once_with("devices")

    @patch("hyperunlock.compatibility.ADB")
    def test_unauthorized_stops_before_shell(self, adb):
        adb.return_value.run.return_value = (0, "List of devices attached\na unauthorized\n")
        with self.assertRaises(UnlockError):
            inspect_android("a")
        adb.return_value.run.assert_called_once_with("devices")
