import json

import pytest

import app
from vidmelt import knowledge


@pytest.fixture
def chat_client(monkeypatch):
    class DummyKB:
        def semantic_search(self, query, limit=5):
            yield knowledge.SemanticHit(
                video_name="demo",
                transcript_path="transcripts/demo.txt",
                summary_path="summaries/demo.md",
                snippet="Snippet about Python",
                score=0.1,
            )

    monkeypatch.setattr(app, "KB", DummyKB())
    monkeypatch.setattr(app, "generate_answer", lambda question, hits: (
        "Answer about Python",
        [
            {
                "video": hit.video_name,
                "snippet": hit.snippet,
                "summary": hit.summary_path,
                "score": hit.score,
            }
            for hit in hits
        ],
    ))
    return app.app.test_client()


def test_chat_endpoint(chat_client):
    response = chat_client.post(
        "/chat",
        data=json.dumps({"question": "What about Python?"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["answer"].startswith("Answer")
    assert data["sources"]
