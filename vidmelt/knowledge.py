"""Transcript knowledge base indexing, embeddings, and search."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Sequence

import numpy as np

DEFAULT_DB_PATH = Path("vidmelt_kb.sqlite3")
DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

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
CREATE TABLE IF NOT EXISTS embeddings (
    video_name TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding BLOB NOT NULL,
    norm REAL NOT NULL,
    PRIMARY KEY(video_name, chunk_index)
);
"""

TRIGGERS = """
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


@dataclass
class SemanticHit:
    video_name: str
    transcript_path: str
    summary_path: Optional[str]
    snippet: str
    score: float


@lru_cache(maxsize=2)
def _load_embeddings_model(model_name: str = DEFAULT_EMBED_MODEL):  # pragma: no cover
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _chunk_text(text: str, max_chars: int = 400) -> List[str]:
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    chunks: List[str] = []
    current: List[str] = []
    length = 0
    for sentence in sentences:
        if length + len(sentence) + 1 > max_chars and current:
            chunks.append(". ".join(current) + ".")
            current = [sentence]
            length = len(sentence)
        else:
            current.append(sentence)
            length += len(sentence) + 1
    if current:
        chunks.append(". ".join(current) + ".")
    if not chunks:
        chunks.append(text[:max_chars])
    return chunks


def _to_blob(vector: np.ndarray) -> bytes:
    return vector.astype(np.float32).tobytes()


def _from_blob(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


class KnowledgeBase:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)
            conn.executescript(TRIGGERS)

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

    # Embeddings -----------------------------------------------------------------
    def build_embeddings(self, *, model_name: str = DEFAULT_EMBED_MODEL) -> None:
        model = _load_embeddings_model(model_name)

        with self._connect() as conn:
            conn.execute("DELETE FROM embeddings")
            cur = conn.execute("SELECT video_name, transcript, summary FROM documents")
            rows = cur.fetchall()
            for row in rows:
                chunks = _chunk_text(row["summary"] or row["transcript"])
                vectors = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
                for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                    conn.execute(
                        "INSERT INTO embeddings (video_name, chunk_index, chunk_text, embedding, norm)"
                        " VALUES (?, ?, ?, ?, ?)",
                        (
                            row["video_name"],
                            idx,
                            chunk,
                            _to_blob(vector),
                            float(np.linalg.norm(vector)),
                        ),
                    )
            conn.commit()

    def semantic_search(self, query: str, *, limit: int = 5, model_name: str = DEFAULT_EMBED_MODEL) -> Iterator[SemanticHit]:
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
            if count == 0:
                for hit in self.search(query, limit=limit):
                    yield SemanticHit(
                        video_name=hit.video_name,
                        transcript_path=hit.transcript_path,
                        summary_path=hit.summary_path,
                        snippet=hit.snippet,
                        score=1.0,
                    )
                return

        model = _load_embeddings_model(model_name)
        query_vec = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]

        with self._connect() as conn:
            cur = conn.execute(
                "SELECT e.video_name, e.chunk_text, d.transcript_path, d.summary_path, e.embedding "
                "FROM embeddings e JOIN documents d ON d.video_name = e.video_name"
            )
            rows = cur.fetchall()

        hits: List[SemanticHit] = []
        for row in rows:
            embedding = _from_blob(row["embedding"])
            similarity = float(np.dot(query_vec, embedding))
            score = 1.0 - similarity
            hits.append(
                SemanticHit(
                    video_name=row["video_name"],
                    transcript_path=row["transcript_path"],
                    summary_path=row["summary_path"],
                    snippet=row["chunk_text"],
                    score=score,
                )
            )

        hits.sort(key=lambda hit: hit.score)
        for hit in hits[:limit]:
            yield hit


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


def semantic_search(query: str, *, db_path: Path | str = DEFAULT_DB_PATH, limit: int = 5) -> Iterator[SemanticHit]:
    kb = KnowledgeBase(db_path)
    yield from kb.semantic_search(query, limit=limit)


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI entry
    parser = argparse.ArgumentParser(description="Vidmelt knowledge base CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Index transcripts and summaries")
    index_parser.add_argument("transcripts", type=Path)
    index_parser.add_argument("--summaries", type=Path)
    index_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)

    search_parser = subparsers.add_parser("search", help="Search indexed transcripts (FTS)")
    search_parser.add_argument("query")
    search_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    search_parser.add_argument("--limit", type=int, default=5)

    embed_parser = subparsers.add_parser("embed", help="Build semantic embeddings")
    embed_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    embed_parser.add_argument("--model", default=DEFAULT_EMBED_MODEL)

    sem_search_parser = subparsers.add_parser("semantic", help="Semantic search using embeddings")
    sem_search_parser.add_argument("query")
    sem_search_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    sem_search_parser.add_argument("--limit", type=int, default=5)
    sem_search_parser.add_argument("--model", default=DEFAULT_EMBED_MODEL)

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "index":
        index_documents(args.transcripts, args.summaries, db_path=args.db)
        print(f"Indexed transcripts from {args.transcripts}")
        return 0
    if args.command == "search":
        for hit in search(args.query, db_path=args.db, limit=args.limit):
            print(f"[{hit.video_name}] {hit.snippet}")
        return 0
    if args.command == "embed":
        kb = KnowledgeBase(args.db)
        kb.build_embeddings(model_name=args.model)
        print(f"Embeddings built using {args.model}")
        return 0
    if args.command == "semantic":
        kb = KnowledgeBase(args.db)
        for hit in kb.semantic_search(args.query, limit=args.limit, model_name=args.model):
            print(f"[{hit.video_name}] {hit.snippet} (score={hit.score:.3f})")
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(main(sys.argv[1:]))
