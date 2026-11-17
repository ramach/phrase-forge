# Sprint 2.3 — Theme-Aware AI Puzzle Generation

Launch: `streamlit run living_prototype.py`

- Existing single AI puzzle generation accepts an optional theme on Home.
- Explore → Create an AI Discovery Collection supports a custom theme, difficulty, and 3/5/10 puzzles.
- Generated puzzles use the existing Phrase Forge local solution validator; duplicate source-word pairs are excluded.
- Generated collection progress is session-scoped. AI generation requires `OPENAI_API_KEY` and network access.
- Model suggestions are not independently verified for semantic theme relevance: review theme fit before public release.
- Generating ten puzzles may take time or use multiple API calls; incomplete collections are explicitly labeled.
- Existing Streamlit beta (`app.py` / `app2.py`) is unchanged.

## Known limitations
- AI may return weakly themed phrases. Theme relevance is currently prompted, not independently scored.
- The lexical validator's coverage is limited by the local dictionary.
- Collections and progress are not persisted across sessions.
