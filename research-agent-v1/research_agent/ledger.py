from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import Evidence, Finding, Hypothesis, Observation, Validation


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS objects (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS edges (
    source_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    target_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_id, relation, target_id),
    FOREIGN KEY(source_id) REFERENCES objects(id),
    FOREIGN KEY(target_id) REFERENCES objects(id)
);

CREATE INDEX IF NOT EXISTS idx_objects_kind ON objects(kind);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
"""


class Ledger:
    def __init__(self, path: str | Path = "evidence.db") -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def put(self, obj) -> str:
        payload = obj.model_dump(mode="json")
        created_at = payload.get("provenance", {}).get("created_at", "")
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO objects(id, kind, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (obj.id, type(obj).__name__, json.dumps(payload, sort_keys=True), created_at),
            )
        return obj.id

    def add_edge(self, source_id: str, relation: str, target_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO edges(source_id, relation, target_id) VALUES (?, ?, ?)",
                (source_id, relation, target_id),
            )

    def get(self, object_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT kind, payload_json FROM objects WHERE id = ?", (object_id,)
            ).fetchone()
        if not row:
            return None
        return {"kind": row["kind"], "payload": json.loads(row["payload_json"])}

    def graph(self, object_id: str) -> dict:
        with self.connect() as conn:
            outgoing = conn.execute(
                "SELECT relation, target_id FROM edges WHERE source_id = ?", (object_id,)
            ).fetchall()
            incoming = conn.execute(
                "SELECT source_id, relation FROM edges WHERE target_id = ?", (object_id,)
            ).fetchall()
        return {
            "object": self.get(object_id),
            "outgoing": [dict(r) for r in outgoing],
            "incoming": [dict(r) for r in incoming],
        }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    return sha256_bytes(p.read_bytes())
