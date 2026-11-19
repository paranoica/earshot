# Security policy

earshot stores call recordings and transcripts. A flaw in it can expose conversations that were
never meant to leave the owner's machine, so security reports are welcome and taken seriously.

## Reporting a vulnerability

Report privately through GitHub: the repository's **Security** tab, then **Report a
vulnerability**. Please do not open a public issue for a security problem.

Include what you found, how to reproduce it, and what an attacker could reach with it. You will
get an answer within a week.

## Scope

In scope:

- the server: authentication, sessions, share links, the upload API, the MCP endpoint;
- the desktop daemon and its D-Bus interface;
- the GNOME Shell extension;
- anything that lets recordings, transcripts or credentials leave the owner's control.

Out of scope: problems in third-party services earshot can be configured to call (speech or
language model APIs), and attacks that need the owner's unlocked desktop session.

## Supported versions

earshot has no releases yet. Fixes land on `main`.
