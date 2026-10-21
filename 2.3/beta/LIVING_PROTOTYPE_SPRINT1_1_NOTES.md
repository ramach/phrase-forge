# Living Prototype Sprint 1.1 — Puzzle Selection Fix

The original Sprint 1 was a fixed `rain + delay` walkthrough. This release adds:

- New Random Puzzle on Home, Play and Continue screens.
- Generate AI Puzzle on Home, Play and Continue screens (requires OPENAI_API_KEY and API access).
- Replay Current Puzzle to reset the answer without changing source words.
- Random puzzle history avoids immediate repeats until the eligible pool is exhausted.
- Dynamic source words and labels on Play and Discovery screens.
- Existing backend, beta application, and test suite retained.

## Run

```bash
pip install -r requirements.txt
streamlit run living_prototype.py
```

For AI generation, set `OPENAI_API_KEY` in the shell before starting Streamlit. AI candidates are checked by the existing local validator and may take multiple API attempts. If generation fails, use Random.

## Scope

This is a Sprint 1.1 testing build, not the final Theme Packs or My Journey implementation.
