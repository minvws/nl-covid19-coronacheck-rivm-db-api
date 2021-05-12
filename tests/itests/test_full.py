import random
import json
from uuid import uuid4

import pytest
from nacl.encoding import HexEncoder, Base64Encoder
from tests.utests.test_decrypt import encrypt_libsodium, encrypt_aes, rstring, pad
from event_provider.decrypt import hash_bsn, get_decryptor
from .test_database import get_log

CHECK_PATH='/v1/check-bsn'
EVENT_PATH='/v1/vaccinaties'

@pytest.fixture(autouse=True)
def mock_database(mocker, backend_db):
    mocker.patch('event_provider.database.psycopg2.connect', return_value=backend_db)

def gen_bsn():
    return ''.join(random.choice("0123456789") for x in range(9))

def prepare_id_string_hash(bsn):
    string = bsn + "-Test-Testerson-01"
    return hash_bsn(string)

def get_payload():
    return {
        "Vaccinsoort": "test",
        "Vaccinmerknaam": "test",
        "Productnaam": "test",
        "Leverancier": "test",
        "Batchnummer": 0,
        "Vaccinatiedatum": "2021-01-01",
        "Uitvoerende": "test",
        "Vaccinatieland": "NL",
        "Vaccinatiestatus": "test",
        "Ouderdan16": True,
        "HPK-code": "test",
        "other": "data",
        "is": "ignored"
    }

def compare_payloads(new, orig):
    assert new['vaccinsoort'] == orig['Vaccinsoort']
    assert new['vaccinmerknaam'] == orig['Vaccinmerknaam']
    assert new['productnaam'] == orig['Productnaam']
    assert new['leverancier'] == orig['Leverancier']
    assert new['batchnummer'] == orig['Batchnummer']
    assert new['vaccinatiedatum'] == orig['Vaccinatiedatum']
    assert new['uitvoerende'] == orig['Uitvoerende']
    assert new['vaccinatieland'] == orig['Vaccinatieland']
    assert new['vaccinatiestatus'] == orig['Vaccinatiestatus']
    assert new['ouderDan16'] == orig['Ouderdan16']
    assert new['hpkCode'] == orig['HPK-code']
    assert "other" not in new
    assert "is" not in new

def test_full(rnonce, riv, bob_keys, alice_keys, client, context, backend_db):
    bsn_priv = bob_keys['privkey']
    bsn_pub = alice_keys['pubkey']
    bsn_hash = rstring()
    payload_key = rstring()
    with context:
        decryptor = get_decryptor()
        decryptor.bsn_keydata = {
            "privkey": Base64Encoder.encode(bytes(bsn_priv)),
            "pubkey": Base64Encoder.encode(bytes(bsn_pub)),
            "hashkey": bsn_hash
        }
        decryptor.payload_keydata = payload_key
        bsn = gen_bsn()
        id_hash = prepare_id_string_hash(bsn)
        enc_bsn = encrypt_aes(bytes(pad(bsn), "utf-8"), bytes(payload_key, 'utf-8'), riv)
        enc_bsn = HexEncoder.encode(enc_bsn)
        enc_bsn = str(enc_bsn, "utf-8")
        payload = get_payload()
        enc_payload = encrypt_aes(bytes(pad(json.dumps(payload)), "utf-8"), bytes(payload_key, 'utf-8'), riv)
        enc_payload = HexEncoder.encode(enc_payload)
        enc_payload = str(enc_payload, "utf-8")
        iv = HexEncoder.encode(riv)
        iv = str(iv, "utf-8")
        with backend_db.cursor() as cur:
            sql = "INSERT INTO vaccinatie_event (bsn_external, bsn_internal, payload, iv, version_cims, version_vcbe) VALUES (%s, %s, %s, %s, %s, %s);"
            cur.execute(sql, [id_hash, enc_bsn, enc_payload, iv, "test", "test"])
        req_body = {'hashedBsn': id_hash}
        pre = len(get_log(backend_db))
        response = client.post(CHECK_PATH, json=req_body)
        assert response.status_code == 200
        assert response.json["exists"] is True
        post = len(get_log(backend_db))
        assert post > pre
        pre = post
        req_body = {'hashedBsn': 'fake_hash'}
        response = client.post(CHECK_PATH, json=req_body)
        assert response.status_code == 200
        assert response.json["exists"] is False
        post = len(get_log(backend_db))
        assert post > pre
        enc_bsn = encrypt_libsodium(bsn, rnonce, alice_keys['privkey'], bob_keys['pubkey'])['ctext']
        pre = post
        nonce = HexEncoder.encode(rnonce)
        nonce = str(nonce, "utf-8")
        req_body = {
            'hashedBsn': id_hash,
            'encryptedBsn': enc_bsn,
            'nonce': nonce,
        }
        response = client.post(EVENT_PATH, json=req_body)
        assert response.status_code == 200
        assert response.json
        assert len(response.json) > 0
        data = response.json
        compare_payloads(data[0], payload)
        post = len(get_log(backend_db))
        assert post > pre
        pre = post
        bsn = gen_bsn()
        enc_bsn = encrypt_libsodium(json.dumps(bsn), rnonce, alice_keys['privkey'], bob_keys['pubkey'])['ctext']
        req_body['encryptedBsn'] = enc_bsn
        response = client.post(EVENT_PATH, json=req_body)
        assert response.status_code == 200
        assert len(response.json) == 0
        post = len(get_log(backend_db))
        assert post > pre
