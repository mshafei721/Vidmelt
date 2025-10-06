# Vidmelt Feature & Enhancement Plan

## Branch Context
- Working branch: plan/roadmap
- Source branch: main
- Goal: capture prioritized backlog and delivery plan for roadmap items identified in the recent audit.

## Planning Assumptions
- Target platform: Linux/WSL with limited GPU access for local mode.
- All work stays offline unless explicitly within the Vercel deployment track.
- Redis requirement should become optional but remains the baseline until the Redis-less transport is delivered.

## Phase Breakdown

### Phase 1 – Stabilize & Unblock (Week 1-2)
1. **Transcript Cache Guard & SSE Skip (Quick Win)**
   - Reinstate transcript existence check before calling Whisper.
   - Emit "skip" SSE when cached transcript is reused.
   - Add failure branch if Whisper does not create the file.
2. **Vidmelt Doctor CLI (Quick Win)**
   - Implement the command "python -m vidmelt.doctor" to verify FFmpeg, Redis connectivity, Whisper import (NumPy <= 2.2), and API key presence.
   - Document the doctor command inside the README onboarding checklist.
3. **Transcript Download & Error Surfacing UI (Quick Win)**
   - Surface transcript download link alongside summary.
   - Propagate summarization errors to SSE without success banner.
4. **Dependency Hygiene & Secret Remediation**
   - Purge .env secret from history, rotate exposed API key.
   - Pin redis, openai-whisper (or alternative), and compatible numpy/numba versions in requirements.txt or constraints file.
5. **Transcription Provider Discovery (Discovery Spike)**
   - Evaluate higher-accuracy or faster STT options (e.g., AssemblyAI, Deepgram, Google STT, faster-whisper).
   - Compare accuracy, latency, cost, and offline viability.
   - Produce recommendation memo with integration considerations.

### Phase 2 – Operability & Automation (Week 3-6)
1. **Batch CLI (vidmelt batch) (Core Enhancement)**
   - Provide headless batch processing with dry-run and resume options.
   - Extract pipeline logic into reusable service module.
   - Add pytest coverage for argument parsing and cached transcript behaviour.
2. **Redis-less Event Channel (Core Enhancement)**
   - Introduce in-process SSE/long-poll transport with feature flag.
   - Keep Redis optional for multi-session scaling.
3. **Observability & Testing**
   - Capture FFmpeg/Whisper stdout to log files for diagnostics.
   - Add smoke tests: FFmpeg conversion, mock transcription job, summarizer error path.
4. **TikTok Video Link Ingestion (Core Enhancement)**
   - Integrate yt-dlp or TikTok-specific extractors to accept video URLs.
   - Add background download step with progress SSE and retry strategy.
   - Extend doctor CLI to verify yt-dlp availability where relevant.

### Phase 3 – Cloud & Workflow Intelligence (Week 7-12)
1. **Job History & Resume Hub (Core Enhancement)**
   - Persist job metadata in SQLite (status, timestamps, model, errors).
   - Provide /jobs web view and CLI commands to list/retry jobs.
2. **Vercel Deployment Strategy (Strategic Bet)**
   - Design architecture for serverless deployment (decide on serverless functions vs. Vercel Edge with background worker).
   - Externalize storage to S3-compatible bucket or Vercel Blob, and replace local disk dependencies.
   - Replace Redis with managed queue or durable event channel.
   - Produce deployment guide and IaC template.
3. **Offline Summarization Stack (Strategic Bet)**
   - Evaluate faster-whisper and local summarization model alternatives.
   - Implement configuration toggle, model download helper, and benchmark accuracy/performance.
4. **Transcript Knowledge Base & Search (Strategic Bet)**
   - Index transcripts/summaries into SQLite FTS or embeddings table.
   - Provide search UI and export endpoints.

## Milestones & Dependencies
- **M0 (End Week 2):** All Quick Wins + dependency cleanup merged; doctor CLI green; STT recommendation memo delivered.
- **M1 (End Week 6):** Batch CLI usable in CI; Redis-less mode behind config; TikTok ingestion live; observability tests passing.
- **M2 (End Week 12):** Job history feature in production; Vercel deployment plan validated with prototype; offline summarization MVP behind feature flag; search design review ready.

## Risks & Mitigations
- **NumPy/Whisper compatibility:** Lock versions and document doctor CLI usage.
- **Redis removal complexity:** Ship with toggle; fall back to Redis until confidence high.
- **Alternative STT vendor lock-in:** Keep abstraction layer for transcription providers; support fallback to Whisper.
- **Vercel serverless constraints:** Use containerized background worker or hybrid architecture for FFmpeg; ensure timeouts and storage limits are respected.
- **Offline model size:** Provide optional download step and storage guidance; allow partial adoption.
- **Data privacy for knowledge base:** Keep indices on local disk or encrypted storage; clarify retention settings.

## Next Actions
1. Share roadmap with stakeholders for validation.
2. Create tickets per item (Quick Wins first).
3. Schedule dependency cleanup, secret remediation, and STT evaluation spike immediately.
