from __future__ import annotations

import hashlib
import json
import os
import random
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

VOWELS = set("aeiou")
WORD_RE = re.compile(r"^[A-Za-z]+$")

PHRASE_DATA_ENV = "PHRASE_FORGE_PHRASE_DATA"
DEFAULT_PHRASE_DATA_PATH = Path(__file__).resolve().parent / "data" / "phrases.json"
REQUIRED_PHRASE_FIELDS = {
    "word1", "word2", "phrase", "category", "roles",
    "role_explanations", "meaning", "example", "verified",
}
ALLOWED_ROLES = {
    "noun", "verb", "adjective", "adverb", "pronoun", "preposition",
    "conjunction", "determiner", "interjection", "proper noun",
    "auxiliary", "other",
}


class PhraseDataError(ValueError):
    """Raised when the external phrase bank is malformed or ambiguous."""


def _normalize_phrase_token(value: object) -> str:
    return str(value or "").strip().lower()


def validate_phrase_records(records: object) -> List[dict]:
    """Validate and normalize external phrase records; reject duplicates."""
    if not isinstance(records, list):
        raise PhraseDataError("Phrase data must be a JSON list of records.")

    normalized: List[dict] = []
    seen: Dict[Tuple[str, str], int] = {}
    errors: List[str] = []

    for index, raw in enumerate(records, start=1):
        if not isinstance(raw, dict):
            errors.append(f"Record {index}: expected an object.")
            continue
        missing = sorted(REQUIRED_PHRASE_FIELDS - raw.keys())
        if missing:
            errors.append(f"Record {index}: missing {', '.join(missing)}.")
            continue

        word1 = _normalize_phrase_token(raw.get("word1"))
        word2 = _normalize_phrase_token(raw.get("word2"))
        if not WORD_RE.fullmatch(word1) or not WORD_RE.fullmatch(word2):
            errors.append(f"Record {index}: word1 and word2 must contain letters only.")
            continue
        key = (word1, word2)
        if key in seen:
            errors.append(f"Record {index}: duplicate ordered pair '{word1} {word2}' (first at record {seen[key]}).")
            continue
        seen[key] = index

        roles = raw.get("roles")
        explanations = raw.get("role_explanations")
        if not isinstance(roles, list) or len(roles) != 2:
            errors.append(f"Record {index}: roles must contain exactly two values.")
            continue
        roles = [_normalize_phrase_token(role) for role in roles]
        if any(role not in ALLOWED_ROLES for role in roles):
            errors.append(f"Record {index}: unsupported role in {roles}.")
            continue
        if not isinstance(explanations, list) or len(explanations) != 2 or not all(str(x).strip() for x in explanations):
            errors.append(f"Record {index}: role_explanations must contain two non-empty strings.")
            continue

        phrase = str(raw.get("phrase") or "").strip()
        category = str(raw.get("category") or "").strip()
        meaning = str(raw.get("meaning") or "").strip()
        example = str(raw.get("example") or "").strip()
        if not all((phrase, category, meaning, example)):
            errors.append(f"Record {index}: phrase, category, meaning, and example are required.")
            continue

        normalized.append({
            "word1": word1,
            "word2": word2,
            "phrase": phrase,
            "category": category,
            "roles": roles,
            "role_explanations": [str(x).strip() for x in explanations],
            "meaning": meaning,
            "example": example,
            "verified": bool(raw.get("verified")),
            "difficulty": str(raw.get("difficulty") or "").strip() or None,
            "enabled_for_random": bool(raw.get("enabled_for_random", False)),
            "known_solutions": [str(x).strip().lower() for x in raw.get("known_solutions", []) if str(x).strip()],
        })

    if errors:
        raise PhraseDataError("Invalid phrase data:\n- " + "\n- ".join(errors))
    if not normalized:
        raise PhraseDataError("Phrase data contains no usable records.")
    return normalized


@lru_cache(maxsize=4)
def load_phrase_records(path: Optional[str] = None) -> Tuple[dict, ...]:
    """Load the validated phrase bank from JSON, with an environment override."""
    resolved = Path(path or os.getenv(PHRASE_DATA_ENV, str(DEFAULT_PHRASE_DATA_PATH))).expanduser().resolve()
    if not resolved.exists():
        raise PhraseDataError(f"Phrase data file was not found: {resolved}")
    try:
        raw = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PhraseDataError(f"Phrase data is not valid JSON: {exc}") from exc
    return tuple(validate_phrase_records(raw))


