# Phrase Forge Decision Log

## 2026-08-12 — Phase A infrastructure

- Production persistence uses PostgreSQL through `DATABASE_URL`; local development falls back to SQLite.
- Player identity is nickname-only for beta. No email or login is required.
- Nicknames are validated for length, characters, reserved system names, and a conservative offensive-language block list.
- Gameplay must continue if analytics writes fail; analytics failures are surfaced in Admin diagnostics rather than blocking play.
- Puzzle analytics are derived from persisted player sessions, puzzle sessions, attempts, hints, completion, leaderboard and feedback records.
- AI proposes puzzles only; deterministic Phrase Forge validation remains authoritative.
- PFL proper-name/pronoun leakage is a documented known issue and does not block Phase A.

- Accepted-solution educational metadata is additive: Word Cards and Discovery Score never change the core puzzle score.
- Vocabulary discoveries are deduplicated by player+word for named players and session+word for anonymous play.
- Definitions are shown only when curated; the UI does not invent a definition when the PFL lacks one.
