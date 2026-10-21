# Phrase Forge Specification 1.0

## Core puzzle
A puzzle contains two words forming a recognized phrase, expression or idiom. The player identifies each word's contextual grammatical role and forges a different English solution from the combined letters.

## Letter rules
- Letter frequency is strict.
- A solution cannot contain either complete input word as a substring.
- Player answers must contain alphabetic characters only.
- Default consonant-start minimum: total phrase letters minus two.
- A vowel-starting solution may be one letter shorter.

## Base scoring
- 6 letters, vowel start: 75
- 7 letters, consonant start: 80
- 7 letters, vowel start: 85
- 8+ letters: 90
- Exact standalone use in the bonus sentence: forged-word score 95
- Contextual grammar role bonus: up to +10

## Grammar
Curated phrase metadata is authoritative. Unknown manual phrases use the lightweight grammar engine. Low-confidence inference can be displayed without automatically awarding role credit.

## Hints
Hints must originate only from answers accepted by the canonical grader. Progression: strategy, start type, length, letter distribution, useful letter, first letter, pattern, final reveal.

## Lexicon
Beta 1.0 uses the Phrase Forge Lexicon rather than accepting every dictionary token. PFL profiles govern rarity; gameplay exclusions reject pronouns and seeded proper names by default. Curated overrides may explicitly accept legitimate low-frequency words.

## AI boundary
AI may propose candidate phrase pairs and educational metadata. AI does not decide whether a puzzle or forged solution is valid. Deterministic Phrase Forge validation remains authoritative.
