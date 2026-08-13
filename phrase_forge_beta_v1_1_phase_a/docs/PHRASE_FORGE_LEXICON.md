# Phrase Forge Lexicon (PFL)

PFL is a gameplay and educational lexicon, not a raw Scrabble dictionary.

## Acceptance policy

Every gameplay subsystem uses the same final PFL decision. A token being present in `wordfreq` is evidence that it occurs in English text; it is **not** sufficient by itself for Phrase Forge play.

Accepted categories include ordinary English nouns, verbs, adjectives, adverbs, useful inflected forms and technical vocabulary according to the selected profile.

Excluded in **all profiles**:
- proper names
- pronouns, including reflexive, relative and indefinite pronouns
- curated abbreviations/acronyms
- curated offensive or unsuitable entries
- nonalphabetic tokens

Profiles only broaden vocabulary rarity:
- **Casual** — everyday English
- **Standard** — broad default beta vocabulary
- **Expert** — rarer legitimate English vocabulary
- **Teacher** — Expert vocabulary plus educational metadata where available

Expert and Teacher do **not** enable names or pronouns.

## Proper-name handling

PFL combines authoritative explicit blocks with a bundled multi-locale first-name corpus. Corpus-name matches are rejected conservatively when their English corpus frequency is low enough to indicate that they are probably functioning as names. This avoids automatically rejecting ordinary words that can also be names, such as `mark`, `rose`, `grant`, `hope`, `bill`, or `will`.

Tester-reported cases such as `ishtar` and `ishant` are explicit proper-name blocks.

## Curated overrides

`lexicon/phrase_forge_lexicon.json` contains authoritative accepted overrides and blocked words. Legitimate lower-frequency discoveries such as `kneeler`, `wheaten`, and `claimer` belong here rather than as scattered exceptions in game logic.

## Single source of truth

`lexicon.validators.lexicon_info()` is the authoritative decision function. Direct grading, indexed solver results, hints, difficulty, AI puzzle validation, Show All Solutions and Admin diagnostics ultimately pass through this same decision.

The Admin **Phrase Forge Lexicon Inspector** shows the decision, reason and source for any word under every profile.
