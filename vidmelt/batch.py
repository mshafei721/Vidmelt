"""Batch processing CLI for Vidmelt."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence

from . import pipeline, history


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch process videos with Vidmelt")
    parser.add_argument(
        "input_dir",
        nargs="?",
        default=str(pipeline.UPLOAD_FOLDER),
        help="Directory to scan for .mp4 videos (defaults to the web upload folder)",
    )
    parser.add_argument(
        "--model",
        default="whisper-base",
        choices=["whisper-base", "whisper-medium", "whisper-large", "whisper-api"],
        help="Transcription backend to use",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List the videos that would be processed without running the pipeline",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Retry failed or in-progress jobs recorded in the history store",
    )
    return parser.parse_args(argv)


def _iter_videos(input_dir: Path) -> Iterable[Path]:
    return sorted(path for path in input_dir.glob("*.mp4"))


def batch_process(args: argparse.Namespace | None = None) -> int:
    ns = args or parse_args()
    input_dir = Path(ns.input_dir).expanduser().resolve()

    if not input_dir.exists():
        print(f"Input directory {input_dir} does not exist")
        return 2

    if ns.resume:
        from . import history

        jobs = list(history.GLOBAL_STORE.retryable_jobs())
        videos = [(Path(job.video_path), job.id, job.model) for job in jobs]
        print(f"Discovered {len(videos)} job(s) to resume")
    else:
        videos = [(video, None, ns.model) for video in _iter_videos(input_dir)]
        print(f"Discovered {len(videos)} video(s) in {input_dir}")

    if ns.dry_run:
        for video, job_id, model in videos:
            label = f"{video}"
            if job_id is not None:
                label += f" (job #{job_id})"
            print(f"[DRY RUN] {label}")
        return 0

    for video, job_id, model in videos:
        summary_path = pipeline.SUMMARY_DIR / f"{video.stem}.md"
        if summary_path.exists() and job_id is None:
            print(f"Skipping {video} (summary already exists)")
            continue

        selected_model = model if job_id is not None else ns.model
        print(f"Processing {video} with model {selected_model}")
        pipeline.process_video(video, selected_model, publish=None, job_id=job_id)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(batch_process())
