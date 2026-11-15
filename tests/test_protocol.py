"""Test crypto primitives for Xiaomi protocol."""
import unittest

from hyperunlock.official import check_response, choose_zone
from hyperunlock.device import UnlockError
from hyperunlock.protocol.mi_protocol import aes_cbc_decrypt, aes_cbc_encrypt


class TestProtocolCrypto(unittest.TestCase):
    def test_aes_roundtrip(self):
        key = b"12345678901234567890123456789012"  # 32 bytes
        iv = b"0102030405060708"  # 16 bytes
        data = b"Hello, Xiaomi 14 Ultra Bootloader!"
        # Pad to multiple of 16
        pad_len = 16 - len(data) % 16
        padded = data + bytes([pad_len]) * pad_len

        encrypted = aes_cbc_encrypt(padded, key, iv)
        decrypted = aes_cbc_decrypt(encrypted, key, iv)
        unpadded = decrypted[:-decrypted[-1]]
        self.assertEqual(unpadded, data)

    def test_choose_zone(self):
        self.assertEqual(choose_zone("CN"), "China")
        self.assertEqual(choose_zone("IN"), "India")
        self.assertEqual(choose_zone("RU"), "Russia")
        self.assertEqual(choose_zone("DE"), "Europe")
        self.assertEqual(choose_zone("FR"), "Europe")
        self.assertEqual(choose_zone("VN"), "Singapore")
        self.assertEqual(choose_zone(None), "Singapore")

    def test_check_response_errors(self):
        with self.assertRaises(UnlockError) as ctx:
            check_response({"code": 20045, "descEN": "Region mismatch"})
        self.assertIn("20045", str(ctx.exception))

        with self.assertRaises(UnlockError) as ctx:
            check_response({"code": 20036, "data": {"waitHour": "168"}})
        self.assertIn("168", str(ctx.exception))

        ok_resp = {"code": 0, "encryptData": "abcdef"}
        self.assertEqual(check_response(ok_resp), ok_resp)


if __name__ == "__main__":
    unittest.main()

