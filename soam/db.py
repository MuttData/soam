import os
from unittest import TestCase
from urllib.parse import urlparse


class PgTestCase(TestCase):

    db_base = os.getenv("TEST_BACKEND_DB_CONNSTR")
    if not db_base:
        raise KeyError('Missing test database in the "BACKEND_DB" venv')

    r = urlparse(db_base)

    db_tests_name = "pytests"
    db_test_pg_conn_params = {
        "dbname": db_tests_name,
        "user": r.username,
        "password": r.password,
        "host": r.hostname,
        "port": r.port,
    }
    db_test_pg_conn = " ".join(
        [f"{k}={v}" for k, v in db_test_pg_conn_params.items() if v]
    )
