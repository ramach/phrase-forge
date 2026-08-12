# Changelog

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
