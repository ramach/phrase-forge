# Sprint 2.3.1 — AI Lexical Intelligence

Preserves the Sprint 2.3 interface, generation, and curated Theme Packs.

## New

- On Play and Word Card screens, select **Identify roles & meanings with AI** to enrich missing word information.
- AI creates grammatical roles, concise meaning, usage and examples for words without editorial cards.
- SQLite cache survives Streamlit restarts, defaulting to `~/.phrase_forge/lexical_cache.sqlite3` (override with `PHRASE_FORGE_LEXICAL_DB`).
- Editorial cards take precedence over cached AI cards.
- All AI cards are visibly marked **AI-assisted · unverified**; no AI etymologies are presented.
- The button is opt-in to avoid unpredictable charges on every Streamlit rerun. No API key: existing local Word Cards still work.
- Existing contextual role quiz remains unchanged; AI's possible roles may differ from a role in the source phrase. No AI role-based points are awarded.

## Run

`pip install -r requirements.txt`

`export OPENAI_API_KEY='your-key'`

`streamlit run living_prototype.py`

## Tests

`python -m pytest -q`

## Next sprint

Save AI collections and add a curator review workflow. Add phrase-context-specific role verification before grading AI-generated puzzles for role bonuses.
