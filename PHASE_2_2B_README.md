# Phrase Forge Phase 2.2B — Lightweight Grammar Engine

Phase 2.2B adds contextual grammar analysis for manually entered phrases without requiring spaCy or a downloadable language model.

## Grammar analysis order

1. Curated metadata in `data/phrases.json` remains authoritative.
2. Unknown two-word phrases are analyzed by the built-in grammar engine.
3. The UI labels the result as inferred and displays an estimated confidence.

The built-in engine combines compact lexical sets, common phrasal-verb particles, and word-form rules. It is intentionally conservative. Lower-confidence cases should be reviewed and, when important, added to the curated phrase bank.

## Local setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

No separate NLP model installation is required.

## Grammar diagnostics and confidence safeguards

The grammar result now records and displays:

- the rule identifier and human-readable rule name
- a concise explanation of why the rule fired
- numeric confidence and a confidence band
- whether the inferred result is eligible for role bonus credit

Confidence behavior:

- Curated: authoritative metadata; role credit enabled.
- High (90%+): strong built-in rule; role credit enabled.
- Medium (70–89%): plausible contextual rule; role credit enabled and labeled inferred.
- Low (below 70%): educational result shown, but automatic role credit is withheld until curated.

The grading result also preserves `raw_points` so the UI can explain what would have been earned if the phrase were verified.

## Explain My Answer panel

Every graded submission now includes a rule-by-rule explanation. The panel reports:

- letters-only input validation
- forbidden input-word substring validation
- exact letter-frequency availability, including quantified shortages
- applicable minimum length and vowel-start exception
- English dictionary recognition
- exact standalone-word bonus validation
- base score, forged-word score, grammar bonus, and combined score
- letters used, letters remaining, and excess letters

Invalid submissions open the panel automatically. Valid submissions keep it collapsed until requested.
