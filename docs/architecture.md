# Architecture

What runs where, how a call flows through it, and where each module lives. Interfaces between the
parts are specified in [contract.md](contract.md); the reasons are in [decisions.md](decisions.md).

## Parts

```
PC (GNOME Wayland, PipeWire, GTX 1060)
├─ extension (GJS, inside gnome-shell)
│    UI only: indicator, prompt, Quick Settings; reports the focused window to the daemon
├─ earshot-daemon (Rust, systemd --user)
│    detects calls, records two tracks into a ring buffer and local Ogg files,
│    cuts chunks with VAD, uploads them, drives gpu-screen-recorder
└─ earshot-server (Python) — on the PC now, on a VPS later (D-001)
     ├─ API process: FastAPI, uploads, web, share pages, MCP
     ├─ worker process: speech recognition, voice prints, echo removal, language model
     └─ SQLite (WAL) + files on disk
```

The daemon and the extension talk over the session D-Bus. The daemon and the server talk over
HTTPS with a bearer token. The web and MCP clients talk only to the server.

## A call, end to end

1. **Detect.** The daemon watches the PipeWire registry. An input stream from an allow-listed
   app (or any browser) that stays linked to a source for 10 s opens a candidate call. The daemon
   resolves which source node the stream is linked to and starts capturing that source and the
   default output monitor into an in-memory ring buffer (D-004, D-005).
2. **Ask.** The daemon emits a prompt signal; the extension shows the notification with the app
   name and the last reported window title. The answer comes back as a D-Bus call. No answer in
   60 s or Not now: the buffer is dropped.
3. **Record.** On Record the buffer becomes the start of two local Ogg Opus files in the spool.
   The daemon asks the extension which monitor holds the call window and starts
   gpu-screen-recorder on that connector (D-008). A track silent for 30 s raises a warning.
4. **Chunk and upload.** Silero VAD marks speech; each track is cut into chunks of 20–30 s at
   speech boundaries. Each closed chunk is put into the upload queue and sent with its key
   (call id, track, sequence) (D-006). Offline, the queue waits.
5. **Transcribe during the call.** The server stores each chunk, enqueues a job, and the worker
   transcribes it with word timestamps and per-chunk language detection. For the system track
   it also computes a voice print per chunk (D-007).
6. **End.** Thirty seconds after the microphone is released the daemon closes the call, uploads
   the full tracks and then the video. The server reconciles the full tracks against the chunks
   and fills any gap.
7. **Finish.** The worker clusters the voice prints, optionally removes echo, merges both tracks
   into one timeline, and runs one language-model pass for punctuation, title, summary, key
   points and action items with the call's template (D-014). The call page is ready.
8. **Clean up.** Intermediate files are deleted. The daemon deletes its local copy a few days
   after the server confirmed the full tracks. Video expires after 30 days.

## Server modules

`server/src/earshot/`, one folder per domain, each with `router`, `schemas`, `service`, `repo`.
Domains call each other only through `service`. No `utils`, `helpers` or `common`.

| Module | Owns |
|---|---|
| `ingest` | daemon API: calls, chunks, full tracks, video; file upload; idempotency and reconcile |
| `calls` | call records, metadata, renames, deletion, fragment cuts |
| `transcripts` | segments, speakers, the merged timeline |
| `summaries` | templates, summary versions, action items |
| `search` | FTS5 index and queries |
| `share` | share links, guest views |
| `auth` | owner password, sessions, daemon token |
| `jobs` | the job table, claiming, retries |
| `mcp` | FastMCP tools over the services above |
| `engines` | `Transcriber`, voice prints, echo removal, the language-model router (D-009, D-010) |
| `worker` | the worker process loop: claim a job, load the needed engine, run, release |
| `importer` | the `~/Videos` import on top of `ingest` |

## Daemon modules

`daemon/src/`: `detect` (PipeWire registry, stream-to-source links), `capture` (ring buffer, two
tracks), `encode` (Opus, Ogg), `vad` (Silero via sherpa-onnx), `spool` (local files and the
upload queue), `upload` (HTTP client, retries), `video` (gpu-screen-recorder process), `dbus`
(the `io.github.paranoica.Earshot1` interface), `config`.

## Extension modules

`extension/earshot@paranoica/`: `extension.js` (enable/disable, wiring), `indicator.js`,
`prompt.js`, `quickSettings.js`, `windows.js` (focused window and its monitor connector),
`dbus.js` (proxy to the daemon). Logic that can be tested without gnome-shell lives in plain
modules with GJS unit tests.

## Storage

On the PC (daemon spool), under `$XDG_DATA_HOME/earshot/spool/<call-id>/`: `mic.ogg`,
`system.ogg`, `video.mp4`, `chunks/`, `state.json`.

On the server, under the data directory: `earshot.db` (SQLite), `calls/<call-id>/` with
`mic.opus`, `system.opus`, `video.mp4` (until expiry), `segments.json`; nothing else is kept.

## Deployment

| Phase | Server runs as | Reached by |
|---|---|---|
| PC | systemd user service next to the daemon, `127.0.0.1` | daemon and Claude Code on localhost; claude.ai and share links through Tailscale Funnel |
| VPS | systemd service behind Caddy (HTTPS) | daemon over HTTPS; web and share links on the VPS's domain; MCP as on the PC |

Backups: monthly, encrypted with age, kept on the same VPS (owner's choice).

## Repository layout

| Path | What |
|---|---|
| `daemon/` | Rust crate `earshot-daemon` (workspace member) |
| `extension/` | GNOME Shell extension (created in stage 2) |
| `server/` | Python project `earshot-server` |
| `web/` | SvelteKit app (created in stage 3) |
| `tools/checks/` | repository guards run by the pre-commit hook and CI |
| `spikes/` | measurements and throwaway experiments; results gitignored |
| `packaging/` | systemd units, install script, later the AUR package |
| `docs/` | this documentation |
| `private/` | owner-only material, gitignored |
| `plugins/`, `.claude-plugin/`, `tests/`, `bench/`, root `pyproject.toml` | the bundled bedrock template (D-016) |