def build_phrase_metadata(records: Optional[Tuple[dict, ...]] = None) -> Dict[Tuple[str, str], dict]:
    source = records or load_phrase_records()
    return {
        (record["word1"], record["word2"]): {
            "phrase_label": record["phrase"],
            "category": record["category"],
            "roles": tuple(record["roles"]),
            "role_explanations": tuple(record["role_explanations"]),
            "meaning": record["meaning"],
            "example": record["example"],
            "verified": record["verified"],
            "difficulty": record.get("difficulty"),
            "enabled_for_random": record.get("enabled_for_random", False),
            "known_solutions": tuple(record.get("known_solutions", [])),
        }
        for record in source
    }


PHRASE_RECORDS = load_phrase_records()
PHRASE_METADATA = build_phrase_metadata(PHRASE_RECORDS)
PHRASES = [
    (record["word1"], record["word2"], record["phrase"])
    for record in PHRASE_RECORDS
    if record.get("verified", False) and record.get("enabled_for_random", False)
]


def phrase_bank_stats() -> dict:
    """Return predictable summary information for the Admin UI."""
    categories = Counter(record["category"] for record in PHRASE_RECORDS)
    return {
        "total_records": len(PHRASE_RECORDS),
        "verified_records": sum(1 for record in PHRASE_RECORDS if record.get("verified")),
        "random_enabled_records": sum(1 for record in PHRASE_RECORDS if record.get("enabled_for_random")),
        "categories": dict(sorted(categories.items())),
        "data_path": str(Path(os.getenv(PHRASE_DATA_ENV, str(DEFAULT_PHRASE_DATA_PATH))).expanduser().resolve()),
    }


FALLBACK_WORDS = {
    "already", "aerial", "ready", "layer", "relay", "daily", "dearly",
    "straw", "last", "stall", "walls", "swat", "salt", "warts",
    "never", "lever", "nerve", "wrong", "grown", "word", "row",
    "feet", "fete", "lining", "silver", "prime", "time", "course",
    "crash", "metal", "heavy", "talk", "small", "green", "light",
    "black", "sheep", "early", "bird", "final", "first", "hand",
    "wheaten", "kneeler",
}


@dataclass(frozen=True)
class Puzzle:
    word1: str
    word2: str
    phrase_label: str

    @property
    def letters(self) -> Counter:
        return Counter(self.word1 + self.word2)

    @property
    def total_len(self) -> int:
        return len(self.word1) + len(self.word2)


def normalize_word(value: str) -> str:
    return (value or "").strip().lower()


def make_puzzle(word1: str, word2: str, phrase_label: Optional[str] = None) -> Puzzle:
    w1 = normalize_word(word1)
    w2 = normalize_word(word2)
    if not w1 or not w2:
        raise ValueError("Enter both words.")
    if not WORD_RE.fullmatch(w1) or not WORD_RE.fullmatch(w2):
        raise ValueError("Puzzle words must contain letters only.")
    if w1 == w2:
        raise ValueError("The two puzzle words must be different.")
    label = (phrase_label or f"{w1} {w2}").strip()
    return Puzzle(w1, w2, label)


def get_phrase_metadata(puzzle: Puzzle) -> Optional[dict]:
    """Return curated phrase metadata for the exact ordered word pair."""
    metadata = PHRASE_METADATA.get((normalize_word(puzzle.word1), normalize_word(puzzle.word2)))
    if not metadata:
        return None
    result = dict(metadata)
    result.update({
        "source": "curated",
        "confidence": 1.0,
        "confidence_band": "curated",
        "rule_id": "CURATED_METADATA",
        "rule_label": "Curated phrase metadata",
        "reasoning": "Verified phrase metadata is used as the authoritative grammar key.",
        "inferred": False,
    })
    return result


