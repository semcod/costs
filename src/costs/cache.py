"""Bounded persistent cache of token counts, never source text or final prices."""

import hashlib
import importlib.metadata
import json
import os
import sqlite3
import time
from pathlib import Path

MAX_ENTRIES = 10_000
MAX_AGE_SECONDS = 30 * 24 * 3600
ESTIMATOR_VERSION = "review-diff-v2"
TOKENIZER_VERSION = importlib.metadata.version("tiktoken")


def estimate_key(diff, model, encoding):
    context = [ESTIMATOR_VERSION, model, encoding, TOKENIZER_VERSION]
    digest = hashlib.sha256(json.dumps(context).encode())
    digest.update(diff.encode("utf-8", errors="surrogatepass"))
    return digest.hexdigest()


class EstimateCache:
    """One connection per analysis; unavailable caches degrade to fresh counting."""

    def __init__(self, path=None):
        self.connection = None
        self.hits = self.misses = 0
        self.enabled = os.getenv("COSTS_CACHE", "1").lower() not in {
            "0",
            "false",
            "off",
        }
        if not self.enabled:
            return
        root = Path(
            os.getenv(
                "COSTS_CACHE_DIR",
                str(
                    Path(os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache")))
                    / "costs"
                ),
            )
        )
        path = Path(path) if path is not None else root / "estimates-v2.sqlite3"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(path, timeout=0.05)
            self.connection = connection
            connection.execute(
                "CREATE TABLE IF NOT EXISTS estimates (key TEXT PRIMARY KEY, created REAL NOT NULL, value TEXT NOT NULL)"
            )
            connection.execute(
                "DELETE FROM estimates WHERE created < ?",
                (time.time() - MAX_AGE_SECONDS,),
            )
            connection.commit()
        except (OSError, sqlite3.Error):
            self.close()

    def get(self, key):
        if self.connection is not None:
            try:
                row = self.connection.execute(
                    "SELECT value FROM estimates WHERE key = ? AND created >= ?",
                    (key, time.time() - MAX_AGE_SECONDS),
                ).fetchone()
                if row:
                    value = json.loads(row[0])
                    tokens, stats = value["tokens"], value["diff_stats"]
                    counts = [tokens[k] for k in ("input", "output", "total")] + [
                        stats[k]
                        for k in ("added_lines", "deleted_lines", "total_changed")
                    ]
                    if (
                        all(type(v) is int and v >= 0 for v in counts)
                        and tokens["total"] == tokens["input"] + tokens["output"]
                        and stats["total_changed"]
                        == stats["added_lines"] + stats["deleted_lines"]
                    ):
                        self.hits += 1
                        return value
            except (sqlite3.Error, ValueError, KeyError, TypeError):
                pass
        self.misses += 1
        return None

    def put(self, key, value):
        if self.connection is None:
            return
        try:
            self.connection.execute(
                "INSERT OR REPLACE INTO estimates VALUES (?, ?, ?)",
                (key, time.time(), json.dumps(value, allow_nan=False)),
            )
            self.connection.execute(
                "DELETE FROM estimates WHERE key IN (SELECT key FROM estimates ORDER BY created DESC LIMIT -1 OFFSET ?)",
                (MAX_ENTRIES,),
            )
            self.connection.commit()
        except (sqlite3.Error, ValueError, TypeError):
            self.close()

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
