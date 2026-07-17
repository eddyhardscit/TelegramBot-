from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class UserProfile:
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    preferred_name: Optional[str]
    first_seen: str
    last_seen: str
    message_count: int


class MemoryStore:
    """Persistent, user-controlled memory for Project Arena."""

    def __init__(self, db_path: str = "data/arena_memory.sqlite3") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=20)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    preferred_name TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    message_count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    memory_key TEXT NOT NULL,
                    memory_value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(telegram_id, memory_key)
                )
                """
            )
            conn.commit()

    def touch_user(
        self,
        telegram_id: int,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
    ) -> tuple[UserProfile, bool, Optional[str]]:
        now = datetime.now(timezone.utc).isoformat()

        with self._lock, self._connect() as conn:
            existing = conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()

            is_new = existing is None
            previous_last_seen = None if is_new else str(existing["last_seen"])

            if is_new:
                conn.execute(
                    """
                    INSERT INTO users (
                        telegram_id, username, first_name, last_name,
                        preferred_name, first_seen, last_seen, message_count
                    )
                    VALUES (?, ?, ?, ?, NULL, ?, ?, 1)
                    """,
                    (telegram_id, username, first_name, last_name, now, now),
                )
            else:
                conn.execute(
                    """
                    UPDATE users
                    SET username = ?, first_name = ?, last_name = ?,
                        last_seen = ?, message_count = message_count + 1
                    WHERE telegram_id = ?
                    """,
                    (username, first_name, last_name, now, telegram_id),
                )

            conn.commit()
            row = conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()

        return self._row_to_profile(row), is_new, previous_last_seen

    def get_user(self, telegram_id: int) -> Optional[UserProfile]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()
        return self._row_to_profile(row) if row else None

    def set_preferred_name(self, telegram_id: int, preferred_name: str) -> None:
        clean = preferred_name.strip()[:50]
        if not clean:
            raise ValueError("Preferred name cannot be empty")

        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE users SET preferred_name = ? WHERE telegram_id = ?",
                (clean, telegram_id),
            )
            conn.commit()

    def remember(self, telegram_id: int, key: str, value: str) -> None:
        clean_key = key.strip().lower()[:80]
        clean_value = value.strip()[:300]
        if not clean_key or not clean_value:
            raise ValueError("Memory key and value are required")

        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memories (
                    telegram_id, memory_key, memory_value, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(telegram_id, memory_key)
                DO UPDATE SET
                    memory_value = excluded.memory_value,
                    updated_at = excluded.updated_at
                """,
                (telegram_id, clean_key, clean_value, now, now),
            )
            conn.commit()

    def recall(self, telegram_id: int, key: str) -> Optional[str]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT memory_value FROM memories
                WHERE telegram_id = ? AND memory_key = ?
                """,
                (telegram_id, key.strip().lower()),
            ).fetchone()
        return str(row["memory_value"]) if row else None

    def list_memories(self, telegram_id: int) -> list[tuple[str, str]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT memory_key, memory_value FROM memories
                WHERE telegram_id = ? AND memory_key NOT LIKE 'context_%'
                ORDER BY updated_at DESC
                """,
                (telegram_id,),
            ).fetchall()
        return [(str(row["memory_key"]), str(row["memory_value"])) for row in rows]

    def forget_memory(self, telegram_id: int, key: str) -> bool:
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM memories WHERE telegram_id = ? AND memory_key = ?",
                (telegram_id, key.strip().lower()),
            )
            conn.commit()
        return cursor.rowcount > 0

    def forget_user(self, telegram_id: int) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM memories WHERE telegram_id = ?", (telegram_id,))
            conn.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            conn.commit()

    @staticmethod
    def display_name(profile: UserProfile) -> str:
        return profile.preferred_name or profile.first_name or profile.username or "Champion"

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> UserProfile:
        return UserProfile(
            telegram_id=int(row["telegram_id"]),
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            preferred_name=row["preferred_name"],
            first_seen=str(row["first_seen"]),
            last_seen=str(row["last_seen"]),
            message_count=int(row["message_count"]),
        )
