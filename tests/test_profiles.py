"""Test profile database and item integrity for both SM8650 and SM8550."""
import unittest
from pathlib import Path

from hyperunlock.profiles import SUPPORTED_DEVICES, get_profile, is_supported, list_profiles


class TestProfiles(unittest.TestCase):
    def test_known_devices_exist(self):
        expected_8g3 = ["aurora", "houji", "shennong", "manet", "zorn", "ruyi", "goku"]
        for codename in expected_8g3:
            self.assertTrue(is_supported(codename), f"{codename} should be supported")
            profile = get_profile(codename)
            self.assertIsNotNone(profile)
            self.assertEqual(profile.soc, "SM8650")

        expected_8g2 = ["sheng", "fuxi", "nuwa", "ishtar", "socrates", "vermeer"]
        for codename in expected_8g2:
            self.assertTrue(is_supported(codename), f"{codename} should be supported")
            profile = get_profile(codename)
            self.assertIsNotNone(profile)
            self.assertEqual(profile.soc, "SM8550")

    def test_case_insensitivity(self):
        self.assertIsNotNone(get_profile("AURORA"))
        self.assertIsNotNone(get_profile("  sheng  "))
        self.assertIsNotNone(get_profile("sheng_global"))
        self.assertIsNone(get_profile("unknown_model"))

    def test_items_exist_on_disk(self):
        items_dir = Path(__file__).parent.parent / "items"
        self.assertTrue(items_dir.is_dir(), "items directory must exist")

        for profile in list_profiles():
            folder = items_dir / profile.items_folder
            self.assertTrue(folder.is_dir(), f"Folder missing for {profile.codename}: {folder}")

            unlock_gpt = folder / "blgpt_both4.bin"
            if not unlock_gpt.is_file():
                unlock_gpt = folder / "unlockgpt_both4.bin"

            stock_gpt = folder / "gpt_both4.bin"

            self.assertTrue(unlock_gpt.is_file(), f"Unlock GPT missing for {profile.codename}")
            self.assertTrue(stock_gpt.is_file(), f"Stock gpt_both4.bin missing for {profile.codename}")
            self.assertIn(unlock_gpt.stat().st_size, (45056, 24576))
            self.assertEqual(stock_gpt.stat().st_size, 45056)

    def test_payloads_exist(self):
        payload_dir = Path(__file__).parent.parent / "payload"
        p_8g3 = payload_dir / "8gen3-Ennea.img"
        p_8g2 = payload_dir / "8550-Ennea.img"

        self.assertTrue(p_8g3.is_file(), "8gen3-Ennea.img payload must exist")
        self.assertTrue(p_8g2.is_file(), "8550-Ennea.img payload must exist")
        self.assertGreater(p_8g3.stat().st_size, 1000000)
        self.assertGreater(p_8g2.stat().st_size, 1000000)


if __name__ == "__main__":
    unittest.main()
