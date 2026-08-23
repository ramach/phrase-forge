from __future__ import annotations

from functools import lru_cache
from typing import Optional

from game_backend import get_word_info

FREQUENCY_POINTS = {
    "very_common": 1,
    "common": 2,
    "less_common": 3,
    "rare": 5,
}


def _infer_pos(word: str) -> list[str]:
    w = (word or "").lower()
    if not w:
        return []
    if w.endswith("ly"):
        return ["adverb"]
    if w.endswith(("tion", "sion", "ment", "ness", "ity", "er", "or", "ist")):
        return ["noun"]
    if w.endswith(("ous", "ful", "less", "able", "ible", "ive", "al", "ic", "ish", "en")):
        return ["adjective"]
    if w.endswith(("ize", "ise", "ify")):
        return ["verb"]
    if w.endswith("ing"):
        return ["verb", "noun"]
    if w.endswith("ed"):
        return ["verb", "adjective"]
    return []


def _display_frequency(value: Optional[str]) -> str:
    return (value or "unknown").replace("_", " ").title()


def _discovery_label(frequency: Optional[str]) -> str:
    return {
        "very_common": "Everyday Vocabulary",
        "common": "Common Vocabulary",
        "less_common": "Vocabulary Discovery",
        "rare": "Rare Vocabulary Discovery",
    }.get(frequency or "", "Vocabulary Discovery")


@lru_cache(maxsize=20000)
def word_learning_metadata(word: str, profile: str = "standard") -> dict:
    info = dict(get_word_info(word, profile) or {})
    pos = list(info.get("part_of_speech") or []) or _infer_pos(word)
    frequency = info.get("frequency")
    points = FREQUENCY_POINTS.get(frequency or "", 2)
    return {
        "word": (word or "").strip().lower(),
        "accepted": bool(info.get("accepted", True)),
        "profile": info.get("profile", profile),
        "part_of_speech": pos,
        "frequency": frequency,
        "frequency_label": _display_frequency(frequency),
        "definition": info.get("definition"),
        "lexicon_source": info.get("source"),
        "zipf": info.get("zipf"),
        "discovery_points": points,
        "discovery_label": _discovery_label(frequency),
    }
