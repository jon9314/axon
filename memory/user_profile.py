from typing import Optional
import psycopg2
from psycopg2 import sql
from config.settings import settings

class UserProfileManager:
    """Simple storage for user profile preferences."""

    def __init__(self, db_uri: str = settings.database.postgres_uri) -> None:
        try:
            self.conn = psycopg2.connect(db_uri)
            self._ensure_table()
        except psycopg2.OperationalError as e:
            print(f"Error connecting to PostgreSQL for profiles: {e}")
            self.conn = None

    def _ensure_table(self) -> None:
        if not self.conn:
            return
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    identity VARCHAR(255) PRIMARY KEY,
                    persona VARCHAR(255),
                    tone VARCHAR(255),
                    email VARCHAR(255)
                );
                """
            )
            self.conn.commit()

    def set_profile(
        self,
        identity: str,
        persona: Optional[str] = None,
        tone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> None:
        if not self.conn:
            return
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_profiles (identity, persona, tone, email)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (identity) DO UPDATE
                SET persona = EXCLUDED.persona,
                    tone = EXCLUDED.tone,
                    email = EXCLUDED.email;
                """,
                (identity, persona, tone, email),
            )
            self.conn.commit()

    def get_profile(self, identity: str) -> Optional[dict]:
        if not self.conn:
            return None
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT persona, tone, email FROM user_profiles WHERE identity=%s",
                (identity,),
            )
            res = cur.fetchone()
            if not res:
                return None
            persona, tone, email = res
            return {"identity": identity, "persona": persona, "tone": tone, "email": email}

    def close_connection(self) -> None:
        if self.conn:
            self.conn.close()

