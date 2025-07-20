# axon/agent/goal_tracker.py

"""Simple goal tracking backed by PostgreSQL."""

import psycopg2
from typing import Optional
import re
from config.settings import settings


class GoalTracker:
    def __init__(self, db_uri: str = settings.database.postgres_uri):
        try:
            self.conn = psycopg2.connect(db_uri)
            self._ensure_table()
        except psycopg2.OperationalError as e:
            print(f"Error connecting to PostgreSQL for goals: {e}")
            self.conn = None

    def _ensure_table(self) -> None:
        if not self.conn:
            return
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS goals (
                    id SERIAL PRIMARY KEY,
                    thread_id VARCHAR(255),
                    identity VARCHAR(255),
                    text TEXT NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    deferred BOOLEAN DEFAULT FALSE
                );
                """
            )
            # Ensure the deferred column exists when upgrading
            cur.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT FROM pg_attribute
                        WHERE attrelid = 'goals'::regclass
                          AND attname = 'deferred'
                          AND NOT attisdropped
                    ) THEN
                        ALTER TABLE goals ADD COLUMN deferred BOOLEAN DEFAULT FALSE;
                    END IF;
                END
                $$;
                """
            )
            self.conn.commit()

    def _is_deferred(self, text: str) -> bool:
        """Return True if the text sounds like a vague or deferred idea."""
        vague_patterns = [r"someday i might", r"maybe", r"one day", r"i might", r"perhaps", r"eventually"]
        for pat in vague_patterns:
            if re.search(pat, text, re.IGNORECASE):
                return True
        return False

    def add_goal(self, thread_id: str, text: str, identity: Optional[str] = None) -> None:
        if not self.conn:
            return
        deferred = self._is_deferred(text)
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO goals (thread_id, identity, text, deferred) VALUES (%s, %s, %s, %s)",
                (thread_id, identity, text, deferred),
            )
            self.conn.commit()

    def detect_and_add_goal(
        self, thread_id: str, message: str, identity: Optional[str] = None
    ) -> bool:
        """Detect goal-related phrases in a message and log them."""
        patterns = [r"i want to .+", r"remind me .+"]
        for pat in patterns:
            if re.search(pat, message, re.IGNORECASE):
                self.add_goal(thread_id, message, identity)
                return True
        return False

    def list_goals(self, thread_id: str):
        if not self.conn:
            return []
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, text, completed, identity, deferred FROM goals WHERE thread_id=%s",
                (thread_id,),
            )
            return cur.fetchall()

    def list_deferred_goals(self, thread_id: str):
        if not self.conn:
            return []
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, text, completed, identity, deferred FROM goals WHERE thread_id=%s AND deferred=TRUE",
                (thread_id,),
            )
            return cur.fetchall()

    def complete_goal(self, goal_id: int) -> None:
        if not self.conn:
            return
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE goals SET completed=TRUE WHERE id=%s",
                (goal_id,),
            )
            self.conn.commit()

