# Open questions

Questions that are known and deliberately not decided yet. Each is decided before the stage that
needs it; the decision then moves to [decisions.md](decisions.md). In code, an unresolved point
is marked `TODO(decision: <topic>)` and linked here.

| Topic | Question | Decided by | Needed before |
|---|---|---|---|
| stt-engine | Which model and settings: large-v3 or turbo, CUDA int8 on the PC, CPU threads on the VPS; is any cloud engine worth having as an option | stage 0 measurements | stage 1 |
| mixed-language | How well mixed Russian and English in one phrase is recognised; whether per-chunk language detection is enough | stage 0 measurements | stage 1 |
| video-fps | Frame rate and codec settings: 1, 5, 10, 24, 60 fps compared for size, GPU load and readability | stage 0 measurements | stage 2 |
| mic-link | How to resolve the source a call app's stream is linked to, for AyuGram/Telegram Desktop and Chrome | stage 0 spike | stage 2 |
| reference-text | What serves as the reference transcript for quality measurements (the owner's corrected fragments or the cleaned old transcripts) | owner | stage 0 |
| browser-rule | Whether prompting on every browser microphone hold is acceptable in daily use | owner, after two weeks of stage 2 | end of stage 2 |
| funnel | Port 8443 for earshot and a non-global reset in the Telegram MCP's rotation script | session | stage 4 |
| mcp-writes | Whether the reversible write tools are enough or too much for the no-sign-in claude.ai access | owner, after use | end of stage 4 |
| cloud-llm | Whether to configure a cloud language model on the VPS, and which | owner | stage 5 |
| vps | Provider, size, price within 10 USD a month, domain | owner | stage 5 |
| reports-channel | Periodic reports and deadline reminders lost their Telegram channel: GNOME notifications, web only, or drop | owner | post-MVP |
| post-mvp-ideas | Chapters, money and deadline tracker, semantic search, translation, phone recording, export to Markdown, asking during a call, interview debrief | owner | post-MVP planning |
| ports | Packaging for other distributions and systems | owner | after the AUR package |
