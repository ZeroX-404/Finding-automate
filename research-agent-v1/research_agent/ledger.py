from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import deque
from pathlib import Path
from typing import Any

from .models import EdgeRelation, ResearchState


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS objects (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    payload_hash TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS object_revisions (
    object_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (object_id, revision),
    FOREIGN KEY(object_id) REFERENCES objects(id)
);

CREATE TABLE IF NOT EXISTS edges (
    source_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    target_id TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_id, relation, target_id),
    FOREIGN KEY(source_id) REFERENCES objects(id),
    FOREIGN KEY(target_id) REFERENCES objects(id)
);

CREATE INDEX IF NOT EXISTS idx_objects_kind ON objects(kind);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_revisions_object ON object_revisions(object_id);
"""


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


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
            # Migrate the V1 tables before applying the full V1.1 schema.
            existing = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='objects'"
            ).fetchone()
            if existing:
                object_columns = {
                    row[1] for row in conn.execute("PRAGMA table_info(objects)").fetchall()
                }
                if "payload_hash" not in object_columns:
                    conn.execute("ALTER TABLE objects ADD COLUMN payload_hash TEXT")
                if "updated_at" not in object_columns:
                    conn.execute("ALTER TABLE objects ADD COLUMN updated_at TEXT")

                edge_exists = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='edges'"
                ).fetchone()
                if edge_exists:
                    edge_columns = {
                        row[1] for row in conn.execute("PRAGMA table_info(edges)").fetchall()
                    }
                    if "metadata_json" not in edge_columns:
                        conn.execute(
                            "ALTER TABLE edges ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'"
                        )

            conn.executescript(SCHEMA)
            self._backfill_hashes_and_revisions(conn)

    def _backfill_hashes_and_revisions(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            "SELECT id, kind, payload_json, created_at, payload_hash FROM objects"
        ).fetchall()
        for row in rows:
            canonical = _canonical_json(json.loads(row["payload_json"]))
            payload_hash = row["payload_hash"] or sha256_text(canonical)
            conn.execute(
                "UPDATE objects SET payload_json=?, payload_hash=?, updated_at=COALESCE(updated_at, created_at) WHERE id=?",
                (canonical, payload_hash, row["id"]),
            )
            has_revision = conn.execute(
                "SELECT 1 FROM object_revisions WHERE object_id=? LIMIT 1", (row["id"],)
            ).fetchone()
            if not has_revision:
                conn.execute(
                    """
                    INSERT INTO object_revisions(
                        object_id, revision, kind, payload_json, payload_hash, recorded_at
                    ) VALUES (?, 1, ?, ?, ?, ?)
                    """,
                    (row["id"], row["kind"], canonical, payload_hash, row["created_at"]),
                )

    def put(self, obj) -> str:
        payload = obj.model_dump(mode="json")
        canonical = _canonical_json(payload)
        payload_hash = sha256_text(canonical)
        created_at = payload.get("provenance", {}).get("created_at", "")
        kind = type(obj).__name__

        with self.connect() as conn:
            current = conn.execute(
                "SELECT kind, payload_hash FROM objects WHERE id=?", (obj.id,)
            ).fetchone()

            if current is None:
                conn.execute(
                    """
                    INSERT INTO objects(
                        id, kind, payload_json, created_at, payload_hash, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (obj.id, kind, canonical, created_at, payload_hash, created_at),
                )
                conn.execute(
                    """
                    INSERT INTO object_revisions(
                        object_id, revision, kind, payload_json, payload_hash
                    ) VALUES (?, 1, ?, ?, ?)
                    """,
                    (obj.id, kind, canonical, payload_hash),
                )
                return obj.id

            if current["kind"] != kind:
                raise ValueError(
                    f"Object {obj.id} already exists as {current['kind']}, not {kind}."
                )

            if current["payload_hash"] == payload_hash:
                return obj.id

            next_revision = conn.execute(
                "SELECT COALESCE(MAX(revision), 0) + 1 FROM object_revisions WHERE object_id=?",
                (obj.id,),
            ).fetchone()[0]
            conn.execute(
                """
                INSERT INTO object_revisions(
                    object_id, revision, kind, payload_json, payload_hash
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (obj.id, next_revision, kind, canonical, payload_hash),
            )
            conn.execute(
                """
                UPDATE objects
                SET payload_json=?, payload_hash=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (canonical, payload_hash, obj.id),
            )
        return obj.id

    def add_edge(
        self,
        source_id: str,
        relation: EdgeRelation | str,
        target_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        relation_value = EdgeRelation(relation).value
        metadata_json = _canonical_json(metadata or {})
        with self.connect() as conn:
            for object_id in (source_id, target_id):
                exists = conn.execute(
                    "SELECT 1 FROM objects WHERE id=?", (object_id,)
                ).fetchone()
                if not exists:
                    raise KeyError(f"Cannot create edge: {object_id} is not in ledger.")
            conn.execute(
                """
                INSERT OR IGNORE INTO edges(source_id, relation, target_id, metadata_json)
                VALUES (?, ?, ?, ?)
                """,
                (source_id, relation_value, target_id, metadata_json),
            )

    def get(self, object_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT kind, payload_json, payload_hash FROM objects WHERE id=?",
                (object_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "kind": row["kind"],
            "payload_hash": row["payload_hash"],
            "payload": json.loads(row["payload_json"]),
        }

    def history(self, object_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT revision, kind, payload_hash, payload_json, recorded_at
                FROM object_revisions
                WHERE object_id=?
                ORDER BY revision
                """,
                (object_id,),
            ).fetchall()
        return [
            {
                "revision": row["revision"],
                "kind": row["kind"],
                "payload_hash": row["payload_hash"],
                "recorded_at": row["recorded_at"],
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]

    def graph(self, object_id: str) -> dict:
        with self.connect() as conn:
            outgoing = conn.execute(
                "SELECT relation, target_id, metadata_json FROM edges WHERE source_id=?",
                (object_id,),
            ).fetchall()
            incoming = conn.execute(
                "SELECT source_id, relation, metadata_json FROM edges WHERE target_id=?",
                (object_id,),
            ).fetchall()
        return {
            "object": self.get(object_id),
            "outgoing": [
                {
                    "relation": r["relation"],
                    "target_id": r["target_id"],
                    "metadata": json.loads(r["metadata_json"]),
                }
                for r in outgoing
            ],
            "incoming": [
                {
                    "source_id": r["source_id"],
                    "relation": r["relation"],
                    "metadata": json.loads(r["metadata_json"]),
                }
                for r in incoming
            ],
        }

    def trace(self, object_id: str, max_depth: int = 4) -> dict[str, Any]:
        if self.get(object_id) is None:
            raise KeyError(f"Unknown object: {object_id}")

        queue = deque([(object_id, 0)])
        seen = {object_id}
        nodes: dict[str, Any] = {}
        edges: list[dict[str, Any]] = []
        edge_keys: set[tuple[str, str, str]] = set()

        while queue:
            current, depth = queue.popleft()
            nodes[current] = self.get(current)
            if depth >= max_depth:
                continue

            local = self.graph(current)
            for edge in local["outgoing"]:
                target = edge["target_id"]
                key = (current, edge["relation"], target)
                if key not in edge_keys:
                    edge_keys.add(key)
                    edges.append(
                        {
                            "source_id": current,
                            "relation": edge["relation"],
                            "target_id": target,
                            "metadata": edge["metadata"],
                        }
                    )
                if target not in seen:
                    seen.add(target)
                    queue.append((target, depth + 1))

            for edge in local["incoming"]:
                source = edge["source_id"]
                key = (source, edge["relation"], current)
                if key not in edge_keys:
                    edge_keys.add(key)
                    edges.append(
                        {
                            "source_id": source,
                            "relation": edge["relation"],
                            "target_id": current,
                            "metadata": edge["metadata"],
                        }
                    )
                if source not in seen:
                    seen.add(source)
                    queue.append((source, depth + 1))

        return {"root": object_id, "nodes": nodes, "edges": edges}

    def audit(self) -> dict[str, Any]:
        issues: list[dict[str, str]] = []

        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, kind, payload_json, payload_hash FROM objects"
            ).fetchall()

            known_ids = {row["id"] for row in rows}

            for row in rows:
                canonical = _canonical_json(json.loads(row["payload_json"]))
                expected_hash = sha256_text(canonical)
                if row["payload_hash"] != expected_hash:
                    issues.append(
                        {
                            "code": "CURRENT_HASH_MISMATCH",
                            "object_id": row["id"],
                            "message": "Current payload hash does not match payload.",
                        }
                    )

                payload = json.loads(row["payload_json"])
                references = []
                for field in (
                    "source_id",
                    "method_id",
                    "experiment_id",
                    "hypothesis_id",
                    "subject_id",
                ):
                    value = payload.get(field)
                    if value:
                        references.append((field, value))
                for field in (
                    "observation_ids",
                    "claim_ids",
                    "evidence_ids",
                    "validation_ids",
                    "critic_ids",
                ):
                    for value in payload.get(field, []) or []:
                        references.append((field, value))

                for field, referenced_id in references:
                    if referenced_id not in known_ids:
                        issues.append(
                            {
                                "code": "MISSING_REFERENCE",
                                "object_id": row["id"],
                                "message": f"{field} references missing object {referenced_id}.",
                            }
                        )

                if row["kind"] == "Finding" and payload.get("state") == ResearchState.CONFIRMED.value:
                    if not payload.get("evidence_ids"):
                        issues.append(
                            {
                                "code": "CONFIRMED_WITHOUT_EVIDENCE",
                                "object_id": row["id"],
                                "message": "Confirmed finding has no evidence IDs.",
                            }
                        )
                    if not payload.get("validation_ids"):
                        issues.append(
                            {
                                "code": "CONFIRMED_WITHOUT_VALIDATION",
                                "object_id": row["id"],
                                "message": "Confirmed finding has no validation IDs.",
                            }
                        )

            revision_rows = conn.execute(
                "SELECT object_id, revision, payload_json, payload_hash FROM object_revisions"
            ).fetchall()
            for row in revision_rows:
                canonical = _canonical_json(json.loads(row["payload_json"]))
                if row["payload_hash"] != sha256_text(canonical):
                    issues.append(
                        {
                            "code": "REVISION_HASH_MISMATCH",
                            "object_id": row["object_id"],
                            "message": f"Revision {row['revision']} hash mismatch.",
                        }
                    )

        return {
            "ok": len(issues) == 0,
            "objects": len(rows),
            "issues": issues,
        }