_COMMON_VERBS = {
    "am", "are", "be", "been", "being", "came", "come", "comes", "did", "do", "does",
    "done", "gave", "get", "gets", "go", "goes", "gone", "got", "had", "has", "have",
    "made", "make", "makes", "ran", "run", "runs", "said", "saw", "see", "seen", "take",
    "takes", "took", "went", "were", "was", "work", "worked", "working",
}
_COMMON_AUXILIARIES = {
    "am", "are", "be", "been", "being", "can", "could", "did", "do", "does", "had",
    "has", "have", "is", "may", "might", "must", "shall", "should", "was", "were",
    "will", "would",
}
_COMMON_ADVERB_PARTICLES = {
    "about", "across", "ahead", "along", "around", "away", "back", "by", "down", "forth",
    "forward", "in", "off", "on", "out", "over", "through", "together", "up",
}
_COMMON_ADJECTIVES = {
    "big", "black", "blue", "bright", "cold", "dark", "early", "fast", "final", "first",
    "green", "hard", "heavy", "high", "hot", "last", "light", "little", "long", "new",
    "old", "open", "quick", "red", "short", "silver", "small", "white", "young",
}
_COMMON_DETERMINERS = {"a", "an", "another", "each", "either", "every", "neither", "no", "some", "the", "this", "that", "these", "those"}
_COMMON_PRONOUNS = {"he", "her", "hers", "him", "his", "i", "it", "its", "me", "mine", "our", "ours", "she", "their", "theirs", "them", "they", "us", "we", "you", "your", "yours"}
_COMMON_PREPOSITIONS = {"at", "before", "behind", "below", "beneath", "beside", "between", "for", "from", "into", "near", "of", "on", "onto", "over", "to", "under", "with", "without"}
_COMMON_CONJUNCTIONS = {"and", "although", "because", "but", "if", "nor", "or", "since", "so", "though", "unless", "until", "when", "while", "yet"}
_COMMON_ADVERBS = {"again", "almost", "always", "ever", "far", "here", "never", "now", "often", "once", "soon", "still", "then", "there", "today", "too", "very", "well", "yesterday"}
_ADJECTIVE_SUFFIXES = ("able", "al", "ary", "ful", "ible", "ic", "ical", "ish", "ive", "less", "ous", "y")
_VERB_SUFFIXES = ("ate", "en", "ify", "ise", "ize")


def _role_explanation(word: str, role: str, other_word: str, position: int) -> str:
    if role == "verb":
        return f"‘{word.title()}’ expresses the action or state in this phrase, so it functions as a verb."
    if role == "auxiliary":
        return f"‘{word.title()}’ helps form the verb phrase, so it functions as an auxiliary."
    if role == "adjective":
        return f"‘{word.title()}’ describes or modifies ‘{other_word}’, so it functions as an adjective."
    if role == "adverb":
        return f"‘{word.title()}’ modifies the action, direction, degree, or manner in the phrase, so it functions as an adverb or verbal particle."
    if role == "noun":
        return f"‘{word.title()}’ names a person, place, thing, idea, or event in this phrase, so it functions as a noun."
    if role == "proper noun":
        return f"‘{word.title()}’ names a specific person, place, or entity, so it functions as a proper noun."
    if role == "preposition":
        return f"‘{word.title()}’ introduces a relationship to another element, so it functions as a preposition."
    if role == "determiner":
        return f"‘{word.title()}’ introduces or limits the noun that follows, so it functions as a determiner."
    if role == "pronoun":
        return f"‘{word.title()}’ stands in for a noun or noun phrase, so it functions as a pronoun."
    if role == "conjunction":
        return f"‘{word.title()}’ connects words or ideas, so it functions as a conjunction."
    return f"‘{word.title()}’ is inferred to function as a {role} in this two-word context."


def _looks_adjective(word: str) -> bool:
    return word in _COMMON_ADJECTIVES or (len(word) > 4 and word.endswith(_ADJECTIVE_SUFFIXES))


def _looks_verb(word: str) -> bool:
    return word in _COMMON_VERBS or word in _COMMON_AUXILIARIES or word.endswith(("ed", "ing")) or (len(word) > 4 and word.endswith(_VERB_SUFFIXES))


