# axon/agent/goal_tracker.py

"""Simple goal tracking backed by PostgreSQL."""

import psycopg2
import threading
from typing import Optional
from datetime import datetime
import re
from config.settings import settings
from .notifier import Notifier


class GoalTracker:
    def __init__(
        self,
        db_uri: str = settings.database.postgres_uri,
        notifier: Notifier | None = None,
    ) -> None:
        try:
            self.conn = psycopg2.connect(db_uri)
            self._ensure_table()
        except psycopg2.OperationalError as e:
            print(f"Error connecting to PostgreSQL for goals: {e}")
            self.conn = None
        self.notifier = notifier or Notifier()
        self._prompt_timer: threading.Timer | None = None

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
                    deferred BOOLEAN DEFAULT FALSE,
                    priority INTEGER DEFAULT 0,
                    deadline TIMESTAMP NULL
                );
                """
            )
            # Ensure columns exist when upgrading
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
                    IF NOT EXISTS (
                        SELECT FROM pg_attribute
                        WHERE attrelid = 'goals'::regclass
                          AND attname = 'priority'
                          AND NOT attisdropped
                    ) THEN
                        ALTER TABLE goals ADD COLUMN priority INTEGER DEFAULT 0;
                    END IF;
                    IF NOT EXISTS (
                        SELECT FROM pg_attribute
                        WHERE attrelid = 'goals'::regclass
                          AND attname = 'deadline'
                          AND NOT attisdropped
                    ) THEN
                        ALTER TABLE goals ADD COLUMN deadline TIMESTAMP NULL;
                    END IF;
                END
                $$;
                """
            )
            self.conn.commit()

    def _is_deferred(self, text: str) -> bool:
        """Return True if the text sounds like a vague or deferred idea."""
        vague_patterns = [
            r"someday i might",
            r"maybe",
            r"one day",
            r"i might",
            r"perhaps",
            r"eventually",
        ]
        for pat in vague_patterns:
            if re.search(pat, text, re.IGNORECASE):
                return True
        return False

    def add_goal(
        self,
        thread_id: str,
        text: str,
        identity: Optional[str] = None,
        priority: int = 0,
        deadline: datetime | None = None,
    ) -> None:
        if not self.conn:
            return
        deferred = self._is_deferred(text)
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO goals (thread_id, identity, text, deferred, priority, deadline) VALUES (%s, %s, %s, %s, %s, %s)",
                (thread_id, identity, text, deferred, priority, deadline),
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
                "SELECT id, text, completed, identity, deferred, priority, deadline FROM goals WHERE thread_id=%s",
                (thread_id,),
            )
            return cur.fetchall()

    def list_deferred_goals(self, thread_id: str):
        if not self.conn:
            return []
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, text, completed, identity, deferred, priority, deadline FROM goals WHERE thread_id=%s AND deferred=TRUE",
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

    def delete_goals(self, thread_id: str) -> int:
        """Delete all goals for a thread."""
        if not self.conn:
            return 0
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM goals WHERE thread_id=%s", (thread_id,))
            deleted = cur.rowcount
            self.conn.commit()
            return deleted

    def _prompt_deferred(self, thread_id: str, interval: float) -> None:
        goals = self.list_deferred_goals(thread_id)
        if goals:
            summary = "; ".join(g[1] for g in goals)
            self.notifier.notify("Deferred goals", summary)
        self.start_deferred_prompting(thread_id, interval)

    def start_deferred_prompting(
        self, thread_id: str, interval_seconds: float = 3600
    ) -> None:
        """Begin periodic reminders for deferred goals."""
        if self._prompt_timer:
            self._prompt_timer.cancel()
        self._prompt_timer = threading.Timer(
            interval_seconds,
            self._prompt_deferred,
            args=(thread_id, interval_seconds),
        )
        self._prompt_timer.daemon = True
        self._prompt_timer.start()

    def stop_deferred_prompting(self) -> None:
        """Stop periodic deferred goal reminders."""
        if self._prompt_timer:
            self._prompt_timer.cancel()
            self._prompt_timer = None
