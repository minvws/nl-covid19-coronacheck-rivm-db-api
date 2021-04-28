# inge-5
RIVM Vaccination Event Provider Database Interface

Contacts a database to support the endpoints as described in https://github.com/minvws/nl-covid19-coronacheck-app-coordination/blob/main/docs/providing-vaccination-events.md

## Endpoints

This service provides 2 endpoints: `/information` and `/events`. The `/information` endpoint checks if data is available in the database
while the `/events` endpoint gets data from the database, decrypts it, and returns it. Any request to the database will be logged to the database.

### Sending requests to `/information`
`/information` expects a POST request with the following body:

```
{
	'id_hash': {ID_HASH}
}
```
where `ID_HASH` follows the format as described in the minvws document.

It then returns the following data:

```
{
	'providerIdentifier': 'BGP',
	'informationAvailable': true|false
}
```

### Sending requests to `/events`
`/events` expects a POST request with the following body:
```
{
	'bsn': {ENCRYPTED_BSN},
	'nonce': {NONCE},
	'keyid': {KEYID},
	'id_hash': {ID_HASH}
}
```
Where `ENCRYPTED_BSN` is the bsn encrypted with libsodium, `NONCE` is the encryption nonce, `KEYID` is the keyid of the cert, and `ID_HASH` follows the format as above. `ID_HASH` is only used for logging purposes.

It then returns the following data:

```
{
	'providerIdentifier': 'BGP'.
	'events': [a list, of, event payloads]
}
```

## Setup

To setup inge-5, simply run the following commands:

```
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp inge5.conf.dist inge5.conf
```

And modify the config file as needed.

## Running

inge-5 is a basic Flask project with the name of `event_provider`. To start it, simply run the following command:

`FLASK_APP=event_provider flask run`

It runs on `http://localhost:5000/` by default.

