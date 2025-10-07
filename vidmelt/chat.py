"""Chat interface over Vidmelt knowledge base."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from . import knowledge

DEFAULT_ANSWER_MODEL = "gpt-4o-mini"


def _load_answer_model():
    from openai import OpenAI

    client = OpenAI()
    return client


def generate_answer(question: str, hits: List[knowledge.SemanticHit], *, model: str = DEFAULT_ANSWER_MODEL):
    client = _load_answer_model()
    if callable(client) and not hasattr(client, "responses"):
        return client(question, hits)

    context_sections = []
    for idx, hit in enumerate(hits, 1):
        context_sections.append(
            f"[{idx}] Video: {hit.video_name}\nSnippet: {hit.snippet}\nTranscript: {hit.transcript_path}\n"
        )

    context = "\n".join(context_sections)
    prompt = (
        "You are an assistant that answers questions using only the supplied transcript snippets.\n"
        "If the answer is not contained in the context, say you don't know.\n"
        "Always cite sources using [index] that corresponds to the snippet.\n\n"
        f"Question: {question}\n"
        "Context:\n"
        f"{context}"
    )
    response = client.responses.create(
        model=model,
        input=[{"role": "user", "content": prompt}],
    )
    content = response.output[0].content[0].text
    return content


def chat(question: str, kb: knowledge.KnowledgeBase, *, top_k: int = 5) -> Tuple[str, List[dict]]:
    hits = list(kb.semantic_search(question, limit=top_k))
    if not hits:
        return "I could not find anything relevant.", []

    answer = generate_answer(question, hits)
    sources = [
        {
            "video": hit.video_name,
            "transcript": hit.transcript_path,
            "summary": hit.summary_path,
            "snippet": hit.snippet,
        }
        for hit in hits
    ]
    return answer, sources


def embed_cli(args: argparse.Namespace) -> int:
    kb = knowledge.KnowledgeBase(db_path=args.db)
    kb.build_embeddings(model_name=args.model)
    print(f"Embeddings built using {args.model} -> {args.db}")
    return 0


def search_cli(args: argparse.Namespace) -> int:
    kb = knowledge.KnowledgeBase(db_path=args.db)
    hits = kb.semantic_search(args.query, limit=args.limit)
    for hit in hits:
        print(f"[{hit.video_name}] {hit.snippet} (score={hit.score:.3f})")
    return 0


def chat_cli(args: argparse.Namespace) -> int:
    kb = knowledge.KnowledgeBase(db_path=args.db)
    answer, sources = chat(args.question, kb, top_k=args.limit)
    print(answer)
    print("\nSources:")
    for source in sources:
        print(f"- {source['video']}: {source['snippet']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vidmelt chat over knowledge base")
    subparsers = parser.add_subparsers(dest="command", required=True)

    embed_parser = subparsers.add_parser("embed", help="Compute embeddings for indexed documents")
    embed_parser.add_argument("--db", type=Path, default=knowledge.DEFAULT_DB_PATH)
    embed_parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")

    search_parser = subparsers.add_parser("search", help="Search indexed transcripts (vector)")
    search_parser.add_argument("query")
    search_parser.add_argument("--db", type=Path, default=knowledge.DEFAULT_DB_PATH)
    search_parser.add_argument("--limit", type=int, default=5)

    chat_parser = subparsers.add_parser("ask", help="Ask a question using RAG")
    chat_parser.add_argument("question")
    chat_parser.add_argument("--db", type=Path, default=knowledge.DEFAULT_DB_PATH)
    chat_parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "embed":
        return embed_cli(args)
    if args.command == "search":
        return search_cli(args)
    if args.command == "ask":
        return chat_cli(args)
    return 1


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(main(sys.argv[1:]))
