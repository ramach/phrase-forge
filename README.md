# Phrase Forge 0.9.0 Beta

**Discover the language hidden inside language.**

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
python3 -m streamlit run app.py
```

## Streamlit Community Cloud

Deploy `app.py` from the repository root. Include `data/phrases.json` and `requirements.txt` in the repository.

Optional secrets:

```toml
OPENAI_API_KEY = "..."
PHRASE_FORGE_OPENAI_MODEL = "gpt-5-mini"
PHRASE_FORGE_AI_SESSION_LIMIT = "3"
```

AI is optional. Normal Practice puzzles come from the curated phrase bank. Every AI suggestion must pass the deterministic Phrase Forge validator before it is presented.

## Beta behavior

- A fresh browser session starts in Practice with a curated random puzzle.
- **New random puzzle** avoids immediately repeating the current phrase.
- Daily mode gives all players the same puzzle for the date.
- Feedback diagnostics can be downloaded as JSON.

See `CHANGELOG.md`, `KNOWN_ISSUES.md`, and `BETA_TEST_GUIDE.md`.
