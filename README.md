# earshot

Call recording for GNOME on Wayland that you do not have to remember. When a call app takes the
microphone, earshot asks whether to record. Shortly after the call a web page is ready: summary,
action items, a transcript with speakers and a player, and a link to share. The archive is
searchable on the web and from Claude through MCP.

[Русская версия](README.ru.md)

## Status

Early development. The repository holds the specification, the decisions, the rules and the
skeletons of the daemon and the server; nothing records yet. Next comes stage 0: measuring speech
recognition and video settings on real hardware. See [docs/roadmap.md](docs/roadmap.md).

## How it works

- **earshot-daemon** (Rust) watches PipeWire. When an app such as Telegram Desktop, Zoom, Discord,
  Slack or a browser holds the microphone, it asks through the GNOME extension. On yes it records
  two tracks, your microphone and everyone else, plus the monitor with the call window.
- **The GNOME Shell extension** shows the prompt, the panel indicator and Quick Settings. It never
  records; a gnome-shell crash does not stop a recording.
- **earshot-server** (Python) transcribes the call in chunks while it goes on, separates speakers,
  and writes the summary with a local or a configured language model. It runs on your PC or on a
  small VPS, and serves the web and the MCP endpoint.

Details: [docs/spec.md](docs/spec.md), [docs/architecture.md](docs/architecture.md).

## Requirements (target)

GNOME Shell 45–51 on Wayland, PipeWire, an NVIDIA GPU for local recognition on the PC (CPU works on
a VPS), gpu-screen-recorder for video.

## Recording other people

Laws on recording conversations differ: some places need the consent of everyone on the call.
earshot asks before every recording and reminds you to tell the other side; telling them is your
responsibility.

## Repository

| Path | What |
|---|---|
| `daemon/` | the Rust daemon |
| `server/` | the Python server |
| `tools/checks/` | repository guards |
| `docs/` | specification, decisions, architecture, contract, roadmap |
| `plugins/bedrock/` | the bundled [bedrock](https://github.com/paranoica/bedrock) plugin for Claude Code, used to develop earshot; with it the repository's working rules apply without installing anything |

## Development

```
cargo test --workspace                       # daemon
cd server && uv run pytest                   # server
cd tools/checks && uvx pytest                # repository guards
git config core.hooksPath .githooks          # pre-commit checks
```

Working rules for people and agents: [AGENTS.md](AGENTS.md). Security reports:
[SECURITY.md](SECURITY.md).

## Licence

Dual-licensed under [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE), at your option.
