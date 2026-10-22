# Living Prototype Sprint 2.1.3

Fixes and restores:
- Eliminates nested Streamlit expanders on the discovery Word Card.
- Custom two-word puzzle entry on Home and Play.
- Interactive source-word grammatical-role selection with grading and inferred-role caveats.
- Player-discovered solutions and optional local lexicon solution listing.

Start: `streamlit run living_prototype.py`

Notes: "Find all verified solutions" uses the configured local lexicon, and does not guarantee every dictionary word. Custom puzzles are not guaranteed to have solutions. AI-generated puzzles still require an OpenAI API key. The existing beta `app.py` is unchanged.
