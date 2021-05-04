"""Decryptor functions"""
import hashlib
import hmac
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
        keyfile = current_app.config["DEFAULT"]["hash_bsn_key"]
        hashkey = rawkey_from_file(keyfile)
        self.bsn_keydata = {
            "privkey": privkey,
            "pubkey": pubkey,
            "hashkey": hashkey,
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


def decrypt_payload(payload, iv):
    """Decrypt Payload data"""
    decryptor = get_decryptor()
    key = decryptor.payload_keydata
    enc = HexEncoder.decode(payload)
    return decrypt_aes(enc, key, iv)


def unpad(ct):
    """Removes pkcs7 padding"""
    return ct[: -ord(ct[-1])]


"""
Would prefer to not have to use aes
but Oracle is keeping us hostage in a bad-cryptography situation
so here we are
"""


def decrypt_aes(enc, key, iv):
    """Decrypt AES encrypted data"""
    iv = HexEncoder.decode(iv)
    cipher = Cipher(algorithms.AES(bytes(key, "utf-8")), modes.CBC(iv))
    decryptor = cipher.decryptor()
    dec = decryptor.update(enc) + decryptor.finalize()
    return unpad(dec.decode("utf-8"))


def hash_bsn(bsn):
    """Hash a bsn"""
    decryptor = get_decryptor()
    key = decryptor.bsn_keydata["hashkey"]
    hma = hmac.new(bytes(key, "utf-8"), bsn.encode(), hashlib.sha256)
    return hma.hexdigest()


def rawkey_from_file(keyfile):
    """Get rawkey from file"""
    try:
        with open(keyfile, "r") as infile:
            rawkey = infile.read().strip()
    except IOError as error:
        raise IOError(
            "Fatal: {} file could not be read. " "Aborting.".format(keyfile), error
        ) from error

    return rawkey
