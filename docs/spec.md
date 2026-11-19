# earshot — specification

Status: accepted 2026-11-19. This is the working specification; it folds the owner's original
brief (Russian, kept privately) together with every decision taken during intake. Decisions are
recorded with their reasons in [decisions.md](decisions.md); stages and their done-when are in
[roadmap.md](roadmap.md); interfaces are in [contract.md](contract.md).

## Goal

earshot offers to record every call the moment it starts. Shortly after the call ends, a web
page is ready with a summary, action items, a transcript with a player, and a link to share. The
whole archive is searchable on the web and through Claude (MCP).

| Pain today | How earshot answers it |
|---|---|
| Forgetting to start recording | Recording is offered as soon as a call app holds the microphone |
| 20–60 minutes from call end to text | Speech is transcribed chunk by chunk while the call goes on |
| RAM, swap and VRAM full, OOM kills | Models run one at a time in a separate worker process; on the VPS the PC only records |
| 1 GB per hour and piles of intermediate files | Audio in Opus, video at a low frame rate, intermediates deleted |
| Hallucinations, "which speaker am I" | VAD before Whisper, separate tracks: the microphone track is always the owner |
| No search, no history | Web archive with full-text search, MCP for Claude |

Quality of the result matters more than speed. There is no hard deadline for the page; it should
simply be ready as soon as the pipeline allows.

## Users

- **Owner**: the only account. Records, reads, edits, shares.
- **Guest**: anyone holding a share link. Sees only what the link allows.

No other accounts, no teams.

## Where things run

- The PC (GNOME on Wayland, PipeWire, GTX 1060 6 GB, 16 GB RAM) records.
- The server is one program that runs either on the PC or on a VPS. It runs on the PC during
  development and until a VPS exists; moving it is a change of one URL in the daemon config.
- Speech recognition and the language model run locally by default (GPU on the PC, CPU on the
  VPS). Cloud engines can be plugged in through configuration; none is required.

## Components

### 1. GNOME Shell extension

- Panel indicator with three states: idle, recording, processing.
- On a new call: a notification "Record this call in <app>?" with **Record** and **Not now**, and
  a reminder to tell the other side. No answer within 60 s means no recording.
- The notification offers "always for this chat" and "never for this chat"; the choice is
  remembered per app and window title.
- Quick Settings: manual start and stop, link to the last call.
- Reports the focused window (app id, cleaned title, monitor connector) to the daemon over D-Bus.
  On Wayland only the shell knows window titles, so call detection depends on this report.
- Holds no recording logic. If gnome-shell crashes, a recording in progress continues.
- Supports GNOME Shell 45–51.

### 2. earshot-daemon (Rust, systemd user service)

Detection:

- Watches PipeWire. A call starts when an app from the allow list holds a microphone stream for
  more than 10 s. The default allow list is broad: Telegram Desktop and its forks (AyuGram), Zoom,
  Discord, Slack, Teams, all common browsers, and more.
- Browsers: any microphone hold over 10 s triggers the prompt; the window title is used only for
  metadata. This rule is experimental and will be revisited after real use.
- A call ends when the microphone has been released for 30 s. A new hold inside those 30 s
  continues the same call. A call in another app is a separate call.

Recording:

- Two tracks: the microphone **that the call app's stream is linked to** (not the system default,
  which on the owner's PC is a webcam) and the monitor of the default output.
- From the moment of detection both tracks go into an in-memory ring buffer. On **Record** the
  recording starts from the beginning of the buffer; on **Not now** or timeout the buffer is
  discarded without touching disk or network.
- Manual start records the default output monitor and the default microphone.
- If either track is silent for 30 s after start, the owner gets a notification.
- Both tracks are written locally as Ogg Opus, mono, 24–32 kbps. These local files are the
  source of truth.
- Video: gpu-screen-recorder as a separate process, capturing the monitor that holds the call
  window through KMS (no portal dialog), HEVC on NVENC, 5 fps by default. The frame rate is a
  setting; stage 0 measures 1, 5, 10, 24 and 60 fps.

Upload:

- Silero VAD cuts each track into chunks of 20–30 s on speech boundaries; each chunk is uploaded
  as soon as it closes, keyed by (call, track, sequence number), so a retry never duplicates.
- After the call, the full tracks are uploaded and the server reconciles them with the chunks.
  Video is uploaded after the call and never delays the page.
- Without network, data waits in a local queue and is sent later. The queue warns when it grows
  but never deletes. No call is ever lost.
- Metadata: app, window title cleaned of invisible Unicode characters, start time, duration.
- The local copy is deleted a few days (default 4, configurable) after the server confirms it.

### 3. Server: processing

- Accepts chunks over HTTPS with the daemon's token.
- Transcribes each chunk as it arrives. The engine sits behind one interface and is chosen in
  config: faster-whisper (CUDA int8 on the PC, CPU on the VPS) by default; cloud engines optional.
- Language is detected per chunk and per track (Russian, English, accents).
- Hallucination guards: VAD, `condition_on_previous_text=False`, word timestamps, a stop list of
  known phrases ("Субтитры сделал…", "Продолжение следует…" and similar).
- Speaker separation: everything on the microphone track is the owner. On the system track a
  voice print is computed per chunk during the call; after the call the prints are clustered,
  so diarization adds seconds, not minutes. A single remote speaker needs no clustering at all.
