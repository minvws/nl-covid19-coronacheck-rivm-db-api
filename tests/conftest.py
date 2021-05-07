import os
import psycopg2

import pytest

from event_provider import create_app
from testcontainers.postgres import PostgresContainer
from flask import current_app

POSTGRES_USER = os.environ.get("TEST_POSTGRES_USER", "test")
POSTGRES_PASSWORD = os.environ.get("TEST_POSTGRES_PASSWORD", "test")
POSTGRES_DB = os.environ.get("TEST_POSTGRES_DB", "vcbe_db")

PRINT_MSG = False

def debug(msg, show: bool):
    if show:
        print(msg)

@pytest.fixture(scope="session")
def app():
    app = create_app()
    yield app


@pytest.fixture(scope="session")
def context(app):
    context = app.app_context()
    context.push()
    yield context


@pytest.fixture(scope="session")
def client(app):
    yield app.test_client()

# pylint: disable=redefined-outer-name
@pytest.fixture(scope='session')
def backend_db_container():
    debug("\n Creating Postgresql Test database...", PRINT_MSG)
    psql = PostgresContainer('postgres:11.3-alpine', user=POSTGRES_USER, password=POSTGRES_PASSWORD, dbname=POSTGRES_DB)
    debug("\nStarting Postgresql Test database...", PRINT_MSG)
    psql.start()
    debug(" Running postgresql service on {}".format(psql.get_connection_url()), PRINT_MSG)

    print(" Running postgresql service on {}".format(psql.get_connection_url()))
    yield psql
    debug("\nStopping Postgresql Test database...", PRINT_MSG)
    psql.stop()

# pylint: disable=redefined-outer-name
@pytest.fixture(scope='session')
def backend_db_connection(backend_db_container):
    conn = psycopg2.connect(
        dbname=backend_db_container.POSTGRES_DB,
        user=backend_db_container.POSTGRES_USER,
        password=backend_db_container.POSTGRES_PASSWORD,
        port=backend_db_container.get_exposed_port(backend_db_container.port_to_expose),
        host=backend_db_container.get_container_host_ip()
    )
    conn.commit()
    yield conn
    conn.close()

##
# This way of creating the database is terrible, but it's the only way we can with the current
# container setup.
#
# TODO: Manually create a Postgres container (as we did for harrie4) so we can setup the db properly
##
@pytest.fixture(scope='session')
def backend_db(backend_db_connection):
    sql1 = """
    CREATE TABLE public.vaccinatie_event (
      id SERIAL PRIMARY KEY,
      bsn_external varchar(64) NOT NULL,
      bsn_internal varchar(64) NOT NULL,
      payload varchar(2048) NOT NULL,
      iv VARCHAR(32) NOT NULL,
      version_cims varchar(10) NOT NULL,
      version_vcbe varchar(10) not null,
      created_at   timestamp(0) default current_timestamp
    );
    """
    sql2 = """
    CREATE TABLE public.vaccinatie_event_logging (
      created_date date not null,
      bsn_external varchar(64) not null,
      channel varchar(10) not null default 'cims',
      created_at timestamp(0) not null,
      events integer not null
    )
    """
    with backend_db_connection.cursor() as cur:
        cur.execute(sql1)
        cur.execute(sql2)
    backend_db_connection.commit()
    return backend_db_connection
