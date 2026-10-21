from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

_kek = None


def set_kek(kek_path):
    global _kek
    with open(kek_path, "rb") as f:
        _kek = f.read()


def _seal(key, plaintext):
    # nonce (16) + tag (16) + ciphertext — one blob to store
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return cipher.nonce + tag + ciphertext


def encrypt_data(data):
    dek = get_random_bytes(32)
    return _seal(dek, data), _seal(_kek, dek)
