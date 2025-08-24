from text2sql.backend.connectors.clients import get_snowflake_connection
import pandas as pd
import snowflake.connector
from functools import lru_cache

@lru_cache
def execute_sql(sql: str, username:str, access_token:str) -> pd.DataFrame | None:
    conn = get_snowflake_connection(username, access_token)
    cs = conn.cursor()
    
    try:
        cur = cs.execute(sql)

        results = cur.fetchall()

        # Create a pandas dataframe from the results
        df = pd.DataFrame(results, columns=[desc[0] for desc in cur.description])
        return df

    except snowflake.connector.errors.ProgrammingError:
        return None