from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
WORD_RE = re.compile(r"^[a-z]+$")
DEFAULT_PROFILE = os.getenv("PHRASE_FORGE_LEXICON_PROFILE", "standard").strip().lower() or "standard"

# Gameplay exclusions are profile-independent. Expert/Teacher broaden rarity,
# not grammatical-function words or proper names.
PRONOUNS = {
    # personal / possessive
    "i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself",
    "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themself", "themselves",
    # demonstrative / relative / interrogative
    "this", "that", "these", "those", "who", "whom", "whose", "which", "what",
    "whoever", "whomever", "whichever", "whatever",
    # indefinite / reciprocal
    "anybody", "anyone", "anything", "each", "either", "everybody", "everyone", "everything",
    "neither", "nobody", "none", "noone", "nothing", "one", "ones", "oneself", "other",
    "others", "somebody", "someone", "something", "both", "few", "many", "several",
    "all", "any", "most", "some", "another", "eachother", "oneanother",
}

# Explicit blocks are authoritative even when a token also has a high corpus
# frequency. The broader proper-name corpus below uses a conservative frequency
# gate so ordinary English words that are also names (mark, rose, grant, etc.)
# are not automatically removed from gameplay.
EXPLICIT_PROPER_NAMES = {
    "ishtar", "ishant",
}


@lru_cache(maxsize=1)
def _profiles() -> dict:
    return json.loads((ROOT / "profiles.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _overrides() -> dict:
    return json.loads((ROOT / "phrase_forge_lexicon.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _proper_names() -> frozenset[str]:
    path = ROOT / "proper_names.txt"
    if not path.exists():
        return frozenset(EXPLICIT_PROPER_NAMES)
    names = {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and WORD_RE.fullmatch(line.strip().lower())
    }
    names.update(EXPLICIT_PROPER_NAMES)
    return frozenset(names)


def available_profiles() -> dict:
    return dict(_profiles())


def _profile(name: Optional[str]) -> tuple[str, dict]:
    requested = (name or DEFAULT_PROFILE).strip().lower()
    profiles = _profiles()
    if requested not in profiles:
        requested = "standard"
    return requested, profiles[requested]


def _frequency_band(zipf: float) -> str:
    if zipf >= 5.0:
        return "very_common"
    if zipf >= 3.5:
        return "common"
    if zipf >= 2.0:
        return "less_common"
    return "rare"


def lexicon_info(word: str, profile: Optional[str] = None) -> dict:
    """Return the authoritative Phrase Forge Lexicon decision.

    This function is the single gameplay acceptance policy used by direct
    grading, solver output, hints, difficulty, AI puzzle validation, Show All
    Solutions and Admin diagnostics.

    Profiles control *rarity*. Proper names and pronouns remain excluded in all
    profiles. Curated accepted overrides can rescue legitimate low-frequency
    English words discovered during beta testing.
    """
    normalized = (word or "").strip().lower()
    profile_name, profile_cfg = _profile(profile)
    result = {
        "word": normalized,
        "profile": profile_name,
        "accepted": False,
        "source": "phrase_forge_lexicon",
        "reason": None,
        "category": None,
        "frequency": None,
        "zipf": None,
        "part_of_speech": [],
        "definition": None,
    }
    if not normalized or not WORD_RE.fullmatch(normalized):
        result["reason"] = "not_alpha"
        return result

    data = _overrides()
    blocked = data.get("blocked_words", {})
    if normalized in blocked:
        reason = str(blocked[normalized])
        result.update({"reason": reason, "category": reason, "source": "curated_block"})
        return result

    # Pronouns are never gameplay words, regardless of profile.
    if normalized in PRONOUNS:
        result.update({"reason": "pronoun", "category": "pronoun", "source": "pfl_grammar_exclusion"})
        return result

    # Explicit proper-name blocks are never gameplay words.
    if normalized in EXPLICIT_PROPER_NAMES:
        result.update({"reason": "proper_name", "category": "proper_name", "source": "pfl_proper_name_exclusion"})
        return result

    override = data.get("accepted_overrides", {}).get(normalized)
    if override:
        allowed_profiles = override.get("profiles", ["standard", "expert", "teacher"])
        accepted = profile_name in allowed_profiles
        result.update({
            "accepted": accepted,
            "source": "curated_override",
            "reason": None if accepted else "profile_excluded",
            "category": "curated_word",
            "frequency": override.get("frequency"),
            "part_of_speech": list(override.get("part_of_speech", [])),
            "definition": override.get("definition"),
        })
        return result

    try:
        from wordfreq import zipf_frequency  # type: ignore
        zipf = float(zipf_frequency(normalized, "en"))
    except Exception:
        result["reason"] = "dictionary_unavailable"
        return result

    result["zipf"] = zipf
    result["frequency"] = _frequency_band(zipf) if zipf > 0 else None

    if zipf <= 0:
        result["reason"] = "not_recognized"
        return result

    # Names from the bundled multi-locale first-name corpus are blocked when
    # they are not common enough to plausibly be ordinary English vocabulary.
    # This catches tokens such as Ishant without rejecting words like mark,
    # rose, grant, hope, bill, or will merely because they can also be names.
    name_max_zipf = float(profile_cfg.get("proper_name_max_zipf", 3.5))
    if normalized in _proper_names() and zipf < name_max_zipf:
        result.update({
            "reason": "proper_name",
            "category": "proper_name",
            "source": "pfl_proper_name_corpus",
        })
        return result

    if zipf < float(profile_cfg.get("min_zipf", 2.0)):
        result["reason"] = "too_rare_for_profile"
        return result

    result.update({
        "accepted": True,
        "source": "wordfreq+pfl",
        "category": "english_word",
        "reason": None,
    })
    return result


def word_allowed(word: str, profile: Optional[str] = None) -> bool:
    """Return the final PFL gameplay acceptance decision."""
    return bool(lexicon_info(word, profile).get("accepted"))
