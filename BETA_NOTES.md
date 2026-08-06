# Phrase Forge Beta onboarding and AI puzzle generation

## Changes
- Practice is now the default mode and creates a random per-session puzzle.
- Daily remains deterministic and is clearly labeled as the same puzzle for everyone that day.
- A visible How to Play box explains the objective and includes `RAIN DELAY → ALREADY`.
- Optional AI puzzle generation uses the OpenAI Responses API.
- AI output is never trusted directly: every suggested phrase must produce at least one candidate that passes the local Phrase Forge grader.

## Streamlit secrets
Create `.streamlit/secrets.toml` locally or add this in Streamlit Community Cloud secrets:

```toml
OPENAI_API_KEY = "your-key"
PHRASE_FORGE_OPENAI_MODEL = "gpt-5-mini"
```

The app works without an API key; only the AI generator is disabled.
