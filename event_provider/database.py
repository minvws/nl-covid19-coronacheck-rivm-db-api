"""Functions to interface with the DB"""
import datetime
import psycopg2
from flask import current_app, g


def read_connection():
    """Get the psycopg2 connection for the read socket"""
    if not hasattr(g, "read_db"):
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
    if not hasattr(g, "write_db"):
        g.write_db = psycopg2.connect(
            **{
                k: v
                for k, v in current_app.config["database_write"].items()
                if k not in current_app.config["DEFAULT"]
            }
        )
    return g.write_db


def log_request(id_hash):
    """Log the request to the db"""
    sql = """INSERT INTO vaccinatie_event_logging (created_date, bsn_external, channel, created_at)
                VALUES (%s,%s,%s,CURRENT_TIMESTAMP);"""
    conn = write_connection()
    curr_date, _ = datetime.datetime.now().isoformat().split("T")
    with conn.cursor() as cur:
        cur.execute(
            sql, [curr_date, id_hash, current_app.config.get("identfier", "BGP")]
        )
    conn.commit()


def check_info_db(id_hash):
    """Query the DB if a given id_hash has info"""
    sql = "SELECT id FROM vaccinatie_event WHERE bsn_external = %s LIMIT 1;"
    conn = read_connection()
    res = None
    with conn.cursor() as cur:
        cur.execute(sql, [id_hash])
        res = cur.fetchone()
    conn.commit()
    log_request(id_hash)
    return res


def get_events_db(bsn, id_hash):
    """Get all the payloads in the DB belonging to a certain id_hash"""
    sql = "SELECT payload FROM vaccinatie_event WHERE bsn_internal = %s;"
    conn = read_connection()
    res = []
    with conn.cursor() as cur:
        cur.execute(sql, [bsn])
        res = cur.fetchall()
    conn.commit()
    log_request(id_hash)
    return res
