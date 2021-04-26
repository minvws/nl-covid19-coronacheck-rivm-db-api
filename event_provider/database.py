"""Functions to interface with the DB"""
import datetime
import psycopg2
from event_provider.config import config

def read_connection():
    """Get the psycopg2 connection for the read socket"""
    return psycopg2.connect(**{k: v for k, v in config['database_read'].items() if k not in config.defaults()})

def write_connection():
    """Get the psycopg2 connection for the write socket"""
    return psycopg2.connect(**{k: v for k, v in config['database_write'].items() if k not in config.defaults()})

def log_request(id_hash):
    """Log the request to the db"""
    sql = "INSERT INTO vaccinatie_event_logging (created_date, bsn_external, channel, created_at VALUES (%s,%s,%s,%s);"
    conn = write_connection()
    curr_date, curr_time = datetime.datetime.now().replace(microsecond=0).isoformat().split("T")
    with conn.cursor() as cur:
        cur.execute(sql, [curr_date, id_hash, config.get('identfier', "BGP"), curr_time])
    conn.commit()

def check_info_db(id_hash):
    """Query the DB if a given id_hash has info"""
    sql = "SELECT id FROM vaccinatie_event WHERE bsn_external = %s LIMIT 1;"
    conn = read_connection()
    res = None
    with conn.cursor() as cur:
        cur.execute(sql, [id_hash])
        res = cur.fetchone()[0]
    conn.commit()
    return res

def get_events_db(bsn):
    """Get all the payloads in the DB belonging to a certain id_hash"""
    sql = "SELECT payload FROM vaccinatie_event WHERE bsn_internal = %s;"
    conn = read_connection()
    res = []
    with conn.cursor() as cur:
        cur.execute(sql, [bsn])
        res = cur.fetchall()
    conn.commit()
    return res
