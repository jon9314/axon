# axon/memory/memory_handler.py

import psycopg2
from psycopg2 import sql

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
                END
                $$;
            """)
            self.conn.commit()

    def add_fact(self, thread_id: str, key: str, value: str, identity: str = None):
        """
        Adds or updates a fact for a given thread and identity.
        """
        if not self.conn:
            print("No database connection.")
            return

        with self.conn.cursor() as cur:
            query = sql.SQL("""
                INSERT INTO facts (thread_id, key, value, identity) VALUES (%s, %s, %s, %s)
                ON CONFLICT (thread_id, key) DO UPDATE SET value = EXCLUDED.value, identity = EXCLUDED.identity;
            """)
            cur.execute(query, (thread_id, key, value, identity))
            self.conn.commit()
            print(f"Added/Updated fact for thread {thread_id}: {key} = {value} (Identity: {identity})")

    def get_fact(self, thread_id: str, key: str):
        """
        Retrieves a fact from the database for a given thread and key.
        """
        if not self.conn:
            print("No database connection.")
            return None

        with self.conn.cursor() as cur:
            query = sql.SQL("SELECT value FROM facts WHERE thread_id = %s AND key = %s")
            cur.execute(query, (thread_id, key))
            result = cur.fetchone()
            print(f"Retrieved fact for thread {thread_id} with key {key}: {'Found' if result else 'Not Found'}")
            return result[0] if result else None

    def close_connection(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            print("PostgreSQL connection closed.")