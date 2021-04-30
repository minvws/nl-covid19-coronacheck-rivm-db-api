import json
import os
import random
import string
import subprocess
import re
import nacl.utils
import nacl.hash
from nacl.encoding import HexEncoder
from nacl.public import PrivateKey, Box
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from event_provider.decrypt import decrypt_libsodium, get_decryptor, Decryptor, decrypt_aes, hash_bsn

from flask import current_app
import pytest

@pytest.fixture
def rnonce():
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    return nonce

@pytest.fixture
def riv():
    return os.urandom(16)

def rstring():
    key = ''.join(random.choice(string.ascii_letters) for x in range(32))
    return key

@pytest.fixture
def bob_keys():
    privkey = PrivateKey.generate()
    return {
        'privkey': privkey,
        'pubkey': privkey.public_key
    }

@pytest.fixture
def alice_keys():
    privkey = PrivateKey.generate()
    return {
        'privkey': privkey,
        'pubkey': privkey.public_key
    }

def test_get_decryptor(context):
    with context:
        decryptor = get_decryptor()
        assert 'decryptor' in current_app.config
        assert isinstance(decryptor, Decryptor)
        assert decryptor == current_app.config['decryptor']

def encrypt_libsodium(data, nonce, privkey, pubkey):
    box = Box(privkey, pubkey)
    enc_data = box.encrypt(data.encode(), nonce, encoder=HexEncoder)
    nonce = enc_data.nonce.decode()
    ctext = enc_data.ciphertext.decode()
    payload = {
        'nonce': nonce,
        'ctext': ctext
    }
    return payload

def test_decrypt_libsodium(rnonce, bob_keys, alice_keys):
    bprivkey = bob_keys['privkey']
    bpubkey = bob_keys['pubkey']
    aprivkey = alice_keys['privkey']
    apubkey = alice_keys['pubkey']
    data = {
        'test': rstring()
    }
    encrypted = encrypt_libsodium(json.dumps(data), rnonce, bprivkey, apubkey)
    decrypted = decrypt_libsodium(encrypted['ctext'], encrypted['nonce'], aprivkey, bpubkey)
    assert json.loads(decrypted) == data

def pad(m):
    return m+chr(16-len(m)%16)*(16-len(m)%16)

def encrypt_aes(data, key, iv):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    data
    ct = encryptor.update(data) + encryptor.finalize()
    return ct

def test_decrypt_aes(riv):
    key = rstring() 
    data = {
        "test": rstring()
    }
    encrypted = encrypt_aes(bytes(pad(json.dumps(data)), "utf-8"), bytes(key, 'utf-8'), riv)
    iv = HexEncoder.encode(riv)
    decrypted = json.loads(decrypt_aes(encrypted, key, iv))
    assert decrypted == data

def test_hash_bsn(mocker):
    class MockDecryptor(Decryptor):

        def __init__(self, key):
            self.bsn_keydata = {
                'hashkey': key
            }
    key = rstring()
    data = rstring()
    print(key)
    print(data)
    ps = subprocess.Popen(['echo', '-n', data], stdout=subprocess.PIPE)
    subproc = subprocess.check_output(['openssl', 'dgst', '-sha256', '-hmac', key], stdin=ps.stdout)
    ps.wait()
    mocker.patch('event_provider.decrypt.get_decryptor', return_value=MockDecryptor(key))
    hashed = hash_bsn(data)
    cap = re.match(r"\(stdin\)=[\s]*([^\s]*)", subproc.decode("utf-8"))
    assert hashed == cap.group(1)
