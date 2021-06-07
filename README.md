# inge-5
RIVM Vaccination Event Provider Database Interface

Contacts a database to support the endpoints as described in https://github.com/minvws/nl-covid19-coronacheck-app-coordination/blob/main/docs/providing-vaccination-events.md

## Endpoints

This service provides 3 endpoints: `/v1/check-bsn`, `/v1/vaccinaties` and `/health`. The `/v1/check-bsn` endpoint checks if data is available in the database
while the `/v1/vaccinaties` endpoint gets data from the database, decrypts it, and returns it. The `/health` endpoint simply returns the status of service

Any request to the database will be logged to the database.

### Sending requests to `/v1/check-bsn`
`/v1/check-bsn` expects a POST request with the following body:

```
{
	'hashedBsn': {ID_HASH}
}
```
where `hashedBsn` follows the format as described in the minvws document.

It then returns the following data:

```
{
	'exists': true|false
}
```

### Sending requests to `/v1/vaccinaties`
`/v1/vaccinaties` expects a POST request with the following body:
```
{
	"hashedBsn": "string",
	"encryptedBsn": "string",
	"nonce": "string"
}
```
Where `encryptedBsn` is the bsn encrypted with libsodium, `nonce` is the encryption nonce, and `hashedBsn` follows the format as above. `hashedBsn` is only used for logging purposes.

It then returns the following data:

```
	[
	  {
	    "vaccinsoort": "string",
	    "vaccinmerknaam": "string",
	    "productnaam": "string",
	    "leverancier": "string",
	    "batchnummer": "string",
	    "vaccinatiedatum": "31-12-2020",
	    "uitvoerende": "string",
	    "vaccinatieland": "string",
	    "vaccinatiestatus": "string",
	    "ouderDan16": true,
	    "hpkCode": "string"
	  }, ...
	]
```

### Sending requests to `/health`
`/health` expects a simple GET request and returns the following data:

```
{
	"healthy": True|False,
	"errors": ["error_msg"]
}
```

The response code header is also set to an appropriate status code


### Getting error responses
If an error occurs anywhere in the process, the following data is returned:

```
{
	"melding": "string",
	"code": int
}
```

Just like with the `/health` endpoint, the response code header is also set

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
* `decrypt_bsn_key_vws_pub` - The location of the public key from vws, combines with our local private key to encrypt the BSN,
* `decrypt_payload_key` - The location of the aes256 key used to decrypt the database payload data.
* `host` - The address to run on (OPTIONAL, defaults to localhost, ignored when using uwsgi)
* `port` - The port to listen on (OPTIONAL, defaults to 5000, ignored when using uwsgi)


The decrypt_bsn_key_* key pair is generated with:
```
php -r '$keypair = sodium_crypto_box_keypair(); file_put_contents("ec.pub", base64_encode(sodium_crypto_box_publickey($keypair))); file_put_contents("ec.priv", base64_encode(sodium_crypto_box_secretkey($keypair)));'
```

#### Database
There are two database sections in the config: `database_read` for the read connection and `database_write` for the write connection. Both have the same fields

* `host` - The address of the database host
* `port` - The port the database is listening on
* `user` - The user for this connection
* `password` - The password for the database user
* `database` - The name of the database to connect to

#### Logging
Logging can be optionally configured. Any errors encountered during a session will be logged at `ERROR` level, an additional stacktrace will be logged at `DEBUG` level. 
Additionally, if an incomplete request comes in (so with missing data), it is logged at `WARNING` level.

The following fields are configurable for logging:

* `log_level` - String representation of the log level, defaults to `ERROR`
* `log_format` - Format string for logging, defaults to `[%%(levelname)s] [%%(asctime)-15s] %%(message)s`
* `log_location` - File to log to, defaults to `/dev/log`

## Running

inge-5 now has a simple run script. Simply run `./run_inge5.sh` after having setup the venv to start the service
in production mode.

### Running in dev

inge-5 is a basic Flask project with the name of `event_provider`. To start it, simply run the following command:

`make run` or `make run-prod`

It runs on `http://localhost:5000/` by default. `make run-prod` starts up the Flask production server, which is not recommended
for actual production (see below)

### Running in production

Flask recommends against running it's production server and instead suggests using `uwsgi`. To run `inge-5` with `uwsgi`,
simply run `uwsgi --ini uwsgi.ini`. This will by default create a unix socket at `./event_provider.sock` and spins up 5 workers.

If you want a different configuration, simply edit `uwsgi.ini`

## Tests

There are a few small tests in this repo. To run them, first install the `requirements-dev`:

```
source .venv/bin/activate
pip install -r requirements-dev.txt
```

and then run `make test`
