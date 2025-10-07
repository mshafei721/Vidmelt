import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import app as app_module
import summarize as summarize_module
import vidmelt.pipeline as pipeline_module


@pytest.fixture
def temp_dirs(tmp_path, monkeypatch):
    videos = tmp_path / "videos"
    audio = tmp_path / "audio_files"
    transcripts = tmp_path / "transcripts"
    summaries = tmp_path / "summaries"
    logs = tmp_path / "logs"
    for path in (videos, audio, transcripts, summaries, logs):
        path.mkdir(parents=True, exist_ok=True)

    # Rebind directory globals across modules
    monkeypatch.setattr(pipeline_module, "UPLOAD_FOLDER", videos)
    monkeypatch.setattr(pipeline_module, "AUDIO_DIR", audio)
    monkeypatch.setattr(pipeline_module, "TRANSCRIPT_DIR", transcripts)
    monkeypatch.setattr(pipeline_module, "SUMMARY_DIR", summaries)
    monkeypatch.setattr(pipeline_module, "LOG_DIR", logs)

    monkeypatch.setattr(app_module, "UPLOAD_FOLDER", videos)
    monkeypatch.setattr(app_module, "SUMMARY_DIR", summaries)
    monkeypatch.setattr(app_module, "TRANSCRIPT_DIR", transcripts)

    monkeypatch.setattr(summarize_module, "TRANSCRIPT_DIR", transcripts)
    monkeypatch.setattr(summarize_module, "SUMMARY_DIR", summaries)

    events = []
    store_events = SimpleNamespace(started=[], succeeded=[], failed=[], retries=[])

    class DummyBus:
        def publish(self, payload, event_type):
            events.append((event_type, payload.get("message", "")))

    monkeypatch.setattr(app_module, "EVENT_BUS", DummyBus())

    class DummyStore:
        def __init__(self):
            self._counter = 0

        def record_start(self, video_path, model):
            self._counter += 1
            store_events.started.append((Path(video_path), model))
            return self._counter

        def record_retry(self, job_id):
            store_events.retries.append(job_id)

        def record_success(self, job_id, summary_path):
            store_events.succeeded.append((job_id, Path(summary_path)))

        def record_failure(self, job_id, error):
            store_events.failed.append((job_id, error))

    dummy_store = DummyStore()
    monkeypatch.setattr(pipeline_module.history, "GLOBAL_STORE", dummy_store)

    return SimpleNamespace(
        videos=videos,
        audio=audio,
        transcripts=transcripts,
        summaries=summaries,
        logs=logs,
        events=events,
        store=dummy_store,
        store_events=store_events,
    )


def test_process_video_skips_transcription_when_transcript_exists(monkeypatch, temp_dirs):
    video_path = temp_dirs.videos / "sample.mp4"
    video_path.write_bytes(b"video")

    audio_path = temp_dirs.audio / "sample.wav"
    audio_path.write_bytes(b"audio-bytes")

    transcript_path = temp_dirs.transcripts / "sample.txt"
    transcript_path.write_text("already transcribed")

    summary_path = temp_dirs.summaries / "sample.md"
    events = temp_dirs.events
    store_events = temp_dirs.store_events

    def fake_summarize(path, title):
        assert path == transcript_path
        generated_path = temp_dirs.summaries / f"{title}.md"
        generated_path.write_text("summary")

    monkeypatch.setattr(pipeline_module, "summarize_transcript", fake_summarize)
    monkeypatch.setattr(pipeline_module.shutil, "which", lambda name: "/usr/bin/ffmpeg")

    def fail_run(*args, **kwargs):  # pragma: no cover - should not run
        raise AssertionError("subprocess.run should not be invoked when transcript exists")

    monkeypatch.setattr(pipeline_module.subprocess, "run", fail_run)

    app_module.process_video_web(video_path, "whisper-base")

    assert summary_path.exists(), "Summary should still be generated from cached transcript"
    assert any("skipping re-transcription" in message for _type, message in events)
    complete_events = [message for event_type, message in events if event_type == "complete"]
    assert complete_events, "Completion event with download links is expected"
    complete_message = complete_events[-1]
    assert "summaries/sample.md" in complete_message
    assert "transcripts/sample.txt" in complete_message
    assert store_events.started and store_events.started[0][0].name == "sample.mp4"
    assert store_events.succeeded and not store_events.failed


