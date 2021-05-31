"""Middleware between API and decryptor/DB"""
import json
import os
import psycopg2
from flask import current_app
from event_provider.database import (
    check_info_db,
    get_events_db,
    read_connection,
    write_connection,
)
from event_provider.decrypt import decrypt_bsn, decrypt_payload


class PayloadConversionException(Exception):
    """Exception for any issues during payload conversion"""

    def __init__(self, errors):
        self.errors = errors
        super().__init__()

    def __str__(self):
        res = "Failed to convert the following keys in the payload: "
        for err in self.errors:
            res += err + ", "
        res = res[:-2]
        return res


class HealthException(Exception):
    """Exception for the health check"""

    def __init__(self, msg, code=500):
        self.code = code
        self.msg = msg
        super().__init__()

    def __str__(self):
        return self.msg


def check_information(id_hash):
    """Convert the db response into whatever is needed in the front"""
    res = check_info_db(id_hash)
    return bool(res)


def get_events(enc_bsn, nonce, id_hash):
    """Get all events belonging to a certain bsn"""
    bsn = decrypt_bsn(enc_bsn, nonce)
    data = get_events_db(id_hash)
    res = convert_payloads(data, bsn)
    return res


def convert_payloads(data, bsn):
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
        "voornamen": "Voornamen",
        "voorvoegsel": "Voorvoegsel",
        "geslachtsnaam": "Geslachtsnaam",
        "geboortedatum": "Geboortedatum"
    }
    for payload in data:
        if compare_bsn(bsn, payload["bsn_internal"], payload["iv"]):
            decrypted = decrypt_payload(payload["payload"], payload["iv"])
            dic = json.loads(decrypted)
            data = {}
            errors = []
            for key, mapped_key in mapper.items():
                if mapped_key not in dic:
                    errors.append(mapped_key)
                    continue
                data[key] = dic[mapped_key]
            if errors:
                raise PayloadConversionException(errors)
            payloads.append(data)
    return payloads


def compare_bsn(bsn, enc_bsn, iv): #pylint: disable=invalid-name
    dec_bsn = decrypt_payload(enc_bsn, iv)
    return dec_bsn.strip() == bsn.strip()


def check_health():
    """Check the health of the service"""
    try:
        conn = read_connection()
    except psycopg2.Error as ex:
        raise HealthException(
            "Something is wrong with the read connection to the database: " + repr(ex)
        ) from ex
    if conn.closed:
        raise HealthException("The read connection to the database is closed")
    try:
        conn = write_connection()
    except psycopg2.Error as ex:
        raise HealthException(
            "Something is wrong with the write connection to the database: " + repr(ex)
        ) from ex
    if conn.closed:
        raise HealthException("The write connection to the database is closed")
    keyfiles = [
        "decrypt_bsn_key_vws_pub",
        "decrypt_bsn_key_our_priv",
        "decrypt_payload_key",
    ]
    for key in keyfiles:
        path = current_app.config["DEFAULT"][key]
        if not os.path.isfile(path):
            raise HealthException(
                "The decryption key file for " + key + " is missing from disk"
            )
