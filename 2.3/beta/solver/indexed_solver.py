from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from typing import Iterable

from lexicon.validators import available_profiles

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
VOWELS = set("aeiou")


def _counts(word: str) -> tuple[int, ...]:
    return tuple(word.count(ch) for ch in ALPHABET)


@lru_cache(maxsize=4)
def build_index(max_words: int = 200_000) -> dict[int, tuple[tuple[str, tuple[int, ...]], ...]]:
    """Build a reusable length/multiset index over the English candidate list."""
    words: set[str] = set()
    try:
        from wordfreq import top_n_list  # type: ignore
        words.update(w.lower() for w in top_n_list("en", max_words) if w.isalpha())
    except Exception:
        pass

    # PFL curated overrides must always be discoverable by the solver.
    try:
        import json
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "lexicon" / "phrase_forge_lexicon.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        words.update(payload.get("accepted_overrides", {}).keys())
    except Exception:
        pass

    buckets: dict[int, list[tuple[str, tuple[int, ...]]]] = defaultdict(list)
    for word in words:
        if word.isalpha():
            buckets[len(word)].append((word, _counts(word)))
    return {length: tuple(items) for length, items in buckets.items()}


def indexed_candidates(
    letters: str,
    consonant_min: int,
    max_words: int = 200_000,
) -> tuple[str, ...]:
    """Return words whose letter multisets can fit inside ``letters``.

    This is a pre-filter only. The canonical Phrase Forge grader remains the
    final authority for substring, lexicon-profile, and scoring rules.
    """
    available = _counts(letters.lower())
    total = len(letters)
    vowel_min = max(1, consonant_min - 1)
    index = build_index(max_words)
    out: list[str] = []
    for length in range(vowel_min, total + 1):
        for word, needed in index.get(length, ()):
            if length < consonant_min and (not word or word[0] not in VOWELS):
                continue
            if all(n <= a for n, a in zip(needed, available)):
                out.append(word)
    return tuple(out)


def index_stats(max_words: int = 200_000) -> dict:
    index = build_index(max_words)
    return {
        "indexed_words": sum(len(items) for items in index.values()),
        "length_buckets": len(index),
        "max_words_requested": max_words,
        "profiles": sorted(available_profiles()),
    }
