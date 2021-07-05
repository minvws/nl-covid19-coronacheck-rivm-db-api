import json
import random
import string
import uuid
from nacl.encoding import HexEncoder
from nacl.public import Box
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from event_provider.crypto import decrypt_libsodium, get_decryptor, Decryptor, decrypt_aes, id_to_uuid

from flask import current_app

def rstring(size=32):
    key = ''.join(random.choice(string.ascii_letters) for x in range(size))
    return key

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


def test_id_to_uuid(mocker):
    mocker.patch("secrets.token_bytes", return_value=b"a"*8)
    assert id_to_uuid(65*256**7+66) == uuid.UUID('41000000-0000-0042-6161-616161616161')