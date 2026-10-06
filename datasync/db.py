"""SQLite storage with change detection, so only new or changed rows are written."""
import hashlib
import json
import sqlite3

import pandas as pd

TABLE = "records"


def _row_hash(row: dict) -> str:
    payload = json.dumps(row, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        f"""CREATE TABLE IF NOT EXISTS {TABLE} (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                row_hash TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
    )
    return conn


def sync_frame(conn: sqlite3.Connection, df: pd.DataFrame, key_column: str) -> dict:
    """Upsert rows keyed by key_column. Returns counts of inserted/updated/unchanged."""
    if key_column not in df.columns:
        raise KeyError(f"Key column '{key_column}' not in data. Columns: {list(df.columns)}")

    existing = dict(conn.execute(f"SELECT key, row_hash FROM {TABLE}").fetchall())
    stats = {"inserted": 0, "updated": 0, "unchanged": 0}

    for record in df.astype(object).where(df.notna(), None).to_dict("records"):
        key = str(record[key_column])
        digest = _row_hash(record)
        if key not in existing:
            conn.execute(
                f"INSERT INTO {TABLE} (key, data, row_hash) VALUES (?, ?, ?)",
                (key, json.dumps(record, default=str), digest),
            )
            stats["inserted"] += 1
        elif existing[key] != digest:
            conn.execute(
                f"UPDATE {TABLE} SET data=?, row_hash=?, updated_at=CURRENT_TIMESTAMP WHERE key=?",
                (json.dumps(record, default=str), digest, key),
            )
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1

    conn.commit()
    return stats


def read_frame(conn: sqlite3.Connection) -> pd.DataFrame:
    rows = [json.loads(r[0]) for r in conn.execute(f"SELECT data FROM {TABLE} ORDER BY key")]
    return pd.DataFrame(rows)
