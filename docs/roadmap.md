# Roadmap

Stages run in order (D-022). Each has a done-when that can be checked. After the MVP stages, the
post-MVP features from [spec.md](spec.md) follow in any order.

| Stage | What | Done when |
|---|---|---|
| 0 | Measurements | A table of recognition quality and speed (GPU and CPU, large-v3 and turbo, Russian, English and mixed speech, fast speech, pauses, similar voices) and of video size and GPU load per frame rate; a working way to find the source a call app is linked to; the open questions `stt-engine`, `mixed-language`, `video-fps`, `mic-link` closed |
| 1 | Server on the PC, file upload, import | An old call from `~/Videos` uploaded as a file gives a call record with a transcript, owner labelled, speakers separated, summary and action items in the chosen template; no hallucinated text on silence; import runs over the recordings the owner keeps |
| 2 | Daemon and extension | Calls in AyuGram/Telegram Desktop and in a browser prompt by themselves, record two tracks and the call monitor, upload chunks during the call, and no call is lost in two weeks of daily use, offline periods included |
| 3 | Web and sharing | The call page opens on a phone, the player jumps to timecodes and shows speakers, search finds the right call, deleting a call or a fragment works, and a guest sees only what the link allows |
| 4 | MCP and bedrock link | claude.ai and Claude Code answer "what did we decide about X last week" with timecodes and a link, reversible edits work, and a call can be handed to the bedrock call archive |
| 5 | VPS and backups | The server runs on the VPS, the daemon points to it, the PC no longer runs models, and a monthly encrypted backup is restored once as a test |
| 6+ | Post-MVP | Features from the spec's "soon" and "later" lists, one block each |

A stage starts only when the open questions it needs are decided ([open-questions.md](open-questions.md)).
