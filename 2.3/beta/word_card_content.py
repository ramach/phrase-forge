"""Verified/local-first content for Living Prototype Word Cards.

Editorial examples are explicitly curated; dictionary metadata remains separate.
Never invent an origin when the local content has none.
"""
from learning_metadata import word_learning_metadata

CURATED = {
    "already": {"roles": ["adverb"], "meaning": "Before now or before the time in question.", "examples": ["She had already found the answer.", "The train has already left."], "usage": "Often signals that something happened earlier than expected.", "origin": None},
    "rain": {"roles": ["noun", "verb"], "meaning": "Water falling from clouds (noun); to fall as rain (verb).", "examples": ["The rain stopped before noon.", "It may rain tomorrow."], "usage": "The same spelling can name a thing or describe an action.", "origin": None},
    "delay": {"roles": ["noun", "verb"], "meaning": "A postponement (noun); to make something happen later (verb).", "examples": ["There was a delay in departure.", "Please do not delay the meeting."], "usage": "Can refer to a postponement or the action of postponing.", "origin": None},
    "final": {"roles": ["adjective", "noun"], "meaning": "Last or concluding (adjective); a deciding competition or examination (noun).", "examples": ["This is the final chapter.", "They reached the final."], "usage": "Often an adjective; also a noun for an examination or competition.", "origin": None},
    "mile": {"roles": ["noun"], "meaning": "A unit of distance equal to 5,280 feet (about 1.609 kilometers).", "examples": ["We walked a mile."], "usage": "A measure of distance.", "origin": None},
    "inflame": {"roles": ["verb"], "meaning": "To ignite or intensify; to provoke strong feelings or conflict.", "examples": ["The remarks threatened to inflame tensions."], "usage": "Often used figuratively for making anger or conflict more intense.", "origin": None},
    "aerial": {"roles": ["adjective", "noun"], "meaning": "Related to the air; as a noun, an antenna.", "examples": ["The photographer captured an aerial view."], "usage": "Its grammatical role depends on context.", "origin": None},
}

def build_word_card(word: str) -> dict:
    normalized = (word or "").strip().lower()
    meta = word_learning_metadata(normalized)
    curated = CURATED.get(normalized, {})
    if not curated:
        try:
            from ai_lexical_enrichment import cached_card
            cached = cached_card(normalized)
            if cached:
                return cached
        except (OSError, ValueError, __import__('sqlite3').DatabaseError):
            pass
    roles = curated.get("roles") or meta.get("part_of_speech") or []
    verified = bool(curated.get("roles") or ((getattr(meta, "get", lambda k: None)("part_of_speech")) and meta.get("definition")))
    # Suffix-based roles from learning_metadata are only suggestions, not verified classifications.
    return {
        "word": normalized,
        "roles": roles,
        "meaning": curated.get("meaning") or meta.get("definition"),
        "examples": curated.get("examples") or [],
        "usage": curated.get("usage"),
        "origin": curated.get("origin"),
        "source": "Phrase Forge editorial" if curated else (meta.get("lexicon_source") or "Not curated"),
        "frequency": meta.get("frequency_label"),
        "role_verified": verified,
    }
