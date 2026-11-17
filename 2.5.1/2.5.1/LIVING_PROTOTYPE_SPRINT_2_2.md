# Phrase Forge — Living Prototype Sprint 2.2

## Playable Theme Packs

- Home → Browse Theme Packs → select a curated collection → Continue Journey.
- Play and solve a source-phrase puzzle. Valid answers mark that source phrase complete for the current Streamlit session.
- Discovery → Word Card → Continue Exploring → Continue This Collection.
- Collection page shows completion counts and the curated source-phrase list.
- Next Discovery prefers an uncompleted phrase; completing all entries returns to the collection.
- Random, AI and Custom puzzle actions leave the current theme and continue independently.

## Important caveats

- The phrase bank includes verified *source phrases* without preverified valid solutions. These are exploratory challenges; some may have no solution under the game's letter constraints.
- Progress is kept in Streamlit session state and is not yet persisted across restarts/devices.
- Existing AI generation and lexical-enrichment limitations remain.
- This sprint does not claim that the Shakespeare collection exists in the current data; it displays the actual source categories.

## Start

`pip install -r requirements.txt`

`streamlit run living_prototype.py`
