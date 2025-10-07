from pathlib import Path

from types import SimpleNamespace

from vidmelt import chat


def test_chat_cli(monkeypatch, tmp_path, capsys):
    transcripts = tmp_path / "transcripts"
    transcripts.mkdir()
    (transcripts / "demo.txt").write_text("Python and Flask.")

    summaries = tmp_path / "summaries"
    summaries.mkdir()
    (summaries / "demo.md").write_text("# Demo\nPython summary")

    kb_path = tmp_path / "kb.sqlite3"

    monkeypatch.setattr(chat.knowledge, "index_documents", lambda *args, **kwargs: None)

    class DummyKB:
        def __init__(self, db_path):
            pass

        def semantic_search(self, query, limit=5, model_name=chat.knowledge.DEFAULT_EMBED_MODEL):
            return [
                chat.knowledge.SemanticHit(
                    video_name="demo",
                    transcript_path="transcripts/demo.txt",
                    summary_path="summaries/demo.md",
                    snippet="Python and Flask.",
                    score=0.1,
                )
            ]

    monkeypatch.setattr(chat.knowledge, "KnowledgeBase", lambda db_path: DummyKB(db_path))
    monkeypatch.setattr(chat, "_load_answer_model", lambda: SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(output=[SimpleNamespace(content=[SimpleNamespace(text="Answer")])]))))

    exit_code = chat.main(["search", "Python", "--db", str(kb_path)])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "[demo]" in output
