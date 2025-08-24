from contextlib import contextmanager
from functools import partial

import streamlit as st
from psycopg2 import OperationalError
from psycopg2.pool import SimpleConnectionPool
from pydantic import SecretStr
from streamlit.logger import get_logger

from text2sql.backend.aws_utils import get_secretsmanager_password
from text2sql.backend.config import settings

logger = get_logger(__name__)


@st.cache_resource
def init_connection_pool():
    partial_pool = partial(
        SimpleConnectionPool,
        minconn=1,
        maxconn=10,
        dbname=settings.postgres.db,
        user=settings.postgres.user,
        host=settings.postgres.host,
        port=settings.postgres.port,
    )

    try:
        pool = partial_pool(password=settings.postgres.password.get_secret_value())
        logger.info("DB connection pool created successfully")
        return pool
    except OperationalError as e:
        if "password authentication failed" in str(e).lower():
            logger.warn(
                "Postgres password authentication failed. Trying to refresh the password from AWS Secrets Manager"
            )
            password = get_secretsmanager_password(
                settings.postgres.aws_secretsmanager_secret_id
            )
            settings.postgres.password = SecretStr(password)
            pool = partial_pool(password=settings.postgres.password.get_secret_value())
            return pool
        else:
            raise


@contextmanager
def get_db_connection():
    pool = init_connection_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        conn.commit()
        pool.putconn(conn)


def run_dml(query, data):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, data)
                conn.commit()
    except Exception as e:
        print(f"Error: {e}")


def insert_chat_history(data):
    query = """INSERT INTO chat_history (chat_id, session_id, email, question, generated_sql, state) VALUES (%(chat_id)s, %(session_id)s, %(email)s, %(question)s, %(generated_sql)s, %(state)s)"""
    run_dml(query, data)


def create_session(data):
    query = """INSERT INTO login_session (session_id, email) VALUES (%(session_id)s, %(email)s)"""
    run_dml(query, data)


def insert_feedback(data):
    query = """INSERT INTO user_feedback (chat_id, feedback) VALUES (%(chat_id)s, %(feedback)s)"""
    run_dml(query, data)