def test_process_video_reports_summarization_errors(monkeypatch, temp_dirs):
    video_path = temp_dirs.videos / "demo.mp4"
    video_path.write_bytes(b"video")

    audio_path = temp_dirs.audio / "demo.wav"
    transcript_path = temp_dirs.transcripts / "demo.txt"
    summary_path = temp_dirs.summaries / "demo.md"
    events = temp_dirs.events
    store_events = temp_dirs.store_events

    def fake_run(cmd, **kwargs):
        if "ffmpeg" in cmd[0]:
            audio_path.write_bytes(b"audio")
        elif "whisper" in cmd:
            transcript_path.write_text("transcript")
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    def failing_summarize(path, title):
        raise summarize_module.SummarizationError("boom")

    monkeypatch.setattr(pipeline_module.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(pipeline_module.subprocess, "run", fake_run)
    monkeypatch.setattr(pipeline_module, "summarize_transcript", failing_summarize)

    app_module.process_video_web(video_path, "whisper-base")

    assert not summary_path.exists(), "Summary file should not be written when summarization fails"
    assert any("boom" in message for event_type, message in events if event_type == "error"), "Error SSE should include root cause"
    assert not any(event_type == "complete" for event_type, _ in events), "Completion event must not fire on failure"
    assert store_events.failed and not store_events.succeeded


def test_process_video_logs_outputs(monkeypatch, temp_dirs):
    video_path = temp_dirs.videos / "logdemo.mp4"
    video_path.write_bytes(b"video")

    audio_path = temp_dirs.audio / "logdemo.wav"
    transcript_path = temp_dirs.transcripts / "logdemo.txt"

    def fake_run(cmd, **kwargs):
        if cmd[0] == "ffmpeg":
            audio_path.write_bytes(b"audio")
            return SimpleNamespace(stdout="ffmpeg out", stderr="ffmpeg err")
        elif cmd[0] == sys.executable and "whisper" in cmd:
            transcript_path.write_text("transcript")
            return SimpleNamespace(stdout="whisper out", stderr="whisper err")
        raise AssertionError("Unexpected command")

    monkeypatch.setattr(pipeline_module.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(pipeline_module.subprocess, "run", fake_run)
    monkeypatch.setattr(pipeline_module, "summarize_transcript", lambda path, title: temp_dirs.summaries.joinpath(f"{title}.md").write_text("summary"))

    store_events = temp_dirs.store_events

    result = pipeline_module.process_video(video_path, "whisper-base", publish=lambda payload, event_type: None)
    assert result is True

    log_files = sorted(temp_dirs.logs.glob("logdemo-*.log"))
    assert len(log_files) == 2
    contents = "\n".join(path.read_text() for path in log_files)
    assert "ffmpeg out" in contents
    assert "whisper out" in contents
    assert store_events.succeeded


def test_process_video_retry(monkeypatch, temp_dirs):
    video_path = temp_dirs.videos / "retry.mp4"
    video_path.write_bytes(b"video")

    audio_path = temp_dirs.audio / "retry.wav"
    audio_path.write_bytes(b"audio")
    transcript_path = temp_dirs.transcripts / "retry.txt"
    transcript_path.write_text("existing transcript")

    store_events = temp_dirs.store_events

    def fake_summarize(path, title):
        temp_dirs.summaries.joinpath(f"{title}.md").write_text("summary")

    monkeypatch.setattr(pipeline_module.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(pipeline_module, "summarize_transcript", fake_summarize)

    result = pipeline_module.process_video(
        video_path,
        "whisper-base",
        publish=lambda payload, event_type: None,
        job_id=42,
    )

    assert result is True
    assert store_events.retries == [42]
