# Sprint 2.1.5 — Lexical Enrichment Correction

- Curated word cards for FINAL (adjective/noun), MILE (noun), and INFLAME (verb).
- Discovery screen now renders through the same `build_word_card` pipeline as the source-word cards, showing meanings, examples, usage notes, and content provenance.
- Regression tests added for FINAL + MILE → INFLAME and uncurated etymology handling.
- No external dictionary integration is included yet: this increment fixes the inconsistent display and the reported example, not universal lexical coverage.
- Existing Streamlit beta remains untouched; run `streamlit run living_prototype.py`.
