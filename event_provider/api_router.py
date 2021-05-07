"""Router that serves the endpoints"""

from nacl.exceptions import CryptoError
from cryptography.exceptions import UnsupportedAlgorithm, AlreadyFinalized
from flask import Blueprint, jsonify, request
import psycopg2
from event_provider.interface import (
    check_information,
    get_events,
    check_health,
    PayloadConversionException,
    HealthException,
)

api = Blueprint("api", __name__)


@api.route("/health", methods=["GET"])
def get_health():
    """Get endpoint to test the health of the service"""
    melding = "ok"
    code = 200
    try:
        check_health()
    except HealthException as ex:
        melding = repr(ex)
        code = ex.code
    return return_error(melding, code)  # Same format can be used for 200 response


@api.route("/v1/check-bsn", methods=["POST"])
def post_information():
    """POST endpoint to check if information is available for a specific identity hash"""
    data = request.get_json()
    required = ["hashedBsn"]
    try:
        check_data(data, required)
    except MissingDataException as err:
        return return_error(str(err), 400)
    id_hash = data["hashedBsn"]
    try:
        check = check_information(id_hash)
    except psycopg2.Error as err:
        res = "A database error occured: " + str(err)
        return return_error(res, 500)
    resp = {"exists": check}
    return jsonify(resp)


@api.route("/v1/vaccinaties", methods=["POST"])
def post_events():
    """POST endpoint to get available events belonging to a specific identity hash"""
    data = request.get_json()
    required = ["encryptedBsn", "nonce", "hashedBsn"]
    try:
        check_data(data, required)
    except MissingDataException as err:
        return return_error(str(err), 400)
    bsn = data["encryptedBsn"]
    nonce = data["nonce"]
    id_hash = data["hashedBsn"]
    try:
        events = get_events(bsn, nonce, id_hash)
    except psycopg2.Error as err:
        res = "A database error occured: " + str(err)
        return return_error(res, 500)
    except (CryptoError, UnsupportedAlgorithm, AlreadyFinalized) as err:
        res = "An error occured while decrypting: " + str(err)
        return return_error(res, 500)
    except PayloadConversionException as err:
        return return_error(str(err), 500)
    return jsonify(events)


class MissingDataException(Exception):
    """Generic Exception for Missing Data"""

    def __init__(self, errors):
        super().__init__()
        self.errors = errors

    def __str__(self):
        if self.errors:
            res = "The following fields are missing from the request body: "
            for err in self.errors:
                res += "'" + err + "', "
            res = res[:-2]
        else:
            res = "Missing request body"
        return res


def check_data(data, required):
    """Check if a list of keys are in a given dict"""
    errors = []
    if data:
        for key in required:
            if key not in data:
                errors.append(key)
        if errors:
            raise MissingDataException(errors)
    else:
        raise MissingDataException(errors)


def return_error(msg, code):
    """Helper function to create error object"""
    data = {"code": code, "melding": msg}
    return jsonify(data), code
