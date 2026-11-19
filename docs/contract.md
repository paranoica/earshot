# Contract

The interfaces between the daemon, the extension, the server and its clients. Status: **draft**.
Parts marked *implemented* are fixed; the rest is the target shape and may change only together
with a decision in [decisions.md](decisions.md).

## Common rules

- Identifiers: a call id is a UUIDv7 created by the daemon (or by the server for uploaded files).
  Tracks are `mic` and `system`. Chunk sequence numbers start at 0 per track.
- Times: milliseconds from the start of the call as integers; wall-clock times in RFC 3339 UTC.
- JSON keys are snake_case. `null` means unknown; `0` means measured zero.
- Text that is shown to people is never built from free-form error strings: errors carry a code.

## HTTP API v1

Base path `/api/v1`. JSON unless stated otherwise.

### Errors (*implemented*)

Every error answers with the HTTP status and:

```json
{"error": {"code": "not_found", "message": "Not Found"}}
```

Codes so far: `not_found` (404), `method_not_allowed` (405), `http_error` (any other HTTP
error). The set is closed: a new code is added here first. Messages are for logs and developers,
not for display.

### Health (*implemented*)

`GET /api/v1/health` → `200 {"status": "ok"}`. No authentication.

### Daemon ingest (draft)

Authentication: `Authorization: Bearer <daemon token>`.

| Method and path | Body | Answer | Notes |
|---|---|---|---|
| `PUT /calls/{call_id}` | `{app, window_title, started_at, source: "daemon"}` | `200` call | Idempotent: repeating it with the same body is a no-op |
| `PUT /calls/{call_id}/tracks/{track}/chunks/{seq}` | Ogg Opus bytes; headers `X-Start-Ms`, `X-Duration-Ms` | `201` new, `200` already stored | Same key and same bytes: no-op; same key, other bytes: `409 chunk_conflict` |
| `POST /calls/{call_id}/end` | `{ended_at, chunk_counts: {mic, system}}` | `202` | Starts reconcile once the full tracks arrive |
| `PUT /calls/{call_id}/tracks/{track}` | full Ogg Opus file | `201`/`200` | The full track wins over chunks during reconcile |
| `PUT /calls/{call_id}/video` | MP4 bytes | `201`/`200` | Never blocks the page |
| `GET /calls/{call_id}/receipt` | — | `{tracks: {mic, system}, video}` with byte counts and hashes | The daemon deletes its local copy only after a matching receipt |

### Upload (draft)

`POST /uploads` (owner session or daemon token), multipart with one audio or video file and an
optional existing transcript → `202 {call_id}`. Used by the web and by the importer.

### Web and share API

Defined in stage 3 and generated as OpenAPI from the code; the web client is generated from it.

## D-Bus: `io.github.paranoica.Earshot1` (draft)

Bus: session. Name and object path: `io.github.paranoica.Earshot` at `/io/github/paranoica/Earshot`.
Interface `io.github.paranoica.Earshot1`, owned by the daemon.

| Kind | Member | Signature | Meaning |
|---|---|---|---|
| property | `State` | `s` | `idle`, `prompting`, `recording`, `processing` |
| property | `LastCallUrl` | `s` | web URL of the last finished call, empty if none |
| signal | `PromptRequested` | `(s prompt_id, s app, s window_title)` | ask the owner |
| signal | `PromptClosed` | `(s prompt_id)` | the prompt timed out or the call ended |
| signal | `Warning` | `(s code, s detail)` | e.g. `track_silent` |
| method | `AnswerPrompt` | `(s prompt_id, s answer, s remember) → ()` | answer `record`/`skip`; remember `none`/`always`/`never` |
| method | `StartManual` | `() → (s call_id)` | manual recording |
| method | `Stop` | `() → ()` | stop the current recording |
| method | `ReportWindow` | `(s app_id, s title, s monitor_connector) → ()` | the extension reports the focused window on every focus change; the daemon keeps the last report per app and uses it for the prompt text and the video monitor |

The extension never records and never holds call state; if gnome-shell restarts, it reads
`State` again and resubscribes.

## Chunk format

- Ogg Opus, mono, 48 kHz internal (Opus native), 24 kbps for speech; the server decodes to 16 kHz
  for recognition.
- One chunk is 20–30 s, cut at a VAD speech boundary; a chunk never splits a word on purpose.
  Silence longer than a chunk produces no chunk; the gap is visible from `X-Start-Ms`.
- The full track is the same stream from start to end; chunks are views of it.

## MCP tools (draft)

| Tool | Kind | Arguments → result |
|---|---|---|
| `search_calls` | read | `query, since?, until?, limit?` → calls with snippets and links |
| `get_call` | read | `call_id` → metadata, summary, action items, link |
| `get_transcript` | read | `call_id, from_ms?, to_ms?` → segments with speakers and timecodes |
| `open_action_items` | read | `owner?: me/others` → open items with call links and timecodes |
| `set_action_item` | write | `item_id, done` |
| `rename` | write | `call_id, title?` or `call_id, speaker, name` |
| `set_tags` | write | `call_id, tags, project?` |
| `regenerate_summary` | write | `call_id, template?, language?` → new summary version; the old one is kept |
