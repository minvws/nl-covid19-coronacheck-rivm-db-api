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

### Explanation of the config file

#### Default
General, default config values

* `decrypt_bsn_key_our_priv` - The location of the local private key, combines with the public key from VWS to decrypt the BSN.
* `decrypt_bsn_key_vws_pub` - The location of the public key from vws, combines with our local private key to decrypt the BSN,
* `decrypt_payload_key` - The location of the aes256 key used to decrypt the database payload data.
* `hash_bsn_key` - The location of the hmac hmac256 key used to hash the database `bsn_internal` data. 
* `host` - The address to run on (OPTIONAL, defaults to localhost)
* `port` - The port to listen on (OPTIONAL, defaults to 5000)

#### Database
There are two database sections in the config: `database_read` for the read connection and `database_write` for the write connection. Both have the same fields

* `host` - The address of the database host
* `port` - The port the database is listening on
* `user` - The user for this connection
* `password` - The password for the database user
* `database` - The name of the database to connect to

## Running

inge-5 is a basic Flask project with the name of `event_provider`. To start it, simply run the following command:

`make run` or `make run-prod`

It runs on `http://localhost:5000/` by default.

