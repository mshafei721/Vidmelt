from types import SimpleNamespace

import pytest

import app
from vidmelt import history


@pytest.fixture
def client(monkeypatch):
    class FakeStore:
        def list_recent(self, limit=50):
            return [
                history.JobRecord(
                    id=1,
                    video_path="videos/demo.mp4",
                    summary_path="summaries/demo.md",
                    model="whisper-base",
                    status="complete",
                    error=None,
                    started_at=123.0,
                    finished_at=456.0,
                    attempt_count=1,
                )
            ]

    monkeypatch.setattr(history, "GLOBAL_STORE", FakeStore())
    return app.app.test_client()


def test_jobs_page_renders(client):
    response = client.get("/jobs")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "videos/demo.mp4" in body
    assert "Download" in body
