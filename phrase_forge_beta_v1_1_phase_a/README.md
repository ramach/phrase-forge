# Phrase Forge Beta 1.1 — Phase A

**Discover the language hidden inside language.**

Phase A extends the stable Beta 1.0 gameplay with persistent multi-user infrastructure while preserving existing grading, hints, grammar, AI validation, and PFL behavior.

## What's new

- nickname-only beta identity with conservative offensive/reserved-name validation
- PostgreSQL persistence through `DATABASE_URL`
- SQLite fallback for local development
- player sessions, puzzle sessions, attempts, hint counts, and completion tracking
- persistent leaderboard and feedback
- Admin infrastructure metrics
- Puzzle Report Cards
- Decision Log and Phase A architecture notes

## Local run

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
python3 -m streamlit run app.py
```

## Hosted beta

In Streamlit Community Cloud secrets, configure:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

Optional AI:

```toml
OPENAI_API_KEY = "..."
PHRASE_FORGE_OPENAI_MODEL = "gpt-5-mini"
PHRASE_FORGE_AI_SESSION_LIMIT = "3"
```

The application creates its required tables automatically.

## Nicknames

Nicknames are optional for playing but required for leaderboard submission. They must be 3–24 characters, use a small safe character set, and pass the beta reserved/offensive-name policy. No email or login is required.

## Known PFL issue

Some proper names/pronouns can still leak through broader lexicon profiles. This is documented and intentionally deferred while Phase A infrastructure is stabilized.

See `docs/PHASE_A.md`, `docs/DECISION_LOG.md`, `docs/ARCHITECTURE.md`, and `KNOWN_ISSUES.md`.

### Educational learning layer
Accepted forged words now produce a Word Card with role(s), frequency, curated definition when available, and Discovery points. The **My Vocabulary** tab stores unique discoveries and shows a cumulative Discovery Score. With PostgreSQL, a nickname carries the notebook across sessions; SQLite provides the same behavior locally.
