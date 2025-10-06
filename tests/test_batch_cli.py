import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_batch_cli_dry_run(tmp_path, monkeypatch, capsys):
    videos = tmp_path / "videos"
    videos.mkdir()
    (videos / "first.mp4").write_bytes(b"video")
    (videos / "second.mp4").write_bytes(b"video")

    import vidmelt.batch as batch

    summaries = tmp_path / "summaries"
    logs = tmp_path / "logs"
    summaries.mkdir()
    logs.mkdir()

    monkeypatch.setattr(batch.pipeline, "UPLOAD_FOLDER", videos)
    monkeypatch.setattr(batch.pipeline, "SUMMARY_DIR", summaries)
    monkeypatch.setattr(batch.pipeline, "LOG_DIR", logs)

    processed = []
    monkeypatch.setattr(batch.pipeline, "process_video", lambda *args, **kwargs: processed.append(args[0]))

    args = SimpleNamespace(input_dir=videos, model="whisper-base", dry_run=True)
    exit_code = batch.batch_process(args)

    assert exit_code == 0
    assert not processed, "Dry run should not call pipeline"
    output = capsys.readouterr().out
    assert "Discovered 2 video(s)" in output
    assert "first.mp4" in output and "second.mp4" in output


def test_batch_cli_skips_completed(tmp_path, monkeypatch):
    videos = tmp_path / "videos"
    videos.mkdir()
    completed = tmp_path / "summaries"
    completed.mkdir()

    pending = videos / "pending.mp4"
    pending.write_bytes(b"video")
    done = videos / "done.mp4"
    done.write_bytes(b"video")
    (completed / "done.md").write_text("summary")

    import vidmelt.batch as batch

    logs = tmp_path / "logs"
    logs.mkdir()

    monkeypatch.setattr(batch.pipeline, "UPLOAD_FOLDER", videos)
    monkeypatch.setattr(batch.pipeline, "SUMMARY_DIR", completed)
    monkeypatch.setattr(batch.pipeline, "LOG_DIR", logs)

    calls = []

    def fake_process(video_path, model, publish=None):
        calls.append((video_path, model))

    monkeypatch.setattr(batch.pipeline, "process_video", fake_process)

    args = SimpleNamespace(input_dir=videos, model="whisper-base", dry_run=False)
    exit_code = batch.batch_process(args)

    assert exit_code == 0
    assert calls == [(pending, "whisper-base")], "CLI should skip videos with existing summaries"
