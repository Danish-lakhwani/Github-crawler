import os
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.getenv('DATABASE_URL', 'postgres://postgres:postgres@localhost:5432/postgres')

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def upsert_repos(rows):
    """rows: list of tuples (id, name, owner, full_name, url, stars, metadata)"""
    sql = '''
    INSERT INTO repositories (id, name, owner, full_name, url, stars, metadata, last_crawled)
    VALUES %s
    ON CONFLICT (id) DO UPDATE SET
      name = EXCLUDED.name,
      owner = EXCLUDED.owner,
      full_name = EXCLUDED.full_name,
      url = EXCLUDED.url,
      stars = EXCLUDED.stars,
      metadata = repositories.metadata || EXCLUDED.metadata,
      last_crawled = EXCLUDED.last_crawled;
    '''
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, rows, template="(%s,%s,%s,%s,%s,%s,%s,now())")
    finally:
        conn.close()
