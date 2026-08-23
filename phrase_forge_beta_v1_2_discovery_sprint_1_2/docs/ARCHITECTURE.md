# Architecture

```text
Streamlit UI (app.py)
   |
   +-- game_backend.py
   |     +-- phrase bank (data/phrases.json)
   |     +-- grammar engine
   |     +-- canonical grader
   |     +-- Phrase Forge Lexicon (lexicon/)
   |     +-- indexed solver (solver/)
   |
   +-- leaderboard_db.py
   |     +-- SQLite (local fallback)
   |     +-- PostgreSQL (DATABASE_URL)
   |
   +-- ai_puzzle_generator.py
         +-- optional phrase proposal
         +-- deterministic local validation
```

The canonical grader is the single source of truth. Solver, hints, difficulty and solution reveal reuse the same accepted solution set.
