import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import app as app_module
import summarize as summarize_module


@pytest.fixture
def temp_dirs(tmp_path, monkeypatch):
    videos = tmp_path / "videos"
    audio = tmp_path / "audio_files"
    transcripts = tmp_path / "transcripts"
    summaries = tmp_path / "summaries"
    for path in (videos, audio, transcripts, summaries):
        path.mkdir(parents=True, exist_ok=True)

    # Rebind directory globals in app.py and summarize.py
    monkeypatch.setattr(app_module, "UPLOAD_FOLDER", videos)
    monkeypatch.setattr(app_module, "AUDIO_DIR", audio)
    monkeypatch.setattr(app_module, "TRANSCRIPT_DIR", transcripts)
    monkeypatch.setattr(app_module, "SUMMARY_DIR", summaries)

    monkeypatch.setattr(summarize_module, "TRANSCRIPT_DIR", transcripts)
    monkeypatch.setattr(summarize_module, "SUMMARY_DIR", summaries)

    return SimpleNamespace(
        videos=videos,
        audio=audio,
        transcripts=transcripts,
        summaries=summaries,
    )


def test_process_video_skips_transcription_when_transcript_exists(monkeypatch, temp_dirs):
    video_path = temp_dirs.videos / "sample.mp4"
    video_path.write_bytes(b"video")

    audio_path = temp_dirs.audio / "sample.wav"
    audio_path.write_bytes(b"audio-bytes")

    transcript_path = temp_dirs.transcripts / "sample.txt"
    transcript_path.write_text("already transcribed")

    summary_path = temp_dirs.summaries / "sample.md"

    events = []

    def fake_publish(payload, type):
        events.append((type, payload["message"]))

    def fake_summarize(path, title):
        assert path == transcript_path
        generated_path = temp_dirs.summaries / f"{title}.md"
        generated_path.write_text("summary")

    monkeypatch.setattr(app_module.sse, "publish", fake_publish)
    monkeypatch.setattr(summarize_module, "summarize_transcript", fake_summarize)
    monkeypatch.setattr(app_module.shutil, "which", lambda name: "/usr/bin/ffmpeg")

    def fail_run(*args, **kwargs):  # pragma: no cover - should not run
        raise AssertionError("subprocess.run should not be invoked when transcript exists")

    monkeypatch.setattr(app_module.subprocess, "run", fail_run)

    app_module.process_video_web(video_path, "whisper-base")

    assert summary_path.exists(), "Summary should still be generated from cached transcript"
    assert any("skipping re-transcription" in message for _type, message in events)
    complete_events = [message for event_type, message in events if event_type == "complete"]
    assert complete_events, "Completion event with download links is expected"
    complete_message = complete_events[-1]
    assert "summaries/sample.md" in complete_message
    assert "transcripts/sample.txt" in complete_message


def test_process_video_reports_summarization_errors(monkeypatch, temp_dirs):
    video_path = temp_dirs.videos / "demo.mp4"
    video_path.write_bytes(b"video")

    audio_path = temp_dirs.audio / "demo.wav"
    transcript_path = temp_dirs.transcripts / "demo.txt"
    summary_path = temp_dirs.summaries / "demo.md"

    events = []

    def fake_publish(payload, type):
        events.append((type, payload["message"]))

    def fake_run(cmd, **kwargs):
        if "ffmpeg" in cmd[0]:
            audio_path.write_bytes(b"audio")
        elif "whisper" in cmd:
            transcript_path.write_text("transcript")
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    def failing_summarize(path, title):
        raise summarize_module.SummarizationError("boom")

    monkeypatch.setattr(app_module.sse, "publish", fake_publish)
    monkeypatch.setattr(app_module.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(app_module.subprocess, "run", fake_run)
    monkeypatch.setattr(summarize_module, "summarize_transcript", failing_summarize)

    app_module.process_video_web(video_path, "whisper-base")

    assert not summary_path.exists(), "Summary file should not be written when summarization fails"
    assert any("boom" in message for event_type, message in events if event_type == "error"), "Error SSE should include root cause"
    assert not any(event_type == "complete" for event_type, _ in events), "Completion event must not fire on failure"
