# axon/memory/memory_handler.py

import psycopg2
from psycopg2 import sql
from typing import Optional, Iterable

class MemoryHandler:
    """
    Handles interactions with the PostgreSQL database for storing and
    retrieving factual memories (key-value pairs).
    """
    def __init__(self, db_uri: str):
        """
        Initializes the MemoryHandler and connects to the PostgreSQL database.
        It also ensures the 'facts' table has the required columns.
        """
        try:
            self.conn = psycopg2.connect(db_uri)
            self._ensure_table_and_columns_exist()
            print("Successfully connected to PostgreSQL and ensured 'facts' table is correctly structured.")
        except psycopg2.OperationalError as e:
            print(f"Error connecting to PostgreSQL: {e}")
            self.conn = None

    def _ensure_table_and_columns_exist(self):
        """
        Ensures the 'facts' table exists and has thread_id and identity columns.
        """
        if not self.conn:
            return

        with self.conn.cursor() as cur:
            # Create table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id SERIAL PRIMARY KEY,
                    thread_id VARCHAR(255) NOT NULL,
                    key VARCHAR(255) NOT NULL,
                    value TEXT,
                    identity VARCHAR(255),
                    locked BOOLEAN DEFAULT FALSE,
                    tags TEXT,
                    UNIQUE(thread_id, key)
                );
            """)

            # Add 'identity' column if it doesn't exist
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid = 'facts'::regclass AND attname = 'identity' AND NOT attisdropped) THEN
                        ALTER TABLE facts ADD COLUMN identity VARCHAR(255);
                    END IF;
                    IF NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid = 'facts'::regclass AND attname = 'locked' AND NOT attisdropped) THEN
                        ALTER TABLE facts ADD COLUMN locked BOOLEAN DEFAULT FALSE;
                    END IF;
                    IF NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid = 'facts'::regclass AND attname = 'tags' AND NOT attisdropped) THEN
                        ALTER TABLE facts ADD COLUMN tags TEXT;
                    END IF;
                END
                $$;
            """)
            self.conn.commit()

    def add_fact(
        self,
        thread_id: str,
        key: str,
        value: str,
        identity: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
    ) -> None:
        """
        Adds or updates a fact for a given thread and identity.
        """
        if not self.conn:
            print("No database connection.")
            return

        tags_str = ",".join(tags) if tags else None
        with self.conn.cursor() as cur:
            query = sql.SQL(
                """
                INSERT INTO facts (thread_id, key, value, identity, tags) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (thread_id, key) DO UPDATE SET value = EXCLUDED.value, identity = EXCLUDED.identity, tags = EXCLUDED.tags;
            """
            )
            cur.execute(query, (thread_id, key, value, identity, tags_str))
            self.conn.commit()
            print(
                f"Added/Updated fact for thread {thread_id}: {key} = {value} "
                f"(Identity: {identity}, Tags: {tags})"
            )

    def get_fact(self, thread_id: str, key: str, include_identity: bool = False):
        """Retrieve a fact and optionally its identity for a given thread."""
        if not self.conn:
            print("No database connection.")
            return None

        with self.conn.cursor() as cur:
            query = sql.SQL(
                "SELECT value, identity FROM facts WHERE thread_id = %s AND key = %s"
            )
            cur.execute(query, (thread_id, key))
            result = cur.fetchone()
            print(
                f"Retrieved fact for thread {thread_id} with key {key}: {'Found' if result else 'Not Found'}"
            )
            if not result:
                return None
            value, ident = result
            return (value, ident) if include_identity else value

    def list_facts(
        self, thread_id: str, tag: Optional[str] = None
    ) -> list[tuple[str, str, str | None, bool, list[str]]]:
        """Returns all facts for a thread including lock state and tags.

        If ``tag`` is provided, only facts containing that tag are returned.
        """
        if not self.conn:
            print("No database connection.")
            return []

        with self.conn.cursor() as cur:
            query = (
                "SELECT key, value, identity, locked, tags FROM facts WHERE thread_id = %s"
            )
            params = [thread_id]
            if tag:
                query += " AND tags ILIKE %s"
                params.append(f"%{tag}%")
            cur.execute(query, params)
            rows = cur.fetchall()
            result = []
            for key, value, identity, locked, tags_str in rows:
                tags_list = [t for t in tags_str.split(',') if t] if tags_str else []
                result.append((key, value, identity, locked, tags_list))
            return result

    def update_fact(
        self,
        thread_id: str,
        key: str,
        value: str,
        identity: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
    ) -> None:
        if not self.conn:
            return
        tags_str = ",".join(tags) if tags else None
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE facts SET value=%s, identity=%s, tags=%s WHERE thread_id=%s AND key=%s",
                (value, identity, tags_str, thread_id, key),
            )
            self.conn.commit()

    def delete_fact(self, thread_id: str, key: str) -> bool:
        if not self.conn:
            return False
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM facts WHERE thread_id=%s AND key=%s AND locked=FALSE",
                (thread_id, key),
            )
            deleted = cur.rowcount > 0
            self.conn.commit()
            return deleted

    def set_lock(self, thread_id: str, key: str, locked: bool) -> bool:
        if not self.conn:
            return False
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE facts SET locked=%s WHERE thread_id=%s AND key=%s",
                (locked, thread_id, key),
            )
            changed = cur.rowcount > 0
            self.conn.commit()
            return changed

    def close_connection(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            print("PostgreSQL connection closed.")

