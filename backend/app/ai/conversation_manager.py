# backend/app/ai/conversation_manager.py
import sqlite3
import json
import os
from collections import deque
from datetime import datetime


class ConversationManager:
    """
    Manages short-term memory (last N turns in RAM) and long-term memory (SQLite).
    """

    SHORT_TERM_MAX = 20  # max turns kept in RAM

    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data"
            )
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "marvin_memory.db")

        self.db_path = db_path
        self._short_term: deque = deque(maxlen=self.SHORT_TERM_MAX)
        self._init_db()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_message(self, role: str, content: str):
        """Add a message to short-term memory and persist to SQLite."""
        message = {"role": role, "content": content}
        self._short_term.append(message)
        self._persist(role, content)

    def get_history(self) -> list[dict]:
        """Return the current short-term conversation history."""
        return list(self._short_term)

    def clear_short_term(self):
        """Wipe the in-RAM conversation (e.g. on session restart)."""
        self._short_term.clear()

    def search_long_term(self, keyword: str, limit: int = 5) -> list[dict]:
        """Search SQLite history for messages containing keyword."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT role, content, created_at FROM messages "
                "WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{keyword}%", limit),
            ).fetchall()
        return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in rows]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    role      TEXT    NOT NULL,
                    content   TEXT    NOT NULL,
                    created_at TEXT   NOT NULL
                )
                """
            )
            conn.commit()

    def _persist(self, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
                (role, content, datetime.utcnow().isoformat()),
            )
            conn.commit()
