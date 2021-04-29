"""Decryptor functions"""
import nacl.secret
import nacl.utils
from nacl.encoding import Base64Encoder
from flask import current_app, g


class MismatchKeyIdError(Exception):
    """Generic exception for mismatching keyid"""

class Decryptor: #pylint: disable=too-few-public-methods
    """Decryptor class which simply holds data written from disk"""
    def __init__(self):
        keyfile = current_app.config["DEFAULT"]["decrypt_bsn_key"]
        key = rawkey_from_file(keyfile)
        self.bsn_keydata = key
        keyfile = current_app.config["DEFAULT"]["decrypt_payload_key"]
        key = rawkey_from_file(keyfile)
        self.payload_keydata = key

def get_decryptor():
    """Add decryptor to globals if it's not there yet"""
    if not hasattr(g, "decryptor"):
        g.decryptor = Decryptor()
    return g.decryptor

def decrypt_bsn(bsn, nonce):
    """Decrypt BSN data"""
    decryptor = get_decryptor()
    key = decryptor.bsn_keydata
    return decrypt(bsn, nonce, key)

def decrypt_payload(payload, nonce):
    """Decrypt Payload data"""
    decryptor = get_decryptor()
    key = decryptor.payload_keydata
    return decrypt(payload, nonce, key)

def decrypt(data, nonce, key):
    """Generic decrypt function"""
    box = nacl.secret.SecretBox(key.encode(), encoder=Base64Encoder)
    nonce = Base64Encoder.decode(nonce)
    decrypted = box.decrypt(data, nonce, encoder=Base64Encoder).decode()
    return decrypted

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
