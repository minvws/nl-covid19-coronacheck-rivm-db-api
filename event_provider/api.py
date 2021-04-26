"""Router that serves the endpoints"""
from functools import wraps

from flask import Blueprint, current_app, jsonify, request, make_response
from event_provider.database import check_information, get_events
from event_provider.config import config

api = Blueprint('api', __name__)

PROTOCOL_VERSION = "3.0"

PROVIDER_IDENTIFIER = "BGP"

def require_headers(func):
    """Decorator to check if headers are correct"""
    @wraps(func)
    def decorator(*args, **kwargs):

        protocol_version = request.headers.get('CoronaCheck-Protocol-Version')

        if not protocol_version:
            return make_response("Missing CoronaCheck-Protocol-Version Request Header", 400)
        if protocol_version.strip() != PROTOCOL_VERSION:
            return make_response("Protocol version mismatch, expecting: " + PROTOCOL_VERSION, 412)

        auth = request.headers.get("Authorization")

        if not auth:
            return make_response("Missing Authorization Request Header", 400)

        kwargs['auth'] = auth

        return func(*args, **kwargs)

    return decorator

@require_headers
@api.route('/information', methods=['POST'])
def post_information(auth):
    """POST endpoint to check if information is available for a specific identity hash"""
    id_hash = auth['identity_hash']
    check = check_information(id_hash)
    resp = {
        "protocolVersion": PROTOCOL_VERSION,
        "providerIdentifier": PROVIDER_IDENTIFIER,
        "informationAvailable": check
    }
    return jsonify(resp)

@require_headers
@api.route('/events', methods=['POST'])
def post_events(auth):
    """POST endpoint to get available events belonging to a specific identity hash"""
    id_hash = auth['identity_hash']
    events = get_events(id_hash)
    resp = {
        "protocolVersion": PROTOCOL_VERSION,
        "providerIdentifier": PROVIDER_IDENTIFIER,
        "status": "complete",
        "identityHash": id_hash,
        "events": events
    }
    return jsonify(resp)