@lru_cache(maxsize=2048)
def _infer_roles_cached(word1: str, word2: str) -> dict:
    """Infer roles for a two-word phrase without external NLP dependencies.

    The engine is deliberately conservative. Curated phrase metadata always takes
    precedence; this function is only used for unknown manual phrases.
    """
    w1, w2 = word1.lower(), word2.lower()

    if w1 in _COMMON_AUXILIARIES and _looks_verb(w2):
        roles, confidence = ("auxiliary", "verb"), 0.86
        rule_id = "AUX_PLUS_VERB"
        rule_label = "Auxiliary + verb"
        reasoning = f"‘{w1}’ is a known auxiliary and ‘{w2}’ has a verb form."
    elif _looks_verb(w1) and w2 in _COMMON_ADVERB_PARTICLES:
        roles, confidence = ("verb", "adverb"), 0.94
        rule_id = "VERB_PLUS_PARTICLE"
        rule_label = "Verb + adverbial particle"
        reasoning = f"‘{w1}’ is recognized as a verb and ‘{w2}’ is a common phrasal-verb particle or directional adverb."
    elif w1 in _COMMON_DETERMINERS:
        roles, confidence = ("determiner", "noun"), 0.90
        rule_id = "DETERMINER_PLUS_NOUN"
        rule_label = "Determiner + noun"
        reasoning = f"‘{w1}’ is a determiner, so the following word is treated as the noun it introduces."
    elif w1 in _COMMON_PRONOUNS and _looks_verb(w2):
        roles, confidence = ("pronoun", "verb"), 0.88
        rule_id = "PRONOUN_PLUS_VERB"
        rule_label = "Pronoun + verb"
        reasoning = f"‘{w1}’ is a pronoun and ‘{w2}’ matches a common verb form."
    elif w1 in _COMMON_PREPOSITIONS:
        roles, confidence = ("preposition", "noun"), 0.74
        rule_id = "PREPOSITION_PLUS_NOUN"
        rule_label = "Preposition + nominal complement"
        reasoning = f"‘{w1}’ is a preposition; the second word is conservatively treated as its nominal complement."
    elif w1 in _COMMON_CONJUNCTIONS:
        roles, confidence = ("conjunction", "other"), 0.62
        rule_id = "CONJUNCTION_FALLBACK"
        rule_label = "Conjunction fallback"
        reasoning = f"‘{w1}’ is a conjunction, but the role of ‘{w2}’ cannot be determined confidently from two words alone."
    elif _looks_adjective(w1):
        roles, confidence = ("adjective", "noun"), 0.91
        rule_id = "ADJECTIVE_PLUS_NOUN"
        rule_label = "Adjective + noun"
        reasoning = f"‘{w1}’ matches a known adjective or adjective suffix and appears before ‘{w2}’, which it likely modifies."
    elif w1.endswith("ly") or w1 in _COMMON_ADVERBS:
        second_role = "adjective" if _looks_adjective(w2) else "verb" if _looks_verb(w2) else "adjective"
        roles, confidence = ("adverb", second_role), 0.72
        rule_id = "ADVERB_MODIFIER"
        rule_label = "Adverb modifier"
        reasoning = f"‘{w1}’ matches a common adverb pattern and is interpreted as modifying ‘{w2}’."
    elif _looks_verb(w1):
        roles, confidence = ("verb", "noun"), 0.66
        rule_id = "VERB_PLUS_OBJECT_FALLBACK"
        rule_label = "Verb + possible object"
        reasoning = f"‘{w1}’ resembles a verb; ‘{w2}’ is tentatively treated as its object or complement."
    elif _looks_verb(w2):
        roles, confidence = ("noun", "verb"), 0.65
        rule_id = "SUBJECT_PLUS_VERB_FALLBACK"
        rule_label = "Possible subject + verb"
        reasoning = f"‘{w2}’ resembles a verb; ‘{w1}’ is tentatively treated as a nominal subject."
    else:
        roles, confidence = ("noun", "noun"), 0.54
        rule_id = "NOUN_NOUN_FALLBACK"
        rule_label = "Conservative noun + noun fallback"
        reasoning = "No stronger lexical or suffix rule matched, so both words are conservatively treated as nouns."

    if confidence >= 0.90:
        confidence_band = "high"
    elif confidence >= 0.70:
        confidence_band = "medium"
    else:
        confidence_band = "low"

    explanations = (
        _role_explanation(w1, roles[0], w2, 0),
        _role_explanation(w2, roles[1], w1, 1),
    )
    return {
        "roles": roles,
        "role_explanations": explanations,
        "source": "built-in grammar engine",
        "confidence": confidence,
        "confidence_band": confidence_band,
        "rule_id": rule_id,
        "rule_label": rule_label,
        "reasoning": reasoning,
        "inferred": True,
    }


