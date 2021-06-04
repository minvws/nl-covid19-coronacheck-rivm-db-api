"""Functions to interface with the DB"""
import datetime
import psycopg2
import psycopg2.extras
from flask import current_app, g


def read_connection():
    """Get the psycopg2 connection for the read socket"""
    if not hasattr(g, "read_db") or g.read_db.closed:
        g.read_db = psycopg2.connect(
            **{
                k: v
                for k, v in current_app.config["database_read"].items()
                if k not in current_app.config["DEFAULT"]
            }
        )
    return g.read_db


def write_connection():
    """Get the psycopg2 connection for the write socket"""
    if not hasattr(g, "write_db") or g.write_db.closed:
        g.write_db = psycopg2.connect(
            **{
                k: v
                for k, v in current_app.config["database_write"].items()
                if k not in current_app.config["DEFAULT"]
            }
        )
    return g.write_db


def log_request(id_hash, count, role):
    """Log the request to the db"""
    sql = """INSERT INTO vaccinatie_event_logging_{}
        (created_date, bsn_external, channel, created_at, events, nen_role)
                VALUES (%s,%s,%s,CURRENT_TIMESTAMP,%s,%s);"""
    curr_date = datetime.date.today().isoformat()
    part_name = curr_date.replace("-", "")
    sql = sql.format(part_name)
    conn = write_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                sql, [curr_date, id_hash, current_app.config.get("identfier", "DGP"), count, role]
            )


def check_info_db(id_hash):
    """Query the DB if a given id_hash has info"""
    sql = "SELECT id FROM vaccinatie_event WHERE bsn_external = %s LIMIT 1;"
    conn = read_connection()
    res = []
    with conn:
        with conn.cursor() as cur:
            cur.execute(sql, [id_hash])
            res = cur.fetchall()
    # No need to log unomi requests as not medical
    #log_request(id_hash, len(res))
    return res


def get_events_db(id_hash, role):
    """Get all the payloads in the DB belonging to a certain id_hash"""
    sql = "SELECT payload, iv, bsn_internal FROM vaccinatie_event WHERE bsn_external = %s;"
    conn = read_connection()
    res = []
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, [id_hash])
            res = cur.fetchall()
    log_request(id_hash, len(res), role)
    return res
