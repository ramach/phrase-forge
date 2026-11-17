# Sprint 2.5.1 — Lexical Integrity

Based on the archived Sprint 2.4 ZIP, not a checkout of the live deployment.

## Run

```sh
python -m pip install -r requirements.txt
streamlit run living_prototype.py
python -m pytest -q
```

Streamlit Cloud: deploy `living_prototype.py` from a separate branch or beta app first. Keep the existing OpenAI secret; no new API key is needed. `geonamescache` adds an offline geographic name index. No new AI calls are made by lexical filtering. The older `app.py`/`app2.py` interfaces continue to use the default standard validator; the optional mode UI is in `living_prototype.py`.

## Behavior

- Standard mode is default. Known proper names are rejected irrespective of word frequency. The name corpus, editorial additions and installed geographic index are used together.
- Names & Places is an opt-in sidebar checkbox. Recognized names may be accepted only if the ordinary letter, length and substring rules pass. Pronouns remain excluded. Common senses (e.g. turkey, amazon, harmony) remain ordinary words. Names in lists and answer cards are labeled; a specific identity is not asserted.
- Switching mode resets the current discovery and collection progress. Mode-specific solver cache keys prevent cross-session/mode result leakage. The same mode is passed to direct grading, explanations, solution listing, AI puzzle validation and AI collections.
- Editorial common-sense exceptions and accepted overrides are maintained in `lexicon/name_policy.py` and `lexicon/phrase_forge_lexicon.json`. Existing frequency thresholds remain for other words.

## Limitations and test status

This is a conservative name-index filter, not a comprehensive dictionary or named-entity recognizer. Unlisted surnames/brands may still slip through; ordinary words that collide with a name index and lack an editorial exception may be rejected. Report both types of error. If the optional geographic import fails, the bundled name lists still work but geographic coverage is reduced. The new dependency is included in requirements for deployment. The execution environment did not have Streamlit, wordfreq or geonamescache installed and could not fetch them; tests exercise curated cases and mocked frequency, geographic and AI responses. Real dependency integration, live AI calls, mobile/browser testing and production deployment remain to be verified. The POUND NOTE literary authenticity problem is explicitly deferred to 2.5.2/2.5.3.

## Manual beta checklist

1. Standard: FIRST + HAND, ISHANT rejected; find all solutions, ISHANT absent.
2. Enable Names & Places in sidebar; same puzzle, ISHANT accepted and listed; card labels proper noun.
3. Disable mode; old results cleared; ISHANT rejected again.
4. BLIND + RAGE -> ABRIDGE; RAIN + DELAY -> ALREADY.
5. Generate AI puzzle and collection in both modes; confirm listed answers follow selected mode.
6. Test mobile and desktop, including a new private session defaulting to Standard.
