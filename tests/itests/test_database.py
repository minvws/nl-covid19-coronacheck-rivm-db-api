import random
from uuid import uuid4

import pytest
from event_provider.database import log_request, check_info_db, get_events_db, write_connection, read_connection

@pytest.fixture(autouse=True)
def mock_database(mocker, backend_db):
    mocker.patch('event_provider.database.psycopg2.connect', return_value=backend_db)


def create_event(conn, bsn="test"):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO vaccinatie_event (bsn_external, bsn_internal, payload, iv, version_cims, version_vcbe) VALUES (%s, %s, 'test', 'test', 'test', 'test');", [bsn, bsn])
    conn.commit()

def get_log(conn):
    res = []
    with conn.cursor() as cur:
        cur.execute("SELECT bsn_external, events FROM vaccinatie_event_logging;")
        res = cur.fetchall()
    return res

def test_log_request(context, backend_db):
    with context:
        test_bsn = "test"
        pre = len(get_log(backend_db))
        number = random.randint(1, 10)
        log_request(test_bsn, number)
        logged = get_log(backend_db)
        found = False
        for row in logged:
            assert row[0] == test_bsn
            if row[1] == number:
                found = True
        assert found
        assert len(logged) > pre

def test_check_info(context, backend_db):
    with context:
        test_bsn = "test"
        create_event(backend_db)
        pre = len(get_log(backend_db))
        res = check_info_db(test_bsn)
        assert res
        logged = get_log(backend_db)
        post = len(logged)
        found = False
        for row in logged:
            assert row[0] == test_bsn
            if row[1] == len(res):
                found = True
        assert found
        assert post > pre

def test_get_events(context, backend_db):
    with context:
        test_bsn = "test"
        create_event(backend_db)
        res = get_events_db(test_bsn, test_bsn)
        assert res
        comp = len(res) + 1
        create_event(backend_db)
        res = get_events_db(test_bsn, test_bsn)
        assert res
        assert len(res) == comp
        create_event(backend_db, "other")
        pre = len(get_log(backend_db))
        res = get_events_db(test_bsn, test_bsn)
        assert res
        assert len(res) == comp
        logged = get_log(backend_db)
        post = len(logged)
        found = False
        for row in logged:
            if row[1] == len(res) and row[0] == test_bsn:
                found = True
        assert found
        assert post > pre


def test_get_connections(context, backend_db):
    with context:
        assert backend_db == read_connection()
        assert backend_db == read_connection()
        assert backend_db == write_connection()
        assert backend_db == write_connection()
