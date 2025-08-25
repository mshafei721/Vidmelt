from pathlib import Path


def test_process_video_web_happy_path(tmp_path, monkeypatch):
    import app as app_mod

    # Point runtime dirs to tmp to avoid writing to repo
    app_mod.AUDIO_DIR = tmp_path / "audio"
    app_mod.TRANSCRIPT_DIR = tmp_path / "transcripts"
    app_mod.SUMMARY_DIR = tmp_path / "summaries"
    for d in (app_mod.AUDIO_DIR, app_mod.TRANSCRIPT_DIR, app_mod.SUMMARY_DIR):
        d.mkdir(parents=True, exist_ok=True)

    # Create a dummy uploaded video
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake mp4 contents")

    # Pretend ffmpeg exists
    monkeypatch.setattr(app_mod.shutil, "which", lambda _: "/usr/bin/ffmpeg")

    # No-op SSE publish
    class _SSE:
        @staticmethod
        def publish(*args, **kwargs):
            return None

    app_mod.sse.publish = _SSE.publish

    # Mock subprocess.run to create expected outputs
    def _subprocess_run(args, check=True, capture_output=True, text=True):
        if isinstance(args, (list, tuple)) and args:
            if args[0] == "ffmpeg":
                # Create non-empty audio file
                audio_path = app_mod.AUDIO_DIR / f"{video_path.stem}.wav"
                audio_path.write_bytes(b"pcm16 data")
                return type("CompletedProcess", (), {"stdout": "", "stderr": "", "returncode": 0})
            # Whisper local invocation
            if args[0] == app_mod.sys.executable and "whisper" in args:
                transcript_path = app_mod.TRANSCRIPT_DIR / f"{video_path.stem}.txt"
                transcript_path.write_text("transcribed text")
                return type("CompletedProcess", (), {"stdout": "", "stderr": "", "returncode": 0})
        raise AssertionError(f"Unexpected subprocess args: {args}")

    monkeypatch.setattr(app_mod.subprocess, "run", _subprocess_run)

    # Stub summarize_transcript to write out a summary
    import summarize as summarize_mod

    def _stub_summarize(transcript_path: Path, video_title: str):
        out = app_mod.SUMMARY_DIR / f"{video_title}.md"
        out.write_text("summary")

    summarize_mod.SUMMARY_DIR = app_mod.SUMMARY_DIR
    monkeypatch.setattr(summarize_mod, "summarize_transcript", _stub_summarize)

    # Act
    app_mod.process_video_web(video_path, "whisper-base")

    # Assert
    out = app_mod.SUMMARY_DIR / f"{video_path.stem}.md"
    assert out.exists(), "Summary was not generated"

