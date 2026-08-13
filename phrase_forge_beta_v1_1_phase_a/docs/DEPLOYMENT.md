# Deployment

## Streamlit Community Cloud
Deploy `app.py` from the repository root. Add secrets in Streamlit's Secrets configuration:

```toml
DATABASE_URL = "postgresql://..."
OPENAI_API_KEY = "..." # optional
PHRASE_FORGE_OPENAI_MODEL = "gpt-5-mini"
PHRASE_FORGE_AI_SESSION_LIMIT = "3"
```

Without `DATABASE_URL`, the app falls back to local SQLite; this is suitable for local development but not persistent cloud beta data.

## Colab
Upload or clone the complete repository into the Colab runtime. Then paste the contents of `COLAB_ONE_CELL.py` into one code cell. The launcher installs dependencies, starts Streamlit, downloads Cloudflare's Linux tunnel binary, prints the temporary public URL, and shows logs on failure.

Colab remains temporary. Use PostgreSQL via `DATABASE_URL` if leaderboard/feedback data must survive runtime restarts.
