import pytest
import random
import json

from .test_decrypt import rnonce, riv, bob_keys, alice_keys, encrypt_libsodium, encrypt_aes, rstring, pad
from nacl.public import PrivateKey, Box
from event_provider.decrypt import hash_bsn, get_decryptor
from flask import current_app

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
		"Vaccinatiedatum": "2021-01-01"
		"Uitvoerende": "test",
		"Vaccinatieland": "NL",
		"Vaccinatiestatus": "test",
		"Ouderdan16": True,
		"HPK-code": "test"
		"other": "data"
		"is": "ignored"
	}

def test_full(rnonce, riv, bob_keys, alice_keys, client, context, backend_db):
	bsn_priv = bob_keys['privkey']
	bsn_pub = alice_keys['pubkey']
	bsn_hash = rstring()
	payload_key = rstring()
	with context:
		decryptor = get_decryptor()
		decryptor.bsn_keydata = {
			"privkey": bsn_priv,
			"pubkey": bsn_pub,
			"hashkey": bsn_hash
		}
		decryptor.payload_keydata = payload_key
		bsn = ''.join(random.choice("0123456789") for x in range(9))
		id_hash = prepare_id_string_hash(bsn)
		hashed_bsn = hash_bsn(bsn)
		payload = get_payload()
		enc_payload = encrypt_aes(bytes(pad(json.dumps(payload)), "utf-8"), bytes(payload_key, 'utf-8'), riv)
		enc_bsn = encrypt_libsodium(json.dumps(bsn), rnonce, alice_keys['privkey'], bob_keys['pubkey'])
		with backend_db.cursor() as cur:
			sql = "INSERT INTO vaccinatie_event (bsn_external, bsn_internal, payload, iv, version_cims, version_vcbe) VALUES (%s, %s, %s, %s, %s, %s);"
			cur.execute(sql, [id_hash, hashed_bsn, enc_payload, riv, "test", "test"])
