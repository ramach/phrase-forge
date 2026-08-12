# Known Issues

- Proper-name detection is seeded, not linguistically exhaustive. Tester reports should be added to the versioned PFL block list.
- Dictionary frequency is evidence, not meaning; unusual legitimate words may need curated PFL overrides.
- Colab and Streamlit local files are ephemeral; configure PostgreSQL for persistent leaderboard/feedback data.
- AI puzzle generation depends on API availability and configured usage limits; curated Practice remains the default.
