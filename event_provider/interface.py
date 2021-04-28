"""Middleware between API and decryptor/DB"""
import json
from event_provider.database import check_info_db, get_events_db
from event_provider.decrypt import decrypt_bsn, decrypt_payload


def check_information(id_hash):
    """Convert the db response into whatever is needed in the front"""
    res = check_info_db(id_hash)
    return bool(res)


def get_events(enc_bsn, nonce, keyid, id_hash):
    """Get all events belonging to a certain bsn"""
    bsn = decrypt_bsn(enc_bsn, nonce, keyid)
    data = get_events_db(bsn, id_hash)
    res = convert_payloads(data)
    return res


def convert_payloads(data):
    """Converts payloads in the DB to how it should be represented in the front"""
    payloads = []
    for payload in data:
        payload = json.dumps(payload[0])
        payloads.extend(
            decrypt_payload(payload["ctext"], payload["nonce"], payload["keyid"])
        )
    return payloads
