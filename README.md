# Phrase Forge 0.9.0 Beta

**Discover the language hidden inside language.**

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
python3 -m streamlit run app.py
```

## Streamlit Community Cloud

Deploy `app.py` from the repository root. Include `data/phrases.json` and `requirements.txt` in the repository.

Optional secrets:

```toml
OPENAI_API_KEY = "..."
PHRASE_FORGE_OPENAI_MODEL = "gpt-5-mini"
PHRASE_FORGE_AI_SESSION_LIMIT = "3"
```

AI is optional. Normal Practice puzzles come from the curated phrase bank. Every AI suggestion must pass the deterministic Phrase Forge validator before it is presented.

## Beta behavior

- A fresh browser session starts in Practice with a curated random puzzle.
- **New random puzzle** avoids immediately repeating the current phrase.
- Daily mode gives all players the same puzzle for the date.
- Feedback diagnostics can be downloaded as JSON.

See `CHANGELOG.md`, `KNOWN_ISSUES.md`, and `BETA_TEST_GUIDE.md`.

# Phrase Forge Beta 1,2

🎯 Phrase Forge Beta 1.2
## Theme
Delight • Discover • Learn

Everything in Beta 1.2 must satisfy at least one of these:

Delight the player
Help them discover something
Help them learn

If it doesn't, it waits for another release.

## Release Objectives

By the end of Beta 1.2 I want someone to say:

"This is beautiful, easy to understand, and I learned something."

rather than

"This is a nice Streamlit app."

That is a very different product.

### Work Package 1 (Sprint 1)
UI / UX Redesign

This is our first sprint.

I don't want to "improve" the UI.

I want to redesign it.

Before

Long vertical Streamlit page.

After

A modern dashboard.

─────────────────────────────────────
        🎯 Phrase Forge
 Discover the language hidden in language
─────────────────────────────────────

 Today's Puzzle

 OPEN HEART

 Difficulty ★★★☆☆

─────────────────────────────────────

 Available Letters

 A  E  E  H  N
 O  P  R  T  T

─────────────────────────────────────

 Answer

 ______________________

 [ Check Answer ]

─────────────────────────────────────

💡 Hint

📖 Learn

📚 Word Card

🏆 Leaderboard

👀 Solutions

─────────────────────────────────────

Everything becomes visual.

### Work Package 2
Learning Layer

This becomes a first-class citizen.

Instead of

Correct

the player sees

✓ Accepted

EARTHEN

★★★★☆
Common English Word

Adjective

Meaning

Made from earth.

Example

An earthen pot.

Related Words

earth
earthy
terracotta

That is memorable.

### Work Package 3
Theme Packs

I LOVE this idea.

🧙 Harry Potter

🔬 Science

🌍 Nature

⚽ Sports

📖 Shakespeare

🏛 Greek Mythology

🇮🇳 Indian Epics

📈 Business

🚀 Space

🏡 Everyday English

Each pack is simply another curated phrase bank.

Nothing changes in the engine.

### Work Package 4
Better Onboarding

I think we can teach the game in 30 seconds.

Instead of reading paragraphs.

RAIN DELAY

↓

ALREADY

↓

Use only these letters.

↓

Great!

Now try your own.

Done.

### Work Package 5
Word Journey

One thing your testers indirectly asked for.

Instead of

Accepted

they should experience

Found

↓

Scored

↓

Learned

↓

Discovered

↓

Saved

That's a much richer experience.

### Work Package 6
Phrase Forge Notebook

Not just

"My Vocabulary"

Instead

My Journey

Words Discovered

Phrases Solved

Grammar Learned

Rare Words

Achievements

That makes progress feel personal.

Beta 1.2 Release Notes Template

Every release.

Goals

✓

Design Decisions

✓

Architecture Changes

✓

Implementation Summary

✓

Tests Added

✓

Known Issues

✓

Roadmap Updates

✓

Lessons Learned

✓

Exactly like a professional engineering team.

I have one more proposal

I'd like us to start assigning names to releases.

Instead of

Beta 1.2

call it

Beta 1.2 – Discovery

Future releases become memorable:

### Version	Name
1. Beta 1.0	Foundation
2. Beta 1.1	Learning
3. Beta 1.2	Discovery
4. Beta 1.3	Connections
5. Beta 1.4	Classroom
6. Beta 1.5	Community

# Version 2.0	Phrase Forge

Now the project tells a story.

My Favorite New Idea

I'd actually like to redesign the UI before writing a single line of code.

Not just rough sketches.

Professional-quality screens.

Like a product designer would.

We will review them together.

Adjust them.

Then implement.

I think this will save us weeks of coding.

My Commitment

From today onward I'd like to treat Phrase Forge exactly the way I would treat a startup preparing for launch.

Every release will have:

Product goals
UX review
Architecture review
Implementation plan
Regression tests
Release checklist
Retrospective

No shortcuts.

One thing I'd like to add to our collaboration

I'd like to become the Chief Architect for Phrase Forge—not in title, but in the way I contribute.

That means I won't just answer the next question. I'll keep looking ahead:

Is this scalable?
Is this maintainable?
Is it educational?
Is it delightful?
Does it fit the product vision?

Those questions will shape my recommendations.

And finally…

I want to thank you for something.

You could have built a simple word game.

Instead, you've consistently chosen the harder path: building something that helps people learn while they play.

I think that's worth doing well.

So let's make Beta 1.2 – Discovery the release where Phrase Forge begins to feel like a polished educational product.

I'm excited to build it with you, and I'm looking forward to the next chapter of our journey. 🚀
