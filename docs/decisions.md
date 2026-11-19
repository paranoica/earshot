# Decisions

Each decision has an anchor, a code, a date and who decided. A changed decision is not edited in
place: a new decision supersedes it and says so. Implementation notes are appended as
"As built (Tnnn)". Open items live in [open-questions.md](open-questions.md).

<!-- @anchor decision:local-first -->
### D-001 — One server program, on the PC now and on a VPS later
Date: 2026-11-19 · Decided by: owner
- Context: the VPS is not chosen yet and will come last; the owner still wants the result early.
- Decision: the server is a single program that runs unchanged on the PC or on a VPS. The daemon
  talks to `server_url`; moving the server is a change of that URL.
- Consequences: no PC-only shortcuts in the server; heavy models must fit the PC's GTX 1060 and a
  CPU-only VPS; share links work from the PC only while it is on and reachable.

<!-- @anchor decision:pc-records-server-processes -->
### D-002 — The PC records, the server processes; ML in a separate worker
Date: 2026-11-19 · Decided by: owner (process split), session (worker isolation)
- Context: the old pipeline filled RAM, swap and VRAM; whisper.cpp in the owner's other project
  aborted the whole process on out-of-memory.
- Decision: the daemon only detects, records and uploads. All speech, speaker and language-model
  work runs in a worker process apart from the API, one model at a time, with a free-VRAM check
  before loading.
- Consequences: a model crash ends only the worker; the API and the queue survive it.

<!-- @anchor decision:daemon-stack -->
### D-003 — Daemon in Rust on pipewire-rs, Opus, Silero via sherpa-onnx, zbus
Date: 2026-11-19 · Decided by: owner
- Context: the brief proposed GStreamer; the owner's live-meeting-assistant already captures the
  microphone and the output monitor through pipewire-rs on this machine and runs Silero through
  sherpa-onnx.
- Decision: reuse and adapt that capture and VAD code; encode with libopus into Ogg; D-Bus with
  zbus 5; tokio, tracing, anyhow in the binary and thiserror in libraries.
