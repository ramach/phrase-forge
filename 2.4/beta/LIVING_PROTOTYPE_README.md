# Phrase Forge — Living Prototype v1.0, Sprint 1

This is a **playable first vertical slice**, not the complete Living Prototype v1.0.

## Run on your Mac

```bash
cd phrase_forge_beta_v1_2_discovery_sprint_1_2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run living_prototype.py
```

Open the local address Streamlit displays (normally http://localhost:8501).

## Included journey

Home → How Phrase Forge Works → Play → educational validation → Discovery Moment → Word Card → Continue Exploring.

Uses the **existing `game_backend.grade_solution` and `explain_answer_attempt`** with a fixed, curated onboarding puzzle, RAIN + DELAY → ALREADY. It applies a seven-letter consonant minimum (six for vowels), and requires the existing lexicon validation.

## Deliberately not yet included

- Multiple playable Theme Packs, persistent journey tracking, hints, and AI-generated puzzles in the new prototype
- A custom frontend or Flutter app
- Public deployment

The original `app.py` Streamlit beta is unchanged; run it with `streamlit run app.py`.

## Next sprint

Make curated themes playable, integrate progress, improve mobile UX, then prepare shareable deployment.
