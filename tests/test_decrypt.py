import json
import nacl.secret
import nacl.utils
import nacl.hash
from nacl.encoding import Base64Encoder

from event_provider.decrypt import rawkey_from_file, decrypt, decrypt_bsn, decrypt_payload, get_decryptor, Decryptor
from event_provider.config import config

from flask import g
import pytest

@pytest.fixture
def rnonce():
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    return nonce

@pytest.fixture
def bsn_key():
    return config['DEFAULT']['decrypt_bsn_key']

@pytest.fixture
def payload_key():
    return config['DEFAULT']['decrypt_payload_key']

def encrypt_payload(data, nonce, keyfile):
    key = rawkey_from_file(keyfile)
    box = nacl.secret.SecretBox(key.encode(), encoder=Base64Encoder)
    enc_data = box.encrypt(data.encode(), nonce, encoder=Base64Encoder)
    nonce = enc_data.nonce.decode()
    ctext = enc_data.ciphertext.decode()
    payload = {
        'nonce': nonce,
        'ctext': ctext
    }
    return payload

def test_decryption(rnonce, bsn_key):
    data = {
        'test': 'test'
    }
    encrypted = encrypt_payload(json.dumps(data), rnonce, bsn_key)
    key = rawkey_from_file(bsn_key)
    decrypted = decrypt(encrypted['ctext'], encrypted['nonce'], key)
    assert json.loads(decrypted) == data

def test_get_decryptor(context):
    with context:
        assert not hasattr(g, 'decryptor')
        decryptor = get_decryptor()
        assert hasattr(g, 'decryptor')
        assert isinstance(decryptor, Decryptor)
        assert decryptor == g.decryptor

def test_decrypt_bsn(context, bsn_key, rnonce):
    bsn = "000000012"
    encrypted = encrypt_payload(bsn, rnonce, bsn_key)
    with context:
        decrypted = decrypt_bsn(encrypted['ctext'], encrypted['nonce'])
    assert decrypted == bsn

def test_decrypt_payload(context, payload_key, rnonce):
    payload = {
        "test": "test"
    }
    encrypted = encrypt_payload(json.dumps(payload), rnonce, payload_key)
    with context:
        decrypted = decrypt_payload(encrypted['ctext'], encrypted['nonce'])
    assert json.loads(decrypted) == payload
