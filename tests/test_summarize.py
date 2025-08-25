import types
from pathlib import Path

import pytest


def test_summarize_transcript_writes_summary(tmp_path, monkeypatch):
    # Arrange
    from summarize import summarize_transcript as fn
    import summarize as summarize_mod

    # Create a fake transcript file
    transcript = tmp_path / "sample.txt"
    transcript.write_text("This is a short transcript for testing.")

    # Redirect SUMMARY_DIR to tmp
    monkeypatch.setattr(summarize_mod, "SUMMARY_DIR", tmp_path)

    # Fake OpenAI client with the expected shape
    class _Msg:
        content = "Fake summary content"

    class _Choice:
        message = _Msg()

    class _Response:
        choices = [_Choice()]

    class _ChatCompletions:
        def create(self, model, messages):  # noqa: D401
            return _Response()

    class _Chat:
        completions = _ChatCompletions()

    class _Client:
        chat = _Chat()

    import openai

    monkeypatch.setattr(openai, "OpenAI", lambda: _Client())

    # Act
    fn(transcript, "video_title")

    # Assert
    out = tmp_path / "video_title.md"
    assert out.exists(), "Summary file was not created"
    assert out.read_text() == "Fake summary content"

