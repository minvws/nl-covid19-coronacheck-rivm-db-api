from event_provider.decrypt import rawkey_from_file, decrypt
from event_provider.config import config

import nacl.secret
import nacl.utils
import nacl.hash
from nacl.encoding import Base64Encoder
import pytest
import json

@pytest.fixture
def rnonce():
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    return nonce

@pytest.fixture
def keyfile():
    return config['DEFAULT']['decrypt_bsn_key']

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

def test_decryption(rnonce, keyfile):
    data = {
        'test': 'test'
    }
    encrypted = encrypt_payload(json.dumps(data), rnonce, keyfile)
    _, key = rawkey_from_file(keyfile)
    decrypted = decrypt(encrypted['ctext'], encrypted['nonce'], key)
    assert json.loads(decrypted) == data
