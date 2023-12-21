"""Decryptor functions"""
import secrets
import uuid
import nacl.secret
import nacl.public
import nacl.utils
from nacl.encoding import HexEncoder, Base64Encoder
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from flask import current_app


class Decryptor:  # pylint: disable=too-few-public-methods
    """Decryptor class which simply holds data written from disk"""

    def __init__(self):
        keyfile = current_app.config["DEFAULT"]["decrypt_bsn_key_our_priv"]
        privkey = rawkey_from_file(keyfile)
        keyfile = current_app.config["DEFAULT"]["decrypt_bsn_key_vws_pub"]
        pubkey = rawkey_from_file(keyfile)
        self.bsn_keydata = {
            "privkey": privkey,
            "pubkey": pubkey,
        }
        keyfile = current_app.config["DEFAULT"]["decrypt_payload_key"]
        key = rawkey_from_file(keyfile)
        self.payload_keydata = key


def get_decryptor():
    """Add decryptor to globals if it's not there yet"""
    if not "decryptor" in current_app.config:
        current_app.config["decryptor"] = Decryptor()
    return current_app.config["decryptor"]


def decrypt_bsn(bsn, nonce):
    """Decrypt BSN data"""
    decryptor = get_decryptor()
    privkey = decryptor.bsn_keydata["privkey"]
    pubkey = decryptor.bsn_keydata["pubkey"]
    privkey = nacl.public.PrivateKey(privkey, Base64Encoder)
    pubkey = nacl.public.PublicKey(pubkey, Base64Encoder)
    return decrypt_libsodium(bsn, nonce, privkey, pubkey)


def decrypt_libsodium(data, nonce, privkey, pubkey):
    """Generic libsodium decrypt function"""
    box = nacl.public.Box(privkey, pubkey)
    nonce = HexEncoder.decode(nonce)
    decrypted = box.decrypt(data, nonce, encoder=HexEncoder).decode()
    return decrypted


def decrypt_payload(payload, iv):  # pylint: disable=invalid-name
    """Decrypt Payload data"""
    decryptor = get_decryptor()
    key = decryptor.payload_keydata
    enc = HexEncoder.decode(payload)
    return decrypt_aes(enc, key, iv)


def unpad(ct):  # pylint: disable=invalid-name
    """Removes pkcs7 padding"""
    if ct:  # No text means no padding
        return ct[: -ord(ct[-1])]
    return ct


###
# Would prefer to not have to use aes
# but Oracle is keeping us hostage in a bad-cryptography situation
# so here we are
###


def decrypt_aes(enc, key, iv):  # pylint: disable=invalid-name
    """Decrypt AES encrypted data"""
    iv = HexEncoder.decode(iv)
    if not iv:
        iv = bytearray(16)
    cipher = Cipher(algorithms.AES(bytes(key, "utf-8")), modes.CBC(iv))
    decryptor = cipher.decryptor()
    dec = decryptor.update(enc) + decryptor.finalize()
    return unpad(dec.decode("utf-8"))


def rawkey_from_file(keyfile):
    """Get rawkey from file"""
    try:
        with open(keyfile, "r", encoding="utf-8") as infile:
            rawkey = infile.read().strip()
    except IOError as error:
        raise IOError(
           f"Fatal: {keyfile} file could not be read. " "Aborting.", error
        ) from error

    return rawkey


def id_to_uuid(identifier: int) -> uuid.UUID:
    id_bytes = identifier.to_bytes(8, "big")
    rand_bytes = secrets.token_bytes(8)
    return uuid.UUID(bytes=id_bytes + rand_bytes)


def uuid_to_id(uuid_in: uuid.UUID) -> int:
    return int(uuid_in.hex[:16], base=16)


def uuid_str_to_id(uuid_str: str) -> int:
    return uuid_to_id(uuid.UUID(uuid_str))
