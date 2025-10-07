from pathlib import Path

from vidmelt import knowledge


def test_index_and_search(tmp_path):
    transcripts = tmp_path / "transcripts"
    summaries = tmp_path / "summaries"
    transcripts.mkdir()
    summaries.mkdir()

    (transcripts / "demo.txt").write_text("Python and Flask are great for rapid APIs.")
    (summaries / "demo.md").write_text("# Demo\nPython + Flask summary")
    (transcripts / "ml.txt").write_text("Machine learning with tensors and gradients.")

    db_path = tmp_path / "kb.sqlite3"

    knowledge.index_documents(transcripts, summaries, db_path=db_path)

    hits = list(knowledge.search("Python", db_path=db_path, limit=5))
    assert hits, "Expected Python query to return a result"
    assert hits[0].video_name == "demo"
    assert "Python" in hits[0].snippet

    # Ensure re-running index is idempotent and updates summaries
    (summaries / "ml.md").write_text("# ML\nNeural networks summary")
    knowledge.index_documents(transcripts, summaries, db_path=db_path)
    hits = list(knowledge.search("neural", db_path=db_path, limit=5))
    assert hits and hits[0].video_name == "ml"
    assert "Neural" in hits[0].snippet
