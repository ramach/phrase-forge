# Phrase Forge Beta 1.0

**Discover the language hidden inside language.**

Beta 1.0 consolidates the stable 0.9.x gameplay into a scalable educational architecture:

- Phrase Forge Lexicon (PFL) profiles and exclusions
- indexed/cached solver shared by difficulty, hints and solution reveal
- contextual grammar with confidence and role credit
- Explain My Answer
- optional AI puzzle suggestions with deterministic validation
- PostgreSQL cloud persistence with SQLite fallback
- leaderboard, feedback and basic usage-event tables
- Streamlit Community Cloud and Colab launch paths

## Local run

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
python3 -m streamlit run app.py
```

## Phrase Forge Lexicon profiles

- **Casual**: common everyday English.
- **Standard**: beta default; broad English vocabulary.
- **Expert**: rarer vocabulary allowed.
- **Teacher**: Expert vocabulary plus educational metadata when available.

Proper names and pronouns are excluded by default. Curated PFL overrides keep valid lower-frequency discoveries such as `kneeler`, `wheaten`, and `claimer` available in appropriate profiles.

## Persistent PostgreSQL

Local development needs no configuration and uses SQLite.

For Streamlit Community Cloud or Colab, set:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

Beta 1.0 automatically creates the `scores`, `beta_feedback`, and `usage_events` tables.

## Optional AI

```toml
OPENAI_API_KEY = "..."
PHRASE_FORGE_OPENAI_MODEL = "gpt-5-mini"
PHRASE_FORGE_AI_SESSION_LIMIT = "3"
```

AI only proposes phrases. The deterministic Phrase Forge engine must find at least one legal solution before an AI puzzle is accepted.

See `docs/SPECIFICATION_1_0.md`, `docs/ARCHITECTURE.md`, `docs/PHRASE_FORGE_LEXICON.md`, and `docs/DEPLOYMENT.md`.

I'd like us to aim for something like this in a future release:

                 Phrase Forge Platform

                ┌────────────────────┐
                │   Streamlit UI     │
                └─────────┬──────────┘
                          │
          ┌───────────────┼────────────────┐
          │               │                │
     Game Engine     Grammar Engine   Teacher Mode
          │               │                │
          └───────────────┼────────────────┘
                          │
                 Phrase Forge Lexicon
                          │


          ┌───────────────┼────────────────┐
          │               │                │
     PostgreSQL      Analytics      AI Assistant

### Phase A — Infrastructure

 1) ✅ PostgreSQL / Supabase backend
 2) ✅ Persistent leaderboard
 3) ✅ Persistent beta feedback
 4) ✅ Analytics
 5) ✅ Admin dashboard

### Phase B — Product Quality
1) Phrase Forge Lexicon (PFL)
2) Pronoun/proper-name classification improvements
3) Puzzle quality metrics
4) Puzzle Report Card

### Phase C — Public Launch
1) Landing page
2) Logo and branding
3) Demo video
4) Teacher Mode
5) Public beta announcement


Phase A – Infrastructure, with this sequence:
---------------------------------------------

1) PostgreSQL / Supabase integration
2) Automatic PostgreSQL detection via DATABASE_URL
3) SQLite fallback for local development
4) Zero changes to gameplay
5) Persistent services
6) Leaderboard
7) Feedback
8) Puzzle analytics
9) User sessions
10) Admin Dashboard
11) Live beta statistics
12) Feedback browser
13) Puzzle Report Cards
14) Lexicon Inspector
15) Solver diagnostics
16) Deployment
17) Streamlit Community Cloud
18) Colab launcher
19) Docker support (optional)
20) Environment templates

Notice that the Phrase Forge Lexicon sits at the center. I think that's the architecture that will allow the project to grow for years.
