# Glossary

| Term | Meaning |
|---|---|
| Owner | The one person who records, reads and edits. The only account |
| Guest | Anyone opening a share link |
| Call | One conversation from detection to the end of the 30-second grace period, in one app |
| Candidate call | A microphone hold that has not yet passed 10 s or not yet been answered |
| Prompt | The "Record this call?" notification and its answer |
| Pre-roll | Audio kept in memory from detection until the answer; kept on Record, dropped otherwise |
| Track | One audio stream of a call: `mic` (the owner) or `system` (everyone else) |
| Chunk | 20–30 s of one track cut at a speech boundary, uploaded on its own |
| Full track | The whole track uploaded after the call; it wins over chunks in reconcile |
| Reconcile | The server's check that chunks and the full track agree, filling any gap |
| Spool | The daemon's local folder of recordings and the upload queue |
| Receipt | The server's confirmation of what it stored; the daemon deletes local data only after it |
| Segment | A piece of transcript with speaker, start, end and text |
| Voice print | A speaker embedding computed from a chunk of the system track |
| Diarization | Grouping segments of the system track by speaker |
| Template | The summary format for a kind of call (Auto, Client call, Scoping, Interview, Work sync, 1:1, Therapy) |
| Summary version | One generated summary; regenerating keeps the old versions |
| Action item | A task found in a call: text, owner, due date, timecode, done flag |
| Share link | A revocable, expiring URL with a random token and toggles for what a guest sees |
| Engine | A replaceable implementation behind an interface: recogniser, voice prints, echo removal, language model |
| Router | The component that sends a language-model request to the configured provider in one of three dialects |
| Worker | The server process that runs engines, separate from the API |
| Stage | A step of the roadmap with its own done-when |
| Block | One unit of work in the bedrock loop: plan, tasks, review, delivery |
| Task | One commit-sized piece of a block with its own test |