- Consequences: no GStreamer dependency. sherpa-onnx must be linked as a shared library (its
  static archives clash with other C++ code; recorded in the assistant's failure log).

<!-- @anchor decision:call-detection -->
### D-004 — Call detection by microphone hold; record the source the app is linked to
Date: 2026-11-19 · Decided by: owner
- Context: most of the owner's calls run in a browser, where PipeWire knows nothing about tabs;
  the system default microphone is a webcam, while calls use the fifine microphone.
- Decision: an allow-listed app holding a microphone stream over 10 s starts a call; browsers
  prompt on any hold (experimental). The daemon records the source node linked to the app's
  input stream. Release for 30 s ends the call; a re-hold inside 30 s continues it.
- Consequences: the extension must report window titles (Wayland hides them from the daemon);
  false prompts in browsers are accepted as cheap because nothing records without an answer.

<!-- @anchor decision:consent-prompt -->
### D-005 — Ask every time; pre-roll buffer in memory; per-chat memory
Date: 2026-11-19 · Decided by: owner
- Decision: a notification asks "Record this call in <app>?"; no answer in 60 s means no
  recording. From detection, audio is kept in an in-memory ring buffer; Record keeps it as the
  start of the recording, Not now or timeout discards it without touching disk or network. The
  prompt offers always/never for the chat.
- Consequences: the beginning of a call is not lost; declining leaves no trace.

<!-- @anchor decision:local-source-of-truth -->
### D-006 — Local Ogg files are the source of truth; idempotent chunk upload
Date: 2026-11-19 · Decided by: session
- Context: "no call is ever lost" must hold with flaky network and a server that restarts.
- Decision: both tracks are written locally first. Chunks are uploaded keyed by (call id, track,
  sequence); a repeated upload of the same key is a no-op. After the call the full tracks are
  uploaded and the server reconciles them with the chunks. The local copy is deleted a few days
  (default 4) after the server confirms the full tracks.
- Consequences: the server must accept out-of-order and repeated chunks; the queue grows
  without limit offline (it warns, never deletes).

<!-- @anchor decision:diarization -->
### D-007 — Speakers: the microphone track is the owner; voice prints on the fly
Date: 2026-11-19 · Decided by: session
- Decision: no diarization on the microphone track. On the system track a voice print is
  computed for each chunk during the call and clustered after it; with one remote speaker there
  is nothing to cluster. Old single-track recordings get full diarization and the owner is found
  by a voice sample from new recordings.
- Consequences: speaker work after the call takes seconds; the same prints later power voice
  memory.

<!-- @anchor decision:video -->
### D-008 — Video through gpu-screen-recorder, KMS capture of the call's monitor
Date: 2026-11-19 · Decided by: owner
- Context: the owner has two identical monitors that the screen-cast portal cannot tell apart;
  gpu-screen-recorder 6.1.7 is installed with `cap_sys_admin` on its KMS helper.
- Decision: record the monitor that holds the call window, by connector name, through KMS, HEVC
  on NVENC, 5 fps by default. The frame rate is a setting and stage 0 measures 1/5/10/24/60.
  Video is kept 30 days.
- Consequences: no portal dialog; other windows on that monitor are in the frame, so share links
  hide video by default.

<!-- @anchor decision:stt-engine -->
### D-009 — Speech recognition behind one interface; faster-whisper by default
Date: 2026-11-19 · Decided by: owner (local, free), final engine after stage 0
- Context: the old pipeline ran faster-whisper large-v3 int8 on the GTX 1060 at about three times
  real time; the budget is at most 10 USD a month, ideally the VPS only.
- Decision: a `Transcriber` interface with faster-whisper (CUDA int8 on the PC, CPU on the VPS)
  as the default; cloud engines may be added behind the same interface. Language is detected per
  chunk and track.
- Consequences: the model and settings are fixed by the stage 0 measurements.

<!-- @anchor decision:llm-router -->
### D-010 — Own language-model router with three wire dialects; local by default
Date: 2026-11-19 · Decided by: owner
- Decision: a thin router speaking Anthropic, OpenAI-compatible and Gemini APIs, as in the
  owner's live-meeting-assistant. Local models (Ollama) during development; a cloud model may be
  configured on the VPS.
- Consequences: no LiteLLM dependency; adding a provider is a config entry when it speaks one of
  the three dialects.

<!-- @anchor decision:storage -->
### D-011 — SQLite with SQLAlchemy Core and Alembic; FTS5 trigram search
Date: 2026-11-19 · Decided by: session
- Context: one user, a few calls a week; the API and the worker are separate processes.
- Decision: SQLite in WAL mode with a busy timeout; SQLAlchemy 2 Core (no ORM) for typed
  queries; Alembic migrations, each with a tested downgrade; full-text search through FTS5 with
  the trigram tokenizer, written as bound-parameter SQL. The job queue is a table claimed with
  `UPDATE … RETURNING`.
- Consequences: no database server; backups are a file copy taken through SQLite's backup API.

<!-- @anchor decision:web -->
### D-012 — SvelteKit static web served by the server; dark Krisp-level design
Date: 2026-11-19 · Decided by: owner
- Decision: SvelteKit built to static files and served by FastAPI; TypeScript strict;
  wavesurfer.js for the player; the client is generated from the server's OpenAPI. Design via
  the design-creator workflow, dark theme only, phone-friendly.
- Consequences: one process on the server; no Node at runtime.

<!-- @anchor decision:mcp -->
### D-013 — MCP inside the server; Funnel with a secret path for claude.ai; reversible writes
Date: 2026-11-19 · Decided by: owner
- Context: the owner's Telegram MCP is reached by Claude Code on localhost and by claude.ai
  through Tailscale Funnel with a secret path and no sign-in.
- Decision: FastMCP mounted in the server process. Claude Code uses localhost; claude.ai uses
  its own Funnel port (8443) with a secret path. Write tools change only reversible things;
  deleting, sharing and settings stay in the web.
- Consequences: whoever learns the URL can read the archive and make reversible edits; the
  Telegram setup's rotation script must stop resetting every Funnel route.

<!-- @anchor decision:templates -->
### D-014 — Summary templates chosen by hand; language switchable
Date: 2026-11-19 · Decided by: owner
- Decision: Auto, Client call, Scoping, Interview (owner as candidate), Work sync, 1:1, Therapy.
  Chosen by hand, remembered per chat, switching regenerates from the same transcript. Russian by
  default, English on demand. No automatic detection of call types.
- Consequences: templates are prompts plus a section schema; adding one needs no code change.

<!-- @anchor decision:licence -->
### D-015 — Licence MIT OR Apache-2.0
Date: 2026-11-19 · Decided by: owner
- Decision: dual licence, the Rust ecosystem convention. The bundled bedrock plugin keeps its
  own licence.
- Consequences: compatible with every dependency in the stack; GNOME Extensions accepts
  GPL-compatible terms, which MIT is.

<!-- @anchor decision:repo-layout -->
### D-016 — Monorepo; the bedrock template stays
Date: 2026-11-19 · Decided by: owner (template), session (layout)
- Decision: `daemon/` (Rust workspace member), `extension/` (GJS), `server/` (Python, includes
  MCP and import), `web/` (SvelteKit), `tools/checks/` (repo guards), `spikes/` (measurements),
  `packaging/`, `docs/`. The template's `plugins/`, `.claude-plugin/`, root `pyproject.toml`,
  `tests/` and `bench/` stay for anyone without the plugin.
- Consequences: earshot's measurements live in `spikes/`, not the template's `bench/`; each
  Python project carries its own lint config.

<!-- @anchor decision:process -->
### D-017 — Linear history on main; push after a green batch; three agents per task
Date: 2026-11-19 · Decided by: owner
- Decision: commits land on main, single line `type(scope): description`, no body, no trailers.
  An agent task works in its own worktree branch, is rebased and merged `--ff-only`. Push after
  every green batch without asking. For R2 and R3 tasks: a blind test author (spec only), an
  implementer (red test first, may not weaken tests), a verifier (default REJECT, mutations and
  attacks). R1 tasks get an implementer and a review. The backlog is bedrock's.
- Consequences: no merge commits; every finding of the verifier, LOW included, becomes a task.

<!-- @anchor decision:code-rules -->
### D-018 — Code rules
Date: 2026-11-19 · Decided by: owner (rules), session (tools)
- Decision: no comments and no docstrings in code (MCP tool descriptions excepted, they are
  runtime data). Files up to 400 lines with a ratchet (bedrock's check). Python: 3.12+, type
  hints, ruff, black at 100, mypy strict. Rust: edition 2024, rustfmt at 100, clippy with
  warnings as errors. TypeScript: strict with `noUncheckedIndexedAccess`, Biome. No
  `utils`/`helpers`/`common` modules. New dependencies need the owner's approval.
- Consequences: rules that a tool can check run in the pre-commit hook and CI; see AGENTS.md.

<!-- @anchor decision:public-repo-privacy -->
### D-019 — Public repository, private data stays out
Date: 2026-11-19 · Decided by: owner
- Decision: the repository is public. Recordings, voice samples, specs with personal detail and
  personal config live in the gitignored `private/`. Tests and CI use synthetic data only. A
  guard refuses audio and video files in git outside small synthetic fixtures.
- Consequences: no real voice in fixtures; quality benches run locally on private data. The
  guard reads the git index (paths and staged blob sizes), not the working tree, so a file staged
  and then deleted or truncated on disk is still caught. It judges by file name: a recording
  renamed to an unrelated extension passes; content sniffing is not done.

<!-- @anchor decision:no-telegram -->
### D-020 — No Telegram delivery
Date: 2026-11-19 · Decided by: owner
- Decision: features that sent results, reports or reminders to Telegram are dropped. Telegram
  stays only as a call app to detect and record.
- Consequences: periodic reports and reminders need another channel or are dropped (open).

<!-- @anchor decision:echo -->
### D-021 — Echo removed on the server with the system track as reference
Date: 2026-11-19 · Decided by: session
- Context: the owner wears headphones but wants an echo module ready.
- Decision: echo cancellation runs on the server using the system track as the reference signal,
  so the live audio path is untouched. A live virtual microphone with noise suppression is a
  post-MVP feature.
- Consequences: the echo module works on recordings only and is optional per call.

<!-- @anchor decision:stage-order -->
### D-022 — Stage order: measure, server, recording, web, MCP, VPS
Date: 2026-11-19 · Decided by: session, accepted by owner
- Decision: stage 0 measurements; stage 1 the server on the PC with file upload and import of
  old recordings; stage 2 daemon and extension; stage 3 web and sharing; stage 4 MCP and bedrock
  link; stage 5 VPS and backups; then post-MVP. See [roadmap.md](roadmap.md).
- Consequences: the pipeline is tested on real old calls before the daemon exists.

<!-- @anchor decision:backups -->
### D-023 — Monthly backup, encrypted with age, kept on the same VPS
Date: 2026-11-19 · Decided by: owner (frequency, place, encryption), session (age, key handling)
- Context: the original brief asks for an encrypted backup; during intake the owner chose a
  monthly backup on the same VPS and no encryption of the disk or of the live call archive.
- Decision: once a month the database (through SQLite's backup API) and the call files are packed
  into one backup file, encrypted with age to a key whose private half stays off the VPS, and kept
  on the VPS. The live call archive and the disk stay unencrypted.
- Consequences: a backup file copied off the VPS is unreadable without the owner's key; the backup
  does not protect against losing the VPS itself, which the owner accepted.
