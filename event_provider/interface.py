"""Middleware between API and decryptor/DB"""

from event_provider.database import check_info_db, get_events_db
from event_provider.decrypt import decrypt_bsn

def check_information(id_hash):
    """Convert the db response into whatever is needed in the front"""
    res = check_info_db(id_hash)
    return bool(res)

def get_events(enc_bsn):
    """Get all events belonging to a certain bsn"""
    bsn = decrypt_bsn(enc_bsn)
    payloads = get_events_db(bsn)
    res = convert_payloads(payloads)
    return res

def convert_payloads(payloads):
    """Converts payloads in the DB to how it should be represented in the front"""
    raise NotImplementedError
