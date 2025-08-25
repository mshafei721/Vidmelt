# Repository Guidelines

## Project Structure & Module Organization
- `app.py`: Flask app, routes (`/`, `/upload`, `/summaries/<file>`), SSE.
- `summarize.py`: GPT summarization utility called by `app.py`.
- `templates/`: HTML templates (`index.html`).
- `videos/`, `audio_files/`, `transcripts/`, `summaries/`: runtime artifacts (`.gitkeep` in each).
- `requirements.txt`: Python deps. `.env.example`: config template.

## Build, Test, and Development Commands
- Create venv and install deps:
  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ```
- Start Redis (required for SSE):
  ```bash
  # macOS (brew): brew services start redis
  # Ubuntu: sudo systemctl start redis-server
  ```
- Run locally:
  ```bash
  python app.py
  # visit http://localhost:5000
  ```
- Manual smoke test: upload a small `.mp4` via UI; watch status in-page and check `summaries/<video>.md` is created.

## Coding Style & Naming Conventions
- Python 3.8+; follow PEP 8 with 4-space indentation.
- Filenames and functions: `snake_case` (e.g., `process_video_web`, `summarize_transcript`).
- Keep modules small and focused; shared helpers belong in new modules under root or `utils/` if added.
- Strings: prefer f-strings; add concise docstrings for public functions.
- Optional: run formatters locally (e.g., `black`, `isort`) before PRs.

## Testing Guidelines
- No formal test suite yet. PRs adding `pytest` are welcome.
- Suggested layout: `tests/test_*.py`; focus on
  - unit tests for `summarize_transcript` (mock OpenAI client), and
  - pipeline wrappers (FFmpeg/Whisper calls mocked via `subprocess.run`).
- Aim for meaningful coverage over I/O; avoid committing large media.

## Commit & Pull Request Guidelines
- Commits: clear, imperative subject. Conventional Commits encouraged, e.g.:
  - `feat: add whisper-api transcription option`
  - `fix: guard empty audio before transcription`
- PRs: include purpose, scope, manual test steps, and screenshots/GIFs for UI/SSE updates. Link related issues. Note any config or migration changes.

## Security & Configuration Tips
- Copy `.env.example` to `.env`; never commit secrets. Required: `OPENAI_API_KEY`.
- Ensure `ffmpeg` and Redis are installed and running.
- Large media files should remain in `videos/` only; avoid committing real data.

## Architecture Overview
- Pipeline: upload `.mp4` → extract audio (FFmpeg) → transcribe (local Whisper or `whisper-1`) → summarize (GPT) → stream progress via SSE → write Markdown to `summaries/`.
