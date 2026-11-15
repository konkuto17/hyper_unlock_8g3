"""
Xiaomi Unlock Protocol Implementation.
Derived with attribution from MiForge/MiUnlockTool (Apache-2.0 License).
Uses standard cryptography library with robust timeout and validation controls.
"""
import binascii
import hashlib
import hmac
import json
from base64 import b64decode, b64encode
from typing import Any, Dict

import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def aes_cbc_encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext) + encryptor.finalize()


def aes_cbc_decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def send_signed_request(
    path: str,
    params_raw: Dict[str, Any],
    domain: str,
    ssecurity: str,
    cookies: Dict[str, str],
    timeout: int = 45,
) -> Dict[str, Any]:
    """Sign, encrypt, and send payload to Xiaomi Account Server."""
    params_raw = dict(params_raw)
    headers = {"User-Agent": "XiaomiPCSuite"}
    ssecurity_key = b64decode(ssecurity)
    iv = b"0102030405060708"
    key = b"2tBeoEyJTunmWUGq7bQH2Abn0k2NhhurOaqBfyxCuLVgn4AVj7swcawe53uDUno"
    params_raw["sid"] = "miui_unlocktool_client"

    if "data" in params_raw:
        params_raw["data"] = json.dumps(params_raw["data"])
        params_raw["data"] = b64encode(params_raw["data"].encode()).decode()

    param_order = sorted(params_raw.keys())
    sign_params = "&".join(f"{k}={params_raw[k]}" for k in param_order)
    sign_str = f"POST\n{path}\n{sign_params}"

    sign_hash_hex = binascii.hexlify(hmac.new(key, sign_str.encode(), hashlib.sha1).digest()).decode().encode()

    pad_len = 16 - len(sign_hash_hex) % 16
    padded_sign = sign_hash_hex + bytes([pad_len]) * pad_len
    current_sign = b64encode(aes_cbc_encrypt(padded_sign, ssecurity_key, iv)).decode()

    encoded_params = []
    for k in param_order:
        data = params_raw[k].encode()
        p_len = 16 - len(data) % 16
        padded_data = data + bytes([p_len]) * p_len
        encrypted = b64encode(aes_cbc_encrypt(padded_data, ssecurity_key, iv)).decode()
        encoded_params.append(f"{k}={encrypted}")

    encoded_params.extend([f"sign={current_sign}", ssecurity])
    sha1_input = f"POST&{path}&{'&'.join(encoded_params)}"
    signature = b64encode(hashlib.sha1(sha1_input.encode()).digest()).decode()

    post_params = {}
    for k in param_order:
        data = params_raw[k].encode()
        p_len = 16 - len(data) % 16
        padded_data = data + bytes([p_len]) * p_len
        post_params[k] = b64encode(aes_cbc_encrypt(padded_data, ssecurity_key, iv)).decode()

    post_params.update({"sign": current_sign, "signature": signature})

    try:
        response = requests.post(
            f"{domain}{path}",
            params=post_params,
            cookies=cookies,
            headers=headers,
            timeout=(10, timeout),
            allow_redirects=False,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Network request failed: {e}"}

    if not response.text or len(response.text) % 4 != 0:
        return {"error": "Invalid base64 response from server"}

    try:
        encrypted_data = b64decode(response.text, validate=True)
        decrypted = aes_cbc_decrypt(encrypted_data, ssecurity_key, iv)
    except Exception as e:
        return {"error": f"Decryption failed: {e}"}

    if not decrypted or len(decrypted) % 16 != 0:
        return {"error": "Decrypted data alignment error"}

    pad_len = decrypted[-1]
    if pad_len < 1 or pad_len > 16 or decrypted[-pad_len:] != bytes([pad_len]) * pad_len:
        return {"error": "Invalid padding in response"}

    clean_data = decrypted[:-pad_len]
    try:
        inner_b64 = b64decode(clean_data, validate=True)
        clean_response = json.loads(inner_b64.decode())
        return clean_response
    except Exception as e:
        return {"error": f"JSON decode failed: {e}"}