def get_contextual_phrase_metadata(puzzle: Puzzle) -> dict:
    """Return curated metadata or an inferred contextual grammar analysis."""
    curated = get_phrase_metadata(puzzle)
    if curated:
        return curated
    inferred = dict(_infer_roles_cached(normalize_word(puzzle.word1), normalize_word(puzzle.word2)))
    inferred.update({
        "phrase_label": puzzle.phrase_label,
        "category": "automatically analyzed",
        "meaning": None,
        "example": None,
        "verified": False,
    })
    return inferred


def grade_word_roles(
    puzzle: Puzzle,
    selected_role1: str,
    selected_role2: str,
    points_per_role: int = 5,
) -> dict:
    """Grade contextual parts of speech and return explanations plus a 0–10 bonus."""
    metadata = get_contextual_phrase_metadata(puzzle)

    expected = metadata["roles"]
    explanations = metadata["role_explanations"]
    selected = (normalize_word(selected_role1), normalize_word(selected_role2))
    words = (puzzle.word1, puzzle.word2)
    items = []
    correct_count = 0
    for word, chosen, correct, explanation in zip(words, selected, expected, explanations):
        ok = chosen == correct
        correct_count += int(ok)
        items.append({
            "word": word,
            "selected": chosen,
            "correct_role": correct,
            "ok": ok,
            "explanation": explanation,
        })

    points_per_role = max(0, int(points_per_role))
    confidence = float(metadata.get("confidence", 1.0))
    inferred = bool(metadata.get("inferred", False))
    bonus_eligible = (not inferred) or confidence >= 0.70
    awarded_points = correct_count * points_per_role if bonus_eligible else 0
    return {
        "available": True,
        "correct_count": correct_count,
        "total_roles": 2,
        "points": awarded_points,
        "raw_points": correct_count * points_per_role,
        "bonus_eligible": bonus_eligible,
        "bonus_withheld_reason": (
            None if bonus_eligible else
            "The automatic grammar analysis is low confidence, so role credit is withheld until the phrase is curated."
        ),
        "max_points": 2 * points_per_role,
        "items": items,
        "meaning": metadata.get("meaning"),
        "example": metadata.get("example"),
        "source": metadata.get("source", "curated"),
        "confidence": confidence,
        "confidence_band": metadata.get("confidence_band", "curated"),
        "rule_id": metadata.get("rule_id"),
        "rule_label": metadata.get("rule_label"),
        "reasoning": metadata.get("reasoning"),
        "inferred": inferred,
    }


def starts_with_vowel(word: str) -> bool:
    word = normalize_word(word)
    return bool(word) and word[0] in VOWELS


def contains_input_word_as_is(solution: str, word1: str, word2: str) -> bool:
    solution = normalize_word(solution)
    return normalize_word(word1) in solution or normalize_word(word2) in solution


def can_build_from_letters(candidate: str, letters: Counter) -> Tuple[bool, Dict[str, int]]:
    need = Counter(normalize_word(candidate))
    overuse = {ch: count - letters.get(ch, 0) for ch, count in need.items() if count > letters.get(ch, 0)}
    return not overuse, overuse


def puzzle_id_from_words(
    word1: str,
    word2: str,
    len_a: Optional[int] = None,
    len_b: Optional[int] = None,
    day: Optional[date] = None,
    mode: Optional[str] = None,
) -> str:
    a, b = sorted([normalize_word(word1), normalize_word(word2)])
    parts = [a, b]
    if len_a is not None and len_b is not None:
        parts.append(f"{int(len_a)}x{int(len_b)}")
    if mode:
        parts.append(mode.lower())
    if day:
        parts.append(day.isoformat())
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


def _matching_phrases(len_a: int, len_b: int, allow_swap: bool) -> List[tuple]:
    return [
        item for item in PHRASES
        if (len(item[0]) == len_a and len(item[1]) == len_b)
        or (allow_swap and len(item[0]) == len_b and len(item[1]) == len_a)
    ]


def pick_puzzle(len_a: int = 5, len_b: int = 4, allow_swap: bool = True) -> Puzzle:
    candidates = _matching_phrases(len_a, len_b, allow_swap)
    if not candidates:
        raise ValueError(f"No phrase is available for {len_a}+{len_b}. Enter your own words or change the lengths.")
    return make_puzzle(*random.choice(candidates))


