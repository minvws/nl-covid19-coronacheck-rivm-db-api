import os
import psycopg2

import pytest

from testcontainers.postgres import PostgresContainer

POSTGRES_USER = os.environ.get("TEST_POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("TEST_POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.environ.get("TEST_POSTGRES_DB", "vcbe_db")

PRINT_MSG = False

def debug(msg, show: bool):
    if show:
        print(msg)

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
@pytest.mark.skipif(not os.path.isfile('tests/itests/vcbe_db_merged.sql'), "Could not create test database, vcbe_db_merged.sql not found")
def backend_db(backend_db_connection):
    sql_file = open('tests/itests/vcbe_db_merged.sql')
    cursor = backend_db_connection.cursor()
    cursor.execute(sql_file.read())
    cursor.close()
    sql_file.close()
    # curr_date = datetime.date.today()
    # next_date = curr_date + datetime.timedelta(days=1)
    # no_delim = curr_date.isoformat().replace("-", "")
    # with backend_db_connection.cursor() as cur:
    #     sql = """
    #         CREATE TABLE vaccinatie_event_logging_{} PARTITION OF vaccinatie_event_logging
    #         FOR VALUES FROM ('{}') TO ('{}'); """.format(no_delim, curr_date.isoformat(), next_date.isoformat())
    #     cur.execute(sql)
    backend_db_connection.commit()
    return backend_db_connection
