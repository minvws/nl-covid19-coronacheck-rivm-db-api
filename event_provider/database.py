"""Functions to interface with the DB"""
import datetime
import psycopg2
import psycopg2.extras
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


def log_request(id_hash, count):
    """Log the request to the db"""
    sql = """INSERT INTO vaccinatie_event_logging
        (created_date, bsn_external, channel, created_at, events)
                VALUES (%s,%s,%s,CURRENT_TIMESTAMP,%s);"""
    conn = write_connection()
    curr_date = datetime.date.today().isoformat()
    with conn.cursor() as cur:
        cur.execute(
            sql, [curr_date, id_hash, current_app.config.get("identfier", "BGP"), count]
        )
    conn.commit()


def check_info_db(id_hash):
    """Query the DB if a given id_hash has info"""
    sql = "SELECT id FROM vaccinatie_event WHERE bsn_external = %s LIMIT 1;"
    conn = read_connection()
    res = []
    with conn.cursor() as cur:
        cur.execute(sql, [id_hash])
        res = cur.fetchall()
    conn.commit()
    log_request(id_hash, len(res))
    return res


def get_events_db(hashed_bsn, id_hash):
    """Get all the payloads in the DB belonging to a certain id_hash"""
    sql = "SELECT payload, iv FROM vaccinatie_event WHERE bsn_internal = %s;"
    conn = read_connection()
    res = []
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, [hashed_bsn])
        res = cur.fetchall()
    conn.commit()
    log_request(id_hash, len(res))
    return res
