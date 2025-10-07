from pathlib import Path
from types import SimpleNamespace

import numpy as np
from vidmelt import knowledge


def test_embedding_pipeline(tmp_path, monkeypatch):
    transcripts = tmp_path / "transcripts"
    transcripts.mkdir()
    (transcripts / "clip.txt").write_text("Python is great. Flask builds APIs. Python rocks.")

    summaries = tmp_path / "summaries"
    summaries.mkdir()
    (summaries / "clip.md").write_text("# Clip\nPython summary")

    monkeypatch.setattr(
        knowledge,
        "_load_embeddings_model",
        lambda model_name=knowledge.DEFAULT_EMBED_MODEL: SimpleNamespace(
            encode=lambda items, **_: [np.ones(3, dtype=np.float32) * i for i, _ in enumerate(items)]
        ),
    )

    db_path = tmp_path / "kb.sqlite3"
    kb = knowledge.KnowledgeBase(db_path=db_path)
    kb.index_directory(transcripts, summaries)
    kb.build_embeddings(model_name="dummy")

    with kb._connect() as conn:
        rows = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()
        assert rows[0] > 0

    hits = list(kb.semantic_search("Python", limit=3))
    assert hits
    assert hits[0].video_name == "clip"
    assert hits[0].score <= hits[-1].score
