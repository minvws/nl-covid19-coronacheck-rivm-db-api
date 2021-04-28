"""Decryptor functions"""
from codecs import decode, encode
import nacl.secret
import nacl.utils
from nacl.hash import generichash
from nacl.encoding import Base64Encoder, HexEncoder
from nacl.public import PrivateKey
from flask import current_app, g


class MismatchKeyIdError(Exception):
    """Generic exception for mismatching keyid"""


class Decryptor: #pylint: disable=too-few-public-methods
    """Decryptor class which simply holds data written from disk"""
    def __init__(self):
        keyfile = current_app.config["DEFAULT"]["bsn_decrypt_key"]
        key, keyid = rawkey_from_file(keyfile)
        self.bsn_keydata = {"key": key, "keyid": keyid}
        keyfile = current_app.config["DEFAULT"]["payload_decrypt_key"]
        key, keyid = rawkey_from_file(keyfile)
        self.payload_keydata = {"key": key, "keyid": keyid}


def get_decryptor():
    """Add decryptor to globals if it's not there yet"""
    if not hasattr(g, "decryptor"):
        g.decryptor = Decryptor()
    return g.decryptor


def decrypt_bsn(bsn, nonce, keyid):
    """Decrypt BSN data"""
    decryptor = get_decryptor()
    key = decryptor.bsn_keydata["key"]
    if keyid != decryptor.bsn_keydata["keyid"]:
        raise MismatchKeyIdError(
            "Got a mismatched keyid while decrypting the bsn: "
            + keyid
            + " expecting: "
            + decryptor.bsn_keydata["keyid"]
        )
    return decrypt(bsn, nonce, key)


def decrypt_payload(payload, nonce, keyid):
    """Decrypt Payload data"""
    decryptor = get_decryptor()
    key = decryptor.payload_keydata["key"]
    if keyid != decryptor.payload_keydata["keyid"]:
        raise MismatchKeyIdError(
            "Got a mismatched keyid while decrypting the payload: "
            + keyid
            + " expecting: "
            + decryptor.bsn_keydata["keyid"]
        )
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

    return get_key_id_from_private_key(rawkey), rawkey


def get_key_id_from_private_key(privkey):
    """Get keyid from private rawkey data"""
    if isinstance(privkey, str):
        privkey = privkey.encode("ASCII")

    if len(privkey) < 50:
        privkey = encode(decode(privkey, "base64"), "hex").decode("ASCII")
    pubkey = encode(
        PrivateKey( # pylint: disable=protected-access
            privkey, encoder=HexEncoder
        ).public_key._public_key,
        "base64",
    ).decode("ASCII")
    return get_key_id_from_public_key(pubkey).strip()


def get_key_id_from_public_key(pubkey):
    """Get keyid from public rawkey data"""
    if isinstance(pubkey, str):
        pubkey = pubkey.encode("ASCII")
    if len(pubkey) < 50:
        pubkey = encode(decode(pubkey, "base64"), "hex")
    return generichash(decode(pubkey, "hex")).decode("ASCII").strip()
