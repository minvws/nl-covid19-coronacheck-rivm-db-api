from os.path import isfile

from flask import Flask, g
from .api import api
from .config import config


class ConfigurationException(Exception):
    pass


def create_app():
    # create and configure the app
    app = Flask(__name__)
    # app.logger.setLevel(logging.INFO)

    # try:
    #     syslog_handler = SysLogHandler(address='/dev/log')
    #     app.logger.addHandler(syslog_handler)
    # except:
    #     app.logger.error('Could not add Sysloghandler.')

    check_config()

    app.config["DEFAULT"] = config["DEFAULT"]
    app.config["database_write"] = config["database_write"]
    app.config["database_read"] = config["database_read"]

    @app.teardown_appcontext
    def close_db(error):
        """Closes the database again at the end of the request."""
        if hasattr(g, "read_db"):
            g.read_db.close()
        if hasattr(g, "write_db"):
            g.write_db.close()

    app.register_blueprint(api)

    return app


def check_config():
    if "database_write" not in config:
        raise ConfigurationException(
            "database_write section is missing from config file"
        )
    if "database_read" not in config:
        raise ConfigurationException(
            "database_read section is missing from config file"
        )

    db_keys = ["host", "port", "user", "password", "database"]

    for key in db_keys:
        if not key in config["database_write"]:
            raise ConfigurationException(
                "Missing key '" + key + "' in database_write section"
            )

    for key in db_keys:
        if not key in config["database_read"]:
            raise ConfigurationException(
                "Missing key '" + key + "' in database_read section"
            )

    if "decrypt_bsn_key" not in config["DEFAULT"]:
        raise ConfigurationException(
            "decrypt_bsn_key field is missing from config file"
        )
    enc_file = config["DEFAULT"]["decrypt_bsn_key"]
    if not isfile(enc_file):
        raise ConfigurationException(
            "decrypt_bsn_key '" + enc_file + "' does not exist"
        )
    if "decrypt_payload_key" not in config["DEFAULT"]:
        raise ConfigurationException(
            "decrypt_payload_key field is missing from config file"
        )
    enc_file = config["DEFAULT"]["decrypt_payload_key"]
    if not isfile(enc_file):
        raise ConfigurationException(
            "decrypt_payload_key '" + enc_file + "' does not exist"
        )
