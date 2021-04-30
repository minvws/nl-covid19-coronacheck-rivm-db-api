"""Middleware between API and decryptor/DB"""
import json
from event_provider.database import check_info_db, get_events_db
from event_provider.decrypt import decrypt_bsn, decrypt_payload, hash_bsn


def check_information(id_hash):
    """Convert the db response into whatever is needed in the front"""
    res = check_info_db(id_hash)
    return bool(res)


def get_events(enc_bsn, nonce, id_hash):
    """Get all events belonging to a certain bsn"""
    bsn = decrypt_bsn(enc_bsn, nonce)
    hashed = hash_bsn(bsn)
    data = get_events_db(hashed, id_hash)
    res = convert_payloads(data)
    return res


def convert_payloads(data):
    """Converts payloads in the DB to how it should be represented in the front"""
    payloads = []
    mapper = {
        "vaccinsoort": "Vaccinsoort",
        "vaccinmerknaam": "Vaccinmerknaam",
        "productnaam": "Productnaam",
        "leverancier": "Leverancier",
        "batchnummer": "Batchnummer",
        "vaccinatiedatum": "Vaccinatiedatum",
        "uitvoerende": "Uitvoerende",
        "vaccinatieland": "Vaccinatieland",
        "vaccinatiestatus": "Vaccinatiestatus",
        "ouderDan16": "Ouderdan16",
        "hpkCode": "HPK-code",
    }
    for payload in data:
        decrypted = decrypt_payload(payload['payload'], payload['iv'])
        dic = json.loads(decrypted)
        data = {}
        for key, mapped_key in mapper.items():
            data[key] = dic[mapped_key]
        payloads.append(
            data
        )
    return payloads
