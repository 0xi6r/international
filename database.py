import sqlite3
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

DB_PATH = Path("bot.db")


class Database:

    def __init__(self):

        self.conn = sqlite3.connect(
            DB_PATH,
            check_same_thread=False
        )

        self.conn.row_factory = sqlite3.Row

        self.create_tables()

    ############################################################

    def create_tables(self):

        cur = self.conn.cursor()

        ########################################################
        # Users
        ########################################################

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (

            telegram_id INTEGER PRIMARY KEY,

            username TEXT,

            first_name TEXT,

            joined_at TEXT,

            last_seen TEXT,

            articles_read INTEGER DEFAULT 0

        )
        """)

        ########################################################
        # Requests
        ########################################################

        cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            telegram_id INTEGER,

            url TEXT,

            domain TEXT,

            title TEXT,

            success INTEGER,

            created_at TEXT

        )
        """)

        ########################################################
        # Errors
        ########################################################

        cur.execute("""
        CREATE TABLE IF NOT EXISTS errors (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            telegram_id INTEGER,

            url TEXT,

            error TEXT,

            created_at TEXT

        )
        """)

        self.conn.commit()

    ############################################################

    def register_user(self, user):

        now = datetime.utcnow().isoformat()

        cur = self.conn.cursor()

        cur.execute(
            """
            INSERT OR IGNORE INTO users
            (
                telegram_id,
                username,
                first_name,
                joined_at,
                last_seen
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user.id,
                user.username,
                user.first_name,
                now,
                now
            )
        )

        cur.execute(
            """
            UPDATE users
            SET
                username=?,
                first_name=?,
                last_seen=?
            WHERE telegram_id=?
            """,
            (
                user.username,
                user.first_name,
                now,
                user.id
            )
        )

        self.conn.commit()

    ############################################################

    def increment_articles(self, telegram_id):

        self.conn.execute(
            """
            UPDATE users

            SET articles_read = articles_read + 1

            WHERE telegram_id=?
            """,
            (telegram_id,)
        )

        self.conn.commit()

    ############################################################

    def log_request(
        self,
        telegram_id,
        url,
        title,
        success
    ):

        domain = urlparse(url).netloc

        self.conn.execute(
            """
            INSERT INTO requests
            (
                telegram_id,
                url,
                domain,
                title,
                success,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                url,
                domain,
                title,
                int(success),
                datetime.utcnow().isoformat()
            )
        )

        self.conn.commit()

    ############################################################

    def log_error(
        self,
        telegram_id,
        url,
        error
    ):

        self.conn.execute(
            """
            INSERT INTO errors
            (
                telegram_id,
                url,
                error,
                created_at
            )

            VALUES (?, ?, ?, ?)
            """,
            (
                telegram_id,
                url,
                str(error),
                datetime.utcnow().isoformat()
            )
        )

        self.conn.commit()




    ############################################################
    # Statistics
    ############################################################

    def total_users(self):

        cur = self.conn.execute(
            "SELECT COUNT(*) FROM users"
        )

        return cur.fetchone()[0]

    ############################################################

    def total_articles(self):

        cur = self.conn.execute(
            """
            SELECT COALESCE(SUM(articles_read), 0)
            FROM users
            """
        )

        return cur.fetchone()[0]

    ############################################################

    def total_requests(self):

        cur = self.conn.execute(
            "SELECT COUNT(*) FROM requests"
        )

        return cur.fetchone()[0]

    ############################################################

    def successful_requests(self):

        cur = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM requests
            WHERE success = 1
            """
        )

        return cur.fetchone()[0]

    ############################################################

    def failed_requests(self):

        cur = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM requests
            WHERE success = 0
            """
        )

        return cur.fetchone()[0]

    ############################################################

    def today_requests(self):

        cur = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM requests
            WHERE DATE(created_at) = DATE('now')
            """
        )

        return cur.fetchone()[0]

    ############################################################

    def top_publishers(self, limit=10):

        cur = self.conn.execute(
            """
            SELECT
                domain,
                COUNT(*) AS total

            FROM requests

            GROUP BY domain

            ORDER BY total DESC

            LIMIT ?
            """,
            (limit,)
        )

        return cur.fetchall()

    ############################################################

    def top_users(self, limit=10):

        cur = self.conn.execute(
            """
            SELECT
                first_name,
                username,
                articles_read

            FROM users

            ORDER BY articles_read DESC

            LIMIT ?
            """,
            (limit,)
        )

        return cur.fetchall()

    ############################################################

    def all_user_ids(self):

        cur = self.conn.execute(
            """
            SELECT telegram_id
            FROM users
            ORDER BY joined_at ASC
            """
        )

        return [
            row["telegram_id"]
            for row in cur.fetchall()
        ]

    ############################################################

    def user_stats(self, telegram_id):

        cur = self.conn.execute(
            """
            SELECT *

            FROM users

            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )

        return cur.fetchone()

    ############################################################

    def user_requests(self, telegram_id):

        cur = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM requests
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )

        return cur.fetchone()[0]

    ############################################################

    def user_successful_requests(self, telegram_id):

        cur = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM requests
            WHERE telegram_id = ?
            AND success = 1
            """,
            (telegram_id,)
        )

        return cur.fetchone()[0]

    ############################################################

    def user_failed_requests(self, telegram_id):

        cur = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM requests
            WHERE telegram_id = ?
            AND success = 0
            """,
            (telegram_id,)
        )

        return cur.fetchone()[0]



db = Database()
