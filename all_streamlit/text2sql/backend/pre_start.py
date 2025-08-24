import logging
import os

from text2sql.backend.connectors.clients import get_opensearch_client
from text2sql.backend.connectors.postgres import get_db_connection
from text2sql.backend.connectors.opensearch import (
    init_indices,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base_dir = os.path.dirname(os.path.realpath(__file__))

max_tries = 60 * 3  # 3 minutes
wait_seconds = 1


def init_opensearch():
    opensearch_client = get_opensearch_client()
    logger.info("Opensearch Client Initiated")
    init_indices(opensearch_client)
    logger.info("Initial training data have been in place.")


def init_postgres() -> None:
    try:
        logger.info("Initializing Postgres Connection")
        # Try to create session to check if DB is awake
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                with open(f"{base_dir}/db/init.sql") as f:
                    sql_script = f.read()
                    cursor.execute(sql_script)
                    conn.commit()
        logger.info("Postgres Tables Established")
    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    init_postgres()
    init_opensearch()


if __name__ == "__main__":
    main()
