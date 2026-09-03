"""Durable storage for serverless deployments; SQLite remains for local runs."""
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

DATABASE_ENV_KEYS = (
    "DATABASE_URL",
    "POSTGRES_URL",
    "POSTGRES_PRISMA_URL",
    "POSTGRES_URL_NON_POOLING",
)


def database_url():
    for key in DATABASE_ENV_KEYS:
        value = os.environ.get(key)

        if value:
            return value

    return None


POSTGRES_URL = database_url()


if POSTGRES_URL:
    import psycopg
    from psycopg.rows import dict_row

    class Database:
        def __init__(self):
            self._schema_ready = False

        def _connection(self):
            return psycopg.connect(POSTGRES_URL, row_factory=dict_row)

        def _ensure_schema(self):
            if self._schema_ready:
                return

            with self._connection() as conn, conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        telegram_id BIGINT PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        joined_at TIMESTAMPTZ NOT NULL,
                        last_seen TIMESTAMPTZ NOT NULL,
                        articles_read INTEGER NOT NULL DEFAULT 0
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS requests (
                        id BIGSERIAL PRIMARY KEY,
                        telegram_id BIGINT,
                        url TEXT,
                        domain TEXT,
                        title TEXT,
                        success BOOLEAN NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS errors (
                        id BIGSERIAL PRIMARY KEY,
                        telegram_id BIGINT,
                        url TEXT,
                        error TEXT,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                """)

            self._schema_ready = True

        def _run(self, sql, values=(), fetch=False):
            self._ensure_schema()

            with self._connection() as conn, conn.cursor() as cur:
                cur.execute(sql, values)
                return cur.fetchall() if fetch else None
        def register_user(self, user):
            now = datetime.now(timezone.utc).isoformat()
            self._run("INSERT INTO users (telegram_id,username,first_name,joined_at,last_seen) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (telegram_id) DO UPDATE SET username=EXCLUDED.username, first_name=EXCLUDED.first_name, last_seen=EXCLUDED.last_seen", (user.id,user.username,user.first_name,now,now))
        def increment_articles(self, telegram_id): self._run("UPDATE users SET articles_read=articles_read+1 WHERE telegram_id=%s", (telegram_id,))
        def log_request(self, telegram_id, url, title, success): self._run("INSERT INTO requests (telegram_id,url,domain,title,success,created_at) VALUES (%s,%s,%s,%s,%s,%s)", (telegram_id,url,urlparse(url).netloc,title,bool(success),datetime.now(timezone.utc).isoformat()))
        def log_error(self, telegram_id, url, error): self._run("INSERT INTO errors (telegram_id,url,error,created_at) VALUES (%s,%s,%s,%s)", (telegram_id,url,str(error),datetime.now(timezone.utc).isoformat()))
        def _one(self, sql, values=()): return self._run(sql, values, fetch=True)[0]["value"]
        def total_users(self): return self._one("SELECT COUNT(*) AS value FROM users")
        def total_articles(self): return self._one("SELECT COALESCE(SUM(articles_read),0) AS value FROM users")
        def total_requests(self): return self._one("SELECT COUNT(*) AS value FROM requests")
        def successful_requests(self): return self._one("SELECT COUNT(*) AS value FROM requests WHERE success=true")
        def failed_requests(self): return self._one("SELECT COUNT(*) AS value FROM requests WHERE success=false")
        def today_requests(self): return self._one("SELECT COUNT(*) AS value FROM requests WHERE created_at::date=CURRENT_DATE")
        def top_publishers(self, limit=10): return self._run("SELECT domain,COUNT(*) AS total FROM requests GROUP BY domain ORDER BY total DESC LIMIT %s", (limit,), True)
        def top_users(self, limit=10): return self._run("SELECT first_name,username,articles_read FROM users ORDER BY articles_read DESC LIMIT %s", (limit,), True)
        def user_stats(self, telegram_id):
            rows = self._run("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,), True)
            return rows[0] if rows else None
        def user_requests(self, telegram_id): return self._one("SELECT COUNT(*) AS value FROM requests WHERE telegram_id=%s", (telegram_id,))
        def user_successful_requests(self, telegram_id): return self._one("SELECT COUNT(*) AS value FROM requests WHERE telegram_id=%s AND success=true", (telegram_id,))
        def user_failed_requests(self, telegram_id): return self._one("SELECT COUNT(*) AS value FROM requests WHERE telegram_id=%s AND success=false", (telegram_id,))
    db = Database()
elif os.environ.get("VERCEL"):
    class MissingDatabase:
        def _raise(self, *args, **kwargs):
            names = ", ".join(DATABASE_ENV_KEYS)
            raise RuntimeError(
                "No PostgreSQL connection string is configured. "
                f"Set one of these Vercel environment variables: {names}."
            )

        register_user = _raise
        increment_articles = _raise
        log_request = _raise
        log_error = _raise
        total_users = _raise
        total_articles = _raise
        total_requests = _raise
        successful_requests = _raise
        failed_requests = _raise
        today_requests = _raise
        top_publishers = _raise
        top_users = _raise
        user_stats = _raise
        user_requests = _raise
        user_successful_requests = _raise
        user_failed_requests = _raise

    db = MissingDatabase()
else:
    from database import db  # local SQLite compatibility