- Echo: when the owner uses speakers instead of headphones, the system track is the reference
  signal and the echo is removed from the microphone track on the server.
- ML work runs in a worker process separate from the API, one model at a time, with a free-VRAM
  check before loading, so an out-of-memory abort kills only the worker.
- One language-model pass after the call: punctuation, merging of turns, `[inaudible]` marks,
  call title, summary, key points, action items (owner, due date, timecode).
- Summary templates: Auto, Client call, Scoping, Interview (owner as candidate), Work sync, 1:1,
  Therapy (topics and homework, no action items). The template is chosen by hand and remembered
  per chat; switching it regenerates the summary from the same transcript.
- Summary language: Russian by default; regenerate in English (or back) on demand.
- The language model goes through earshot's own router with three wire dialects: Anthropic,
  OpenAI-compatible (Ollama, OpenRouter, Groq, LM Studio, vLLM and others) and Gemini. Local
  models during development.
- Stored: audio in Opus, video, segments and the final transcript. Intermediate files are
  deleted. Video is kept 30 days, then only audio (recompressed to the smallest acceptable
  size) and text remain.

### 4. Web

- Call list and search across the whole archive (SQLite FTS5 with the trigram tokenizer so
  Russian works).
- Call page: tabs AI Notes and Transcript, action items with checkboxes, clickable timecodes.
- Audio player with a waveform coloured by speaker; video player when video exists.
- Rename speakers and the call. Delete a call; delete a fragment (cut from audio, video, text,
  and regenerate the summary).
- Share links: random unguessable token, revocable, lifetime (default 7 days), toggles for what
  the guest sees: summary, transcript, audio, video. Video is off by default.
- The admin side is behind a password and a session; only share pages are public.
- Design at Krisp's level: dark theme only, the same structure, its own style, no Krisp brand.
  Reads well on a phone. Built with the design-creator workflow.
- No chat on the call page: Claude through MCP covers it.

### 5. MCP server

- Runs in the server process (FastMCP, streamable HTTP).
- Read tools: `search_calls`, `get_call`, `get_transcript`, `open_action_items`.
- Write tools, reversible only: close or reopen an action item, rename a call or a speaker, set
  tags or the project link, regenerate a summary with another template or language. Deleting,
  creating share links and changing settings are web-only.
- Claude Code reaches it on localhost. claude.ai reaches it through Tailscale Funnel on its own
  port with a secret path, the same way the owner's other MCP servers are exposed.
- earshot can hand transcripts to the bedrock knowledge base (the `call` skill), and a call can
  be linked to a project so project questions find what was decided on calls.

### 6. Import of old recordings

- Implemented on top of the server's file upload: a script walks `~/Videos`, finds GPU Screen
  Recorder mp4 files with their existing transcripts and uploads them.
- Old recordings have one mixed track, so they get ordinary diarization; the owner is identified
  by a voice sample taken from new recordings.
- Existing cleaned transcripts are reused as text; summaries are generated fresh.
- Originals and intermediates are deleted only after the owner confirms, and only the recordings
  the owner chooses to keep are imported.

## Not doing

- A browser extension: PipeWire plus the window title already catch web calls.
- A bot that joins the call.
- A live transcript on screen during the call.
- Accounts for other people or teams: share links only.
- A mobile app: the web works on a phone.
- Training or fine-tuning models.
- Calendar integration (may come back later).
- Anything with Telegram as a delivery channel.

## After the MVP — soon

Each is an extension of the pipeline or the web, in any order after stage 3.

| Feature | What it does |
|---|---|
| Own vocabulary | Names and terms recognised correctly: a list in settings feeds the recogniser prompt and the language-model pass; new words are suggested from corrections |
| Shared action-item list | All open items from all calls on one page, the owner's and others' apart; status changes from the web and MCP |
| Tags, folders, client page | All calls with one client or on one project in order; the model proposes tags, the owner corrects |
| Listen later | Speed-up and silence skipping using the VAD marks |
| Talk time | "You spoke 62%", longest monologue, from the VAD marks of both tracks |
| Follow-up draft | A message to the client with the results, in the right tone and language |

## After the MVP — later

| Feature | What it does |
|---|---|
| Pre-call briefing | The "Record?" notification links to what was promised to this client last time and what is still open |
| Moment marker | A hotkey drops a bookmark; the model gives it extra attention, the player highlights it |
| Voice memory | Regular contacts are named instead of "Speaker 2"; rename once and the voice is remembered |
| Clips | A fragment of a call (audio, video, text) behind its own share link |
| Periodic reports | Weekly: promised, done, still open (delivery channel to be decided) |
| Topic tracking | Every mention of rates, deadlines, payment or chosen topics across the archive |
| Live noise suppression | A virtual microphone through a PipeWire filter chain (DeepFilterNet or RNNoise), toggled in Quick Settings |

## Security

- HTTPS, a token for the daemon, password and session for the admin side, API keys only in the
  environment, an encrypted monthly backup of the archive.
- Share tokens cannot be guessed, can be revoked, and do not show video unless allowed.
- Logs never contain transcript text, only identifiers and durations.
- The repository is public: recordings, voice samples and personal configuration live only in the
  gitignored `private/` folder; tests and CI use synthetic data.