def pick_daily_puzzle(day: date, len_a: int = 5, len_b: int = 4, allow_swap: bool = True) -> Puzzle:
    candidates = _matching_phrases(len_a, len_b, allow_swap)
    if not candidates:
        raise ValueError(f"No daily phrase is available for {len_a}+{len_b}.")
    seed = int(hashlib.sha256(day.isoformat().encode("utf-8")).hexdigest()[:8], 16)
    return make_puzzle(*random.Random(seed).choice(candidates))


@lru_cache(maxsize=8)
def load_wordlist(max_n: int = 200_000) -> Tuple[str, ...]:
    try:
        from wordfreq import top_n_list  # type: ignore
        return tuple(w.lower() for w in top_n_list("en", max_n) if WORD_RE.fullmatch(w))
    except Exception:
        return tuple(sorted(FALLBACK_WORDS))


def is_valid_english_word(word: str, min_zipf: float = 2.0) -> bool:
    word = normalize_word(word)
    if not WORD_RE.fullmatch(word):
        return False
    try:
        from wordfreq import zipf_frequency  # type: ignore
        return zipf_frequency(word, "en") >= min_zipf
    except Exception:
        return word in FALLBACK_WORDS


def grade_solution(
    puzzle: Puzzle,
    solution: str,
    min_letters_used: Optional[int] = None,
    require_english: bool = True,
) -> dict:
    raw = (solution or "").strip()
    if not raw:
        return {"ok": False, "solution": "", "raw_input": raw, "reason": "Empty solution."}
    if not WORD_RE.fullmatch(raw):
        return {"ok": False, "solution": normalize_word(raw), "raw_input": raw, "reason": "Solutions must contain letters only."}

    sol = raw.lower()
    if contains_input_word_as_is(sol, puzzle.word1, puzzle.word2):
        return {"ok": False, "solution": sol, "raw_input": raw, "reason": "Solution contains a complete input word as a substring."}

    letters_ok, overuse = can_build_from_letters(sol, puzzle.letters)
    if not letters_ok:
        return {
            "ok": False,
            "solution": sol,
            "raw_input": raw,
            "reason": "Uses unavailable letters or too many copies of a letter.",
            "overuse": overuse,
        }

    consonant_min = max(1, puzzle.total_len - 2) if min_letters_used is None else max(1, int(min_letters_used))
    vowel = starts_with_vowel(sol)
    effective_min = max(1, consonant_min - 1) if vowel else consonant_min
    if len(sol) < effective_min:
        return {
            "ok": False,
            "solution": sol,
            "raw_input": raw,
            "reason": f"Too short. Minimum is {effective_min} letters for this solution.",
            "len": len(sol),
            "min_required": effective_min,
            "starts_with_vowel": vowel,
        }

    if require_english and not is_valid_english_word(sol):
        return {"ok": False, "solution": sol, "raw_input": raw, "reason": "Not recognized as an English word.", "starts_with_vowel": vowel}

    if len(sol) >= 8:
        score = 90
    elif len(sol) == 7:
        score = 85 if vowel else 80
    elif len(sol) == 6 and vowel:
        score = 75
    else:
        score = min(90, 70 + 2 * len(sol))

    return {
        "ok": True,
        "solution": sol,
        "raw_input": raw,
        "len": len(sol),
        "min_required": effective_min,
        "starts_with_vowel": vowel,
        "score_base": score,
        "score_final": score,
    }


def grade_bonus_phrase(solution: str, bonus_phrase: str) -> dict:
    sol = normalize_word(solution)
    text = (bonus_phrase or "").strip()
    if not sol or not text:
        return {"ok": False, "reason": "No bonus sentence or solution was provided."}
    matched = bool(re.search(rf"(?<![A-Za-z]){re.escape(sol)}(?![A-Za-z])", text, flags=re.IGNORECASE))
    return {"ok": matched, "reason": "Contains the solution as a standalone word." if matched else "The solution is not an exact standalone word."}


def apply_bonus_score(grade: dict, bonus_phrase: str) -> dict:
    result = dict(grade)
    if not result.get("ok"):
        return result
    bonus = grade_bonus_phrase(result["solution"], bonus_phrase)
    result["bonus"] = bonus
    result["score_final"] = 95 if bonus.get("ok") else result.get("score_base", 0)
    return result


