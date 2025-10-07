"""Core processing pipeline shared between web and CLI entrypoints."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

import openai

from summarize import SummarizationError, summarize_transcript
from vidmelt import history

Publisher = Callable[[dict[str, str], str], None]

UPLOAD_FOLDER = Path("videos")
AUDIO_DIR = Path("audio_files")
TRANSCRIPT_DIR = Path("transcripts")
SUMMARY_DIR = Path("summaries")
LOG_DIR = Path("logs")

for directory in (UPLOAD_FOLDER, AUDIO_DIR, TRANSCRIPT_DIR, SUMMARY_DIR, LOG_DIR):
    directory.mkdir(exist_ok=True)


def _emit(publish: Optional[Publisher], event_type: str, message: str, icon: str | None = None) -> None:
    if publish is None:
        return
    payload = {"message": message}
    if icon:
        payload["icon"] = icon
    publish(payload, event_type)


def _write_log(video_name: str, stage: str, stdout: Optional[str], stderr: Optional[str]) -> None:
    content = []
    if stdout:
        content.append("# STDOUT\n" + stdout.strip())
    if stderr:
        content.append("# STDERR\n" + stderr.strip())
    if not content:
        return
    log_path = LOG_DIR / f"{video_name}-{stage}.log"
    log_path.write_text("\n\n".join(content) + "\n")


def process_video(
    video_path: Path,
    transcription_model: str,
    publish: Optional[Publisher] = None,
    job_store: Optional[history.JobStore] = None,
) -> bool:
    """Process a single video and return True on success."""

    if shutil.which("ffmpeg") is None:
        msg = "Oops! FFmpeg is playing hide-and-seek. Please install it and try again! 🕵️‍♂️"
        _emit(publish, "error", msg, "❌")
        return False

    video_name = video_path.stem
    audio_path = AUDIO_DIR / f"{video_name}.wav"
    transcript_path = TRANSCRIPT_DIR / f"{video_name}.txt"
    summary_path = SUMMARY_DIR / f"{video_name}.md"
    job_store = job_store or history.GLOBAL_STORE
    job_id = job_store.record_start(video_path, transcription_model)

    try:
        if not audio_path.exists():
            _emit(publish, "update", f"Extracting audio from {video_name}... This might take a moment, our digital ears are tuning in! 🎧", "🎶")
            ffmpeg_result = subprocess.run([
                "ffmpeg",
                "-i", str(video_path),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(audio_path)
            ], check=True, capture_output=True, text=True)
            _emit(publish, "update", f"Audio extracted: {audio_path.name} - Success! Our digital ears are happy. 🎉", "✅")
            _write_log(video_name, "ffmpeg", ffmpeg_result.stdout, ffmpeg_result.stderr)

        if not audio_path.exists() or audio_path.stat().st_size == 0:
            msg = f"Error: Audio file {audio_path.name} was not created or is empty. Cannot proceed with transcription. 🚫"
            _emit(publish, "error", msg, "❌")
            return False

        transcript_exists = transcript_path.exists()
        _emit(publish, "update", f"Checking if transcript exists: {transcript_exists}")

        if not transcript_exists:
            _emit(publish, "update", f"Transcribing audio for {video_name}... Our AI is listening intently! 👂", "✍️")

            if transcription_model.startswith('whisper-') and transcription_model != 'whisper-api':
                model_name = transcription_model.split('-')[1]
                whisper_result = subprocess.run([
                    sys.executable, "-m", "whisper",
                    str(audio_path),
                    "--model", model_name,
                    "--language", "en",
                    "--output_dir", str(TRANSCRIPT_DIR)
                ], check=True, capture_output=True, text=True)
                _write_log(video_name, f"whisper-{model_name}", whisper_result.stdout, whisper_result.stderr)
            elif transcription_model == 'whisper-api':
                client = openai.OpenAI()
                with open(audio_path, "rb") as audio_file:
                    transcript_response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                with open(transcript_path, "w") as f:
                    f.write(transcript_response.text)
            else:
                msg = f"Invalid transcription model selected: {transcription_model}"
                _emit(publish, "error", msg, "❌")
                raise ValueError(msg)

            transcript_exists = transcript_path.exists()
        else:
            _emit(publish, "update", f"Transcript found for {video_name}, skipping re-transcription. 📝", "🗂️")

        if not transcript_exists or transcript_path.stat().st_size == 0:
            msg = f"Transcription failed for {video_name}; no transcript was produced. ❌"
            _emit(publish, "error", msg, "❌")
            return False

        _emit(publish, "update", f"Audio transcribed: {transcript_path.name} - Phew, that was a lot of words! 📝", "✅")

        _emit(publish, "update", f"Summarizing transcript for {video_name}... Our AI is brewing some wisdom! 🧠", "✨")
        try:
            summarize_transcript(transcript_path, video_name)
        except SummarizationError as err:
            msg = f"Summarization failed for {video_name}: {err}"
            _emit(publish, "error", msg, "❌")
            job_store.record_failure(job_id, msg)
            return False

        _emit(publish, "update", f"Summary created for {video_name}. - Ta-da! Your insights are ready! 🌟", "✅")
        _emit(publish, "complete", (
            "Completed! "
            f"<a href='/summaries/{summary_path.name}' target='_blank'>Download Summary</a> | "
            f"<a href='/transcripts/{transcript_path.name}' target='_blank'>Download Transcript</a> - Mission accomplished! 🚀"
        ), "🎉")
        job_store.record_success(job_id, summary_path)
        return True

    except subprocess.CalledProcessError as exc:
        msg = (
            "Uh oh! A tool ran into trouble! 🛠️\n"
            f"Command: {exc.cmd}\nReturn Code: {exc.returncode}\nStdout: {exc.stdout}\nStderr: {exc.stderr} 💥"
        )
        _emit(publish, "error", msg, "❌")
        job_store.record_failure(job_id, msg)
        return False
    except Exception as exc:  # pragma: no cover - defensive
        _emit(publish, "error", f"An unexpected error occurred: {exc}", "❌")
        job_store.record_failure(job_id, str(exc))
        return False
