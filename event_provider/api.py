"""Router that serves the endpoints"""

from flask import Blueprint, jsonify, request, make_response, current_app
from event_provider.interface import check_information, get_events
from event_provider.decrypt import MismatchKeyIdError

api = Blueprint("api", __name__)


@api.route("/information", methods=["POST"])
def post_information():
    """POST endpoint to check if information is available for a specific identity hash"""
    provider_identifier = current_app.config["DEFAULT"].get("identifier", "BGP")
    data = request.get_json()
    if not data:
        return make_response("Missing request body", 400)
    required = ["identity_hash"]
    try:
        check_data(data, required)
    except MissingDataException as err:
        return make_response(str(err), 400)
    id_hash = data["identity_hash"]
    check = check_information(id_hash)
    resp = {"providerIdentifier": provider_identifier, "informationAvailable": check}
    return jsonify(resp)


@api.route("/events", methods=["POST"])
def post_events():
    """POST endpoint to get available events belonging to a specific identity hash"""
    provider_identifier = current_app.config["DEFAULT"].get("identifier", "BGP")
    data = request.get_json()
    if not data:
        return make_response("Missing request body", 400)
    required = ["bsn", "nonce", "keyid", "id_hash"]
    try:
        check_data(data, required)
    except MissingDataException as err:
        return make_response(str(err), 400)
    bsn = data["bsn"]
    nonce = data["nonce"]
    keyid = data["keyid"]
    id_hash = data["id_hash"]
    try:
        events = get_events(bsn, nonce, keyid, id_hash)
    except MismatchKeyIdError as err:
        return make_response(str(err), 400)
    resp = {"providerIdentifier": provider_identifier, "events": events}
    return jsonify(resp)

class MissingDataException(Exception):
    """Generic Exception for Missing Data"""

def check_data(data, required):
    """Check if a list of keys are in a given dict"""
    for key in required:
        if key not in data:
            raise MissingDataException("Missing '" + str(key) + "' field in request body")