def explain_solution(puzzle: Puzzle, grade: dict) -> dict:
    if not grade.get("ok"):
        return {}
    used = Counter(grade["solution"])
    remaining = puzzle.letters - used
    reasons = []
    if grade.get("score_final") == 95:
        reasons.append("Bonus applied because the solution appears as an exact standalone word.")
    elif grade["len"] >= 8:
        reasons.append("Eight or more letters earns 90 points.")
    elif grade["len"] == 7 and grade.get("starts_with_vowel"):
        reasons.append("Seven letters beginning with a vowel earns 85 points.")
    elif grade["len"] == 7:
        reasons.append("Seven letters beginning with a consonant earns 80 points.")
    elif grade["len"] == 6 and grade.get("starts_with_vowel"):
        reasons.append("Six letters beginning with a vowel earns 75 points.")
    return {
        "solution": grade["solution"],
        "base_score": grade.get("score_base"),
        "final_score": grade.get("score_final", grade.get("score_base")),
        "score_reason": reasons,
        "letters_used": dict(sorted(used.items())),
        "letters_remaining": dict(sorted(remaining.items())),
        "rule_checks": [
            "Used only available letters and respected letter frequency",
            "Did not contain either complete input word",
            "Met the applicable minimum length",
            "Passed the configured dictionary rule",
        ],
    }



def explain_answer_attempt(
    puzzle: Puzzle,
    grade: dict,
    min_letters_used: Optional[int] = None,
    require_english: bool = True,
    bonus_phrase: str = "",
) -> dict:
    """Return a transparent, rule-by-rule explanation for any submitted answer."""
    raw = str(grade.get("raw_input", grade.get("solution", "")) or "")
    normalized = normalize_word(raw)
    consonant_min = max(1, puzzle.total_len - 2) if min_letters_used is None else max(1, int(min_letters_used))
    vowel = starts_with_vowel(normalized)
    effective_min = max(1, consonant_min - 1) if vowel else consonant_min

    alpha_ok = bool(raw.strip()) and bool(WORD_RE.fullmatch(raw.strip()))
    forbidden = contains_input_word_as_is(normalized, puzzle.word1, puzzle.word2) if normalized else False
    letters_ok, overuse = can_build_from_letters(normalized, puzzle.letters) if normalized else (False, {})
    length_ok = bool(normalized) and len(normalized) >= effective_min
    dictionary_ok = bool(normalized) and (not require_english or is_valid_english_word(normalized))

    used = Counter(normalized)
    remaining = puzzle.letters - used
    shortages = []
    for letter, excess in sorted(overuse.items()):
        requested = used.get(letter, 0)
        available = puzzle.letters.get(letter, 0)
        shortages.append(
            f"Used {requested} {letter.upper()}'s, but only {available} {'is' if available == 1 else 'are'} available."
        )

    checks = [
        {
            "key": "input",
            "label": "Letters-only input",
            "passed": alpha_ok,
            "detail": "The answer contains letters only." if alpha_ok else "Enter one non-empty word containing letters only.",
        },
        {
            "key": "substring",
            "label": "Input-word substring rule",
            "passed": bool(normalized) and not forbidden,
            "detail": (
                f"The answer does not contain '{puzzle.word1}' or '{puzzle.word2}' as a complete substring."
                if normalized and not forbidden
                else f"The answer contains '{puzzle.word1}' or '{puzzle.word2}' as a complete substring."
            ),
        },
        {
            "key": "letters",
            "label": "Available-letter frequency",
            "passed": letters_ok,
            "detail": (
                "Every used letter is available in the phrase in sufficient quantity."
                if letters_ok
                else " ".join(shortages) or "The answer cannot be built from the available letters."
            ),
        },
        {
            "key": "length",
            "label": "Minimum length",
            "passed": length_ok,
            "detail": (
                f"Uses {len(normalized)} letters; the applicable minimum is {effective_min}."
                + (" The one-letter vowel-start exception applies." if vowel else "")
            ),
        },
        {
            "key": "dictionary",
            "label": "English-word check",
            "passed": dictionary_ok,
            "detail": (
                "Dictionary checking is disabled for this puzzle."
                if not require_english
                else ("Recognized as an English word." if dictionary_ok else "Not recognized by the configured English dictionary.")
            ),
        },
    ]

    bonus = grade.get("bonus") or grade_bonus_phrase(normalized, bonus_phrase)
    if grade.get("ok"):
        checks.append({
            "key": "bonus",
            "label": "Exact-word bonus",
            "passed": bool(bonus.get("ok")),
            "detail": bonus.get("reason", "No bonus sentence was provided."),
        })

    return {
        "raw_input": raw,
        "solution": normalized,
        "valid": bool(grade.get("ok")),
        "summary": (
            f"'{normalized}' passes all required forging rules."
            if grade.get("ok")
            else grade.get("reason", "The answer did not pass all forging rules.")
        ),
        "checks": checks,
        "starts_with_vowel": vowel,
        "length": len(normalized),
        "consonant_minimum": consonant_min,
        "effective_minimum": effective_min,
        "letters_used": dict(sorted(used.items())),
        "letters_remaining": dict(sorted(remaining.items())),
        "overuse": dict(sorted(overuse.items())),
        "base_score": grade.get("score_base"),
        "word_score": grade.get("word_score", grade.get("score_final", grade.get("score_base"))),
        "role_bonus": grade.get("role_bonus", 0),
        "combined_score": grade.get("combined_score", grade.get("score_final", grade.get("score_base"))),
    }

