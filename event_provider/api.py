"""Router that serves the endpoints"""
from functools import wraps

from flask import Blueprint, jsonify, request, make_response, current_app
from event_provider.interface import check_information, get_events
from event_provider.decrypt import MismatchKeyIdError

api = Blueprint('api', __name__)

PROTOCOL_VERSION = "3.0"

def require_headers(func):
    """Decorator to check if headers are correct"""
    @wraps(func)
    def decorator(*args, **kwargs):

        protocol_version = request.headers.get('CoronaCheck-Protocol-Version')

        if not protocol_version:
            return make_response("Missing CoronaCheck-Protocol-Version Request Header", 400)
        if protocol_version.strip() != PROTOCOL_VERSION:
            return make_response("Protocol version mismatch, expecting: " + PROTOCOL_VERSION, 412)

        return func(*args, **kwargs)

    return decorator

@require_headers
@api.route('/information', methods=['POST'])
def post_information():
    """POST endpoint to check if information is available for a specific identity hash"""
    provider_identifier = current_app.config['DEFAULT'].get('identifier', 'BGP')
    data = request.get_json()
    if not data:
        return make_response("Missing request body", 400)
    if 'identity_hash' not in data:
        return make_response("Missing 'identity_hash' field in request body", 400)
    id_hash = data['identity_hash']
    check = check_information(id_hash)
    resp = {
        "protocolVersion": PROTOCOL_VERSION,
        "providerIdentifier": provider_identifier,
        "informationAvailable": check
    }
    return jsonify(resp)

@require_headers
@api.route('/events', methods=['POST'])
def post_events():
    """POST endpoint to get available events belonging to a specific identity hash"""
    provider_identifier = current_app.config['DEFAULT'].get('identifier', 'BGP')
    data = request.get_json()
    if not data:
        return make_response("Missing request body", 400)
    if 'bsn' not in data:
        return make_response("Missing 'bsn' field in request body", 400)
    bsn = data['bsn']
    if 'nonce' not in data:
        return make_response("Missing 'nonce' field in request body", 400)
    nonce = data['nonce']
    if 'keyid' not in data:
        return make_response("Missing 'keyid' field in request body", 400)
    keyid = data['keyid']
    if 'id_hash' not in data:
        return make_response("Missing 'id_hash' field in request body", 400)
    id_hash = data['id_hash']
    try:
        events = get_events(bsn, nonce, keyid, id_hash)
    except MismatchKeyIdError as err:
        return make_response(str(err), 400)
    resp = {
        "protocolVersion": PROTOCOL_VERSION,
        "providerIdentifier": provider_identifier,
        "status": "complete",
        "events": events
    }
    return jsonify(resp)
