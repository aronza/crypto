from os import environ
from pathlib import Path

import pymysql
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv(raise_error_if_not_found=True))
CREATE_TABLES_SCRIPT = Path(__file__).parent.parent / 'create-tables.sql'


def reset_db():
    with pymysql.connect(host=environ['DB_HOST'], port=int(environ['DB_PORT']),
                         user=environ['DB_USERNAME'], password=environ['DB_PASSWORD']) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP DATABASE IF EXISTS crypto;")
            for sql in CREATE_TABLES_SCRIPT.read_text().strip().split(';'):
                if len(sql) > 0:
                    cur.execute(sql)
