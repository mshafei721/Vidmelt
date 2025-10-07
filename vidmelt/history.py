"""Job history tracking for Vidmelt."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

DEFAULT_DB_PATH = Path("vidmelt_history.sqlite3")

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_path TEXT NOT NULL,
    summary_path TEXT,
    model TEXT NOT NULL,
    status TEXT NOT NULL,
    error TEXT,
    started_at REAL NOT NULL,
    finished_at REAL
);
"""

@dataclass
class JobRecord:
    id: int
    video_path: str
    summary_path: Optional[str]
    model: str
    status: str
    error: Optional[str]
    started_at: float
    finished_at: Optional[float]


class JobStore:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def record_start(self, video_path: Path, model: str) -> int:
        started = time.time()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO jobs (video_path, model, status, started_at) VALUES (?, ?, ?, ?)",
                (str(video_path), model, "processing", started),
            )
            conn.commit()
            return int(cur.lastrowid)

    def record_success(self, job_id: int, summary_path: Path) -> None:
        finished = time.time()
        with self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, summary_path = ?, finished_at = ?, error = NULL WHERE id = ?",
                ("complete", str(summary_path), finished, job_id),
            )
            conn.commit()

    def record_failure(self, job_id: int, error: str) -> None:
        finished = time.time()
        with self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, error = ?, finished_at = ? WHERE id = ?",
                ("failed", error, finished, job_id),
            )
            conn.commit()

    def list_recent(self, limit: int = 20) -> Iterator[JobRecord]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id, video_path, summary_path, model, status, error, started_at, finished_at "
                "FROM jobs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        for row in rows:
            yield JobRecord(*row)

    def pending_jobs(self) -> Iterator[JobRecord]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id, video_path, summary_path, model, status, error, started_at, finished_at "
                "FROM jobs WHERE status = 'processing' ORDER BY started_at"
            )
            rows = cur.fetchall()
        for row in rows:
            yield JobRecord(*row)


GLOBAL_STORE = JobStore(DEFAULT_DB_PATH)


def main(argv: Optional[Iterable[str]] = None) -> int:  # pragma: no cover - thin CLI
    print("Recent jobs:")
    for job in GLOBAL_STORE.list_recent():
        print(f"[{job.status}] {job.video_path} -> {job.summary_path or 'pending'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
