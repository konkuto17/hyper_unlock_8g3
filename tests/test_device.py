"""Test device variable parsing and abstraction helpers."""
import unittest

from hyperunlock.device import parse_var


class TestDeviceParsing(unittest.TestCase):
    def test_parse_var_simple(self):
        sample = "product: aurora\nFinished. Total time: 0.004s"
        self.assertEqual(parse_var(sample, "product"), "aurora")

    def test_parse_var_bootloader_prefix(self):
        sample = "(bootloader) unlocked: yes\n(bootloader) secure: yes"
        self.assertEqual(parse_var(sample, "unlocked"), "yes")
        self.assertEqual(parse_var(sample, "secure"), "yes")

    def test_parse_var_multiline_getvar_all(self):
        sample = """
(bootloader) product: aurora
(bootloader) unlocked: yes
(bootloader) current-slot: a
(bootloader) anti: 1
Finished. Total time: 0.050s
"""
        self.assertEqual(parse_var(sample, "product"), "aurora")
        self.assertEqual(parse_var(sample, "unlocked"), "yes")
        self.assertEqual(parse_var(sample, "current-slot"), "a")
        self.assertEqual(parse_var(sample, "anti"), "1")
        self.assertEqual(parse_var(sample, "nonexistent"), "")


if __name__ == "__main__":
    unittest.main()
