# Known Issues

- Proper-name detection is seeded, not linguistically exhaustive. Tester reports should be added to the versioned PFL block list.
- Dictionary frequency is evidence, not meaning; unusual legitimate words may need curated PFL overrides.
- Colab and Streamlit local files are ephemeral; configure PostgreSQL for persistent leaderboard/feedback data.
- AI puzzle generation depends on API availability and configured usage limits; curated Practice remains the default.

- **PFL classification:** Some proper names and pronouns may still appear in validated solution lists, especially under broader lexicon profiles. Letter-rule correctness and scoring are unaffected. This is tracked for a stronger lexical-classification pass after the Phase A infrastructure work.

## Zero-solution puzzles
Some natural two-word phrases may have no PFL-accepted forged solution under the active profile. Manual and AI puzzle creation reject such pairs rather than forcing a puzzle into play.
