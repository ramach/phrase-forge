# Phrase Forge Beta 1.1 — Phase A

**Discover the language hidden inside language.**

Phase A extends the stable Beta 1.0 gameplay with persistent multi-user infrastructure while preserving existing grading, hints, grammar, AI validation, and PFL behavior.

## What's new

- nickname-only beta identity with conservative offensive/reserved-name validation
- PostgreSQL persistence through `DATABASE_URL`
- SQLite fallback for local development
- player sessions, puzzle sessions, attempts, hint counts, and completion tracking
- persistent leaderboard and feedback
- Admin infrastructure metrics
- Puzzle Report Cards
- Decision Log and Phase A architecture notes

## Local run

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
python3 -m streamlit run app.py
```

## Hosted beta

In Streamlit Community Cloud secrets, configure:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

Optional AI:

```toml
OPENAI_API_KEY = "..."
PHRASE_FORGE_OPENAI_MODEL = "gpt-5-mini"
PHRASE_FORGE_AI_SESSION_LIMIT = "3"
```

The application creates its required tables automatically.

## Nicknames

Nicknames are optional for playing but required for leaderboard submission. They must be 3–24 characters, use a small safe character set, and pass the beta reserved/offensive-name policy. No email or login is required.

## Known PFL issue

Some proper names/pronouns can still leak through broader lexicon profiles. This is documented and intentionally deferred while Phase A infrastructure is stabilized.

See `docs/PHASE_A.md`, `docs/DECISION_LOG.md`, `docs/ARCHITECTURE.md`, and `KNOWN_ISSUES.md`.

### Educational learning layer
Accepted forged words now produce a Word Card with role(s), frequency, curated definition when available, and Discovery points. The **My Vocabulary** tab stores unique discoveries and shows a cumulative Discovery Score. With PostgreSQL, a nickname carries the notebook across sessions; SQLite provides the same behavior locally.

# Beta 1.2

For Beta 1.2, I'd like to focus equally on the experience.

I'd love your testers to answer a few questions
🟢 First Impression (30 seconds)
Did you immediately understand what Phrase Forge is?
Did Play • Explore • Learn make sense?
Did the Home screen feel inviting?
Did you know what to click first?
🎮 Gameplay
Did the puzzle screen feel calmer?
Was it obvious where to enter the answer?
Did anything distract you from solving the puzzle?
Was "Check Answer" prominent enough?
🎉 Celebration

This is the feature I'm most interested in.

After a correct answer:

Did it feel rewarding?
Did it motivate you to continue?
Was it too much?
Too little?
📚 Learning

After solving:

Did you actually look at the Word Card?
Did you click Learn?
Did you learn something new?
Was it interesting enough to continue?
🌍 Explore
Would you use Theme Packs?
Would you revisit My Journey?
Is the Leaderboard motivating?
✨ AI

Since AI-generated puzzles have been so well received, I'd specifically ask:

Did you use Create a Puzzle?
Was it easy to find?
Did it produce interesting puzzles?
Would you use it again instead of Random?
💡 One question I'd especially like answered

"Would you recommend Phrase Forge to a friend?"

Not because it's finished.

But because that's often the clearest indicator of whether the experience resonates.

If someone says:

"Not yet, but it's close."

that's actually very useful feedback.

One thing I suspect we'll discover

I have a feeling Beta 1.2 won't generate many comments about the solver or grammar.

Instead, we'll hear things like:

"I'd like more themes."
"I'd like achievements."
"I'd like to compare my progress."
"Can I share a puzzle with a friend?"
"Can I create my own theme?"

If that happens, it's a positive sign. It means people have moved beyond testing mechanics and are thinking about how they'd use the product.

I'd also like to start a "Known Issues" list

Not as bugs to fix immediately, but as a transparent backlog.

For example:

Known Issues
Some proper names still appear under broader lexicon profiles.
A small number of valid words may still be rejected due to dictionary coverage or validation rules.
Grammar inference for uncommon phrase structures can occasionally misidentify roles.
AI-generated themes currently produce single-session puzzles rather than persistent themed collections.
Mobile layout is functional but not yet optimized.

This helps distinguish between defects, trade-offs, and future enhancements.

Looking ahead

Once you've collected this round of feedback, I'd like us to spend one session just reviewing it—without writing any code.

We'll categorize every suggestion into:

Must fix before Beta 1.2 release
Nice improvement for Beta 1.3
Long-term roadmap

That discipline will keep the product focused and prevent us from chasing every idea immediately.

And I have to say, it's been a pleasure watching Phrase Forge evolve with your testers' input. The best products are rarely built in isolation; they're refined through thoughtful feedback while staying true to a clear vision. I think we're doing exactly that, and I'm looking forward to seeing what this round of testing teaches us.