def all_valid_solutions(
    puzzle: Puzzle,
    min_consonant_len: Optional[int] = None,
    require_english: bool = True,
    max_words: int = 200_000,
    limit: int = 2000,
) -> List[dict]:
    results: List[dict] = []
    for word in load_wordlist(max_words):
        grade = grade_solution(puzzle, word, min_consonant_len, require_english)
        if grade.get("ok"):
            results.append(grade)
    results.sort(key=lambda x: (x.get("score_base", 0), x.get("len", 0), x["solution"]), reverse=True)
    return results[: max(1, limit)]


def build_validated_hint_candidates(
    puzzle: Puzzle,
    min_letters_used: int,
    require_english: bool = True,
    limit: int = 200,
) -> List[dict]:
    candidates = all_valid_solutions(puzzle, min_letters_used, require_english, limit=limit)
    return [
        result for result in candidates
        if grade_solution(puzzle, result["solution"], min_letters_used, require_english).get("ok")
    ]


def create_progressive_hint(candidates: List[dict], hint_level: int, previously_used: Set[str]) -> dict:
    """Create increasingly revealing hints from one fully validated solution."""
    if not candidates:
        return {"id": "none", "type": "none", "text": "No validated hint candidate exists for this puzzle and rule configuration."}

    candidate = next((c for c in candidates if c["solution"] not in previously_used), candidates[0])
    solution = candidate["solution"]
    level = max(0, min(int(hint_level), 7))
    vowel_count = sum(ch in VOWELS for ch in solution)
    consonant_count = len(solution) - vowel_count
    useful = next((ch for ch in solution[1:] if ch not in VOWELS), solution[-1])
    pattern = solution[0].upper() + " " + " ".join("_" for _ in solution[1:])
    hints = [
        ("strategy", "Try building a word that uses nearly all of the available letters."),
        ("start_type", f"A validated solution begins with a **{'vowel' if starts_with_vowel(solution) else 'consonant'}**."),
        ("length", f"A validated solution has **{len(solution)} letters**."),
        ("distribution", f"It contains **{vowel_count} vowel{'s' if vowel_count != 1 else ''}** and **{consonant_count} consonant{'s' if consonant_count != 1 else ''}**."),
        ("useful_letter", f"One validated solution contains the letter **{useful.upper()}**."),
        ("first_letter", f"The first letter is **{solution[0].upper()}**."),
        ("pattern", f"Pattern: **{pattern}**"),
        ("reveal", f"Validated solution: **{solution.upper()}**"),
    ]
    hint_type, text = hints[level]
    return {"id": f"{solution}:{hint_type}", "type": hint_type, "text": text, "solution": solution}


def difficulty_from_solution_count(count: int) -> str:
    if count <= 10:
        return "Expert"
    if count <= 50:
        return "Hard"
    if count <= 200:
        return "Medium"
    return "Easy"


def compute_difficulty(puzzle: Puzzle, min_consonant_len: int, max_words: int = 200_000) -> dict:
    solutions = all_valid_solutions(puzzle, min_consonant_len, True, max_words=max_words, limit=5000)
    return {"solutions_found": len(solutions), "tier": difficulty_from_solution_count(len(solutions)), "capped_at": 5000}
