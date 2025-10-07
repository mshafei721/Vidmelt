from pathlib import Path

from vidmelt import history


def test_job_store_success(tmp_path):
    db_path = tmp_path / "jobs.sqlite3"
    store = history.JobStore(db_path)

    video = Path("videos/demo.mp4")
    job_id = store.record_start(video, "whisper-base")
    store.record_success(job_id, Path("summaries/demo.md"))

    jobs = list(store.list_recent())
    assert len(jobs) == 1
    job = jobs[0]
    assert job.status == "complete"
    assert job.video_path.endswith("videos/demo.mp4")
    assert job.summary_path.endswith("summaries/demo.md")
    assert job.finished_at is not None


def test_job_store_failure(tmp_path):
    db_path = tmp_path / "jobs.sqlite3"
    store = history.JobStore(db_path)

    job_id = store.record_start(Path("videos/fail.mp4"), "whisper-api")
    store.record_failure(job_id, "boom")

    job = next(iter(store.list_recent()))
    assert job.status == "failed"
    assert job.error == "boom"
    assert job.finished_at is not None


def test_job_store_retry(tmp_path):
    db_path = tmp_path / "jobs.sqlite3"
    store = history.JobStore(db_path)

    job_id = store.record_start(Path("videos/demo.mp4"), "whisper-base")
    store.record_failure(job_id, "boom")

    store.record_retry(job_id)

    job = next(iter(store.list_recent()))
    assert job.status == "processing"
    assert job.error is None
    assert job.summary_path is None
    assert job.attempt_count == 2

    retry_jobs = list(store.retryable_jobs())
    assert retry_jobs and retry_jobs[0].id == job_id
