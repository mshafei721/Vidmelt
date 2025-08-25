import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

DB_DIR = Path("data")
DB_PATH = DB_DIR / "vidmelt.db"


def init_db() -> None:
    DB_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT,
                platform TEXT,
                original_filename TEXT,
                video_title TEXT,
                transcript_path TEXT,
                summary_path TEXT,
                created_at TEXT
            );
            """
        )
        conn.commit()


def add_history(
    *,
    source_url: Optional[str],
    platform: Optional[str],
    original_filename: str,
    video_title: str,
    transcript_path: str,
    summary_path: str,
) -> int:
    created_at = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            INSERT INTO history (source_url, platform, original_filename, video_title, transcript_path, summary_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_url,
                platform,
                original_filename,
                video_title,
                transcript_path,
                summary_path,
                created_at,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_history(limit: int = 200) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, source_url, platform, original_filename, video_title, transcript_path, summary_path, created_at FROM history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

