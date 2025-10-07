"""Transcript knowledge base indexing and search."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

DEFAULT_DB_PATH = Path("vidmelt_kb.sqlite3")

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    video_name TEXT PRIMARY KEY,
    transcript_path TEXT NOT NULL,
    summary_path TEXT,
    transcript TEXT NOT NULL,
    summary TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    video_name,
    transcript,
    summary,
    content='documents',
    content_rowid='rowid'
);
"""

INDEX_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, video_name, transcript, summary)
    VALUES (new.rowid, new.video_name, new.transcript, new.summary);
END;
CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, video_name, transcript, summary)
    VALUES('delete', old.rowid, old.video_name, old.transcript, old.summary);
END;
CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, video_name, transcript, summary)
    VALUES('delete', old.rowid, old.video_name, old.transcript, old.summary);
    INSERT INTO documents_fts(rowid, video_name, transcript, summary)
    VALUES (new.rowid, new.video_name, new.transcript, new.summary);
END;
"""


@dataclass
class SearchHit:
    video_name: str
    transcript_path: str
    summary_path: Optional[str]
    snippet: str


class KnowledgeBase:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)
            conn.executescript(INDEX_TRIGGERS)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def index_directory(self, transcripts_dir: Path, summaries_dir: Path | None = None) -> None:
        transcripts_dir = transcripts_dir.resolve()
        summaries_dir = summaries_dir.resolve() if summaries_dir else None

        with self._connect() as conn:
            for transcript_path in sorted(transcripts_dir.glob("*.txt")):
                video_name = transcript_path.stem
                transcript_text = transcript_path.read_text(encoding="utf-8")
                summary_path = None
                summary_text = None
                if summaries_dir:
                    candidate = summaries_dir / f"{video_name}.md"
                    if candidate.exists():
                        summary_path = str(candidate)
                        summary_text = candidate.read_text(encoding="utf-8")

                conn.execute(
                    "REPLACE INTO documents (video_name, transcript_path, summary_path, transcript, summary) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        video_name,
                        str(transcript_path),
                        summary_path,
                        transcript_text,
                        summary_text,
                    ),
                )
            conn.commit()

    def search(self, query: str, *, limit: int = 5) -> Iterator[SearchHit]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT d.video_name, d.transcript_path, d.summary_path, "
                "snippet(documents_fts, -1, '[', ']', ' … ', 10) AS snippet "
                "FROM documents_fts JOIN documents d ON d.rowid = documents_fts.rowid "
                "WHERE documents_fts MATCH ? ORDER BY rank LIMIT ?",
                (query, limit),
            )
            for row in cur.fetchall():
                yield SearchHit(
                    video_name=row["video_name"],
                    transcript_path=row["transcript_path"],
                    summary_path=row["summary_path"],
                    snippet=row["snippet"],
                )


def index_documents(
    transcripts_dir: Path,
    summaries_dir: Path | None = None,
    *,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> None:
    kb = KnowledgeBase(db_path)
    kb.index_directory(transcripts_dir, summaries_dir)


def search(query: str, *, db_path: Path | str = DEFAULT_DB_PATH, limit: int = 5) -> Iterator[SearchHit]:
    kb = KnowledgeBase(db_path)
    yield from kb.search(query, limit=limit)


def main(argv: Iterable[str] | None = None) -> int:  # pragma: no cover - CLI entry
    import argparse

    parser = argparse.ArgumentParser(description="Vidmelt knowledge base CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Index transcripts and summaries")
    index_parser.add_argument("transcripts", type=Path)
    index_parser.add_argument("--summaries", type=Path)
    index_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)

    search_parser = subparsers.add_parser("search", help="Search indexed transcripts")
    search_parser.add_argument("query")
    search_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    search_parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "index":
        index_documents(args.transcripts, args.summaries, db_path=args.db)
        print(f"Indexed transcripts from {args.transcripts}")
        return 0
    if args.command == "search":
        for hit in search(args.query, db_path=args.db, limit=args.limit):
            print(f"[{hit.video_name}] {hit.snippet}")
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(main(sys.argv[1:]))
