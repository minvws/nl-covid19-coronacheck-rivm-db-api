"""Module Script to start Flask properly"""
from os.path import isfile

from flask import Flask, g
from .api import api
from .config import config
from .decrypt import Decryptor


class ConfigurationException(Exception):
    """Generic Exception for Configuration Issues"""

    def __init__(self, errors):
        super().__init__()
        self.errors = errors

    def __str__(self):
        if len(self.errors) == 0:
            res = "Something is wrong with the config file, but the cause is unknown."
        elif len(self.errors) == 1:
            res = self.errors[0]
        else:
            res = "The following errors occured while reading the config file: [\n"
            for err in self.errors:
                res += err + "\n"
            res += "]"
        res += " Please fix the Configuration file"
        return res


def create_app():
    """create and configure the app"""
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
    """
    This is pretty ugly, but it's the only way to "keep state"
    so to speak. Done this way so we don't have to read the keyfiles
    from disk for every request
    """
    with app.app_context():
        app.config["decryptor"] = Decryptor()

    @app.teardown_appcontext
    def close_db(_):  # pylint: disable=unused-variable
        """Closes the database again at the end of the request."""
        if hasattr(g, "read_db"):
            g.read_db.close()
        if hasattr(g, "write_db"):
            g.write_db.close()

    app.register_blueprint(api)

    return app


def check_config():
    """Check if the config was setup properly"""
    errors = []
    if "database_write" not in config:
        errors.append("database_write section is missing from config file")
    if "database_read" not in config:
        errors.append("database_read section is missing from config file")

    db_keys = ["host", "port", "user", "password", "database"]

    for key in db_keys:
        if not key in config["database_write"]:
            errors.append("Missing field '" + key + "' in database_write section")
        if not key in config["database_read"]:
            errors.append("Missing field '" + key + "' in database_read section")

    keyfiles = [
        "decrypt_bsn_key_vws_pub",
        "decrypt_bsn_key_our_priv",
        "decrypt_payload_key",
        "hash_bsn_key",
    ]
    for file in keyfiles:
        if file not in config["DEFAULT"]:
            errors.append(file + " field is missing from config file")
        else:
            enc_file = config["DEFAULT"][file]
            if not isfile(enc_file):
                errors.append(file + " file: '" + enc_file + "' does not exist")

    if errors:
        raise ConfigurationException(errors)
