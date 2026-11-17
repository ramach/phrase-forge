# Phase A — Persistent Infrastructure

Phase A adds durable multi-user beta infrastructure without changing the core game rules.

## Storage modes

- **Local development:** SQLite, automatically selected when `DATABASE_URL` is absent.
- **Hosted beta:** PostgreSQL, automatically selected when `DATABASE_URL` starts with `postgres://` or `postgresql://`.

## Persisted entities

- `players`: nickname-based beta player identity.
- `player_sessions`: browser/app sessions and application version.
- `puzzle_sessions`: started/completed puzzles and hint counts.
- `attempts`: submitted forged words and score breakdowns.
- `scores`: best leaderboard score per player/puzzle/mode.
- `beta_feedback`: structured tester feedback and diagnostic snapshot.
- `usage_events`: lightweight event stream for later analytics.

## Privacy

The beta does not require email, password, full name, or other direct identifiers. Testers may choose a nickname. Avoid entering personal information in nicknames or feedback.

## Puzzle Report Cards

Admin can aggregate persisted sessions into report cards showing sessions, completion rate, attempts, average hints, and average accepted score.

## Failure behavior

Analytics and persistence warnings are non-blocking. The game continues to function if an analytics write fails; the latest warning appears in Admin diagnostics.

## Learning layer
Phase A now also persists educational discoveries. Each accepted solution receives a Word Card derived from Phrase Forge Lexicon metadata. Named players accumulate a persistent vocabulary notebook across sessions when PostgreSQL is configured; anonymous players retain a session-scoped notebook. Discovery Score rewards new vocabulary only and does not alter gameplay or leaderboard scoring.
