# Changelog
## 1.1.2 Beta — Feedback regressions
- Fixed `spare time` grammar inference: spare = adjective, time = noun.
- Fixed `call again` grammar inference: call = verb, again = adverb.
- Added PFL accepted overrides for `earthen` and `ardent`.
- Added regression coverage for `open heart -> earthen` and `data entry -> ardent`.
- Confirmed `green room` has no bundled Standard-profile playable solution and remains rejectable as an unplayable puzzle.


## 1.0.1-beta — 2026-08-09
- Enforced Phrase Forge Lexicon exclusions consistently across every profile.
- Expanded pronoun exclusions to personal, reflexive, relative, reciprocal and indefinite forms.
- Added a bundled multi-locale proper-name corpus with conservative frequency gating.
- Explicitly blocked tester-reported proper names `ishtar` and `ishant`.
- Clarified that Expert and Teacher broaden vocabulary rarity but never enable proper names or pronouns.
- Added Admin Phrase Forge Lexicon Inspector.
- Added regression tests for `FIRST HAND`, proper names and extended pronouns.

## 1.0.0-beta — 2026-08-08
- Added Phrase Forge Lexicon profiles and curated overrides.
- Added indexed solver and validated-solution cache.
- Added PostgreSQL persistence with SQLite fallback.
- Added Beta feedback and diagnostics foundation.

## 1.1.1 Beta Phase A — Learning Layer
- Added accepted-solution Word Cards with part of speech, frequency, definition when curated, lexicon source, and Discovery points.
- Added persistent My Vocabulary notebook backed by PostgreSQL or SQLite fallback.
- Added Discovery Score and rare-vocabulary discovery count.
- Vocabulary discoveries are unique per named player across sessions, or per anonymous browser session.
- Added regression tests for learning metadata and notebook persistence.
