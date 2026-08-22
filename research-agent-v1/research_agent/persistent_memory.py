from __future__ import annotations

import sqlite3
import json

from datetime import datetime, timezone



class PersistentMemory:


    def __init__(
        self,
        path="agent_memory.db",
    ):

        self.path = path

        self.init()



    def connect(self):

        conn = sqlite3.connect(
            self.path
        )

        return conn



    def init(self):

        with self.connect() as conn:

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    category TEXT NOT NULL,

                    payload TEXT NOT NULL,

                    created_at TEXT NOT NULL

                )
                """
            )



    def store(
        self,
        category: str,
        data: dict,
    ):

        with self.connect() as conn:

            conn.execute(
                """
                INSERT INTO memories
                (
                    category,
                    payload,
                    created_at
                )

                VALUES (?, ?, ?)
                """,

                (
                    category,
                    json.dumps(
                        data
                    ),
                    datetime.now(
                        timezone.utc
                    ).isoformat(),
                ),
            )



    def query(
        self,
        category: str,
    ):

        with self.connect() as conn:

            rows = conn.execute(
                """
                SELECT payload
                FROM memories
                WHERE category=?
                """,

                (
                    category,
                ),

            ).fetchall()


        return [
            json.loads(
                row[0]
            )
            for row in rows
        ]



    def count(self):

        with self.connect() as conn:

            result = conn.execute(
                """
                SELECT COUNT(*)
                FROM memories
                """
            ).fetchone()


        return result[0]
