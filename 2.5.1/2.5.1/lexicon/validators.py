from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional
from .name_policy import COMMON_SENSES, extra_names

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

# Editorial name blocks supplement the bundled name corpus.
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

    Profiles control *rarity*. Proper names are excluded unless the explicit _names mode is selected.
    Pronouns remain excluded. Curated accepted overrides can rescue legitimate low-frequency
    English words discovered during beta testing.
    """
    normalized = (word or "").strip().lower()
    requested = (profile or DEFAULT_PROFILE).lower()
    allow_names = requested in {name + "_names" for name in _profiles()}
    profile_name, profile_cfg = _profile(requested[:-6] if allow_names else requested)
    result = {
        "word": normalized,
        "profile": requested if allow_names else profile_name,
        "allow_names": allow_names,
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
    reason = blocked.get(normalized)
    if normalized in PRONOUNS or (reason and reason != "proper_name"):
        reason = "pronoun" if normalized in PRONOUNS else str(reason)
        result.update(reason=reason, category=reason, source="curated_block")
        return result

    # Explicit editorial common senses take precedence over name matches.
    # The existing curated accepted overrides are also ordinary-word evidence.
    common = COMMON_SENSES.get(normalized)
    curated = data.get("accepted_overrides", {}).get(normalized)
    is_name = (reason == "proper_name" or normalized in _proper_names()
               or normalized in extra_names()) and not (common or curated)
    if is_name:
        result.update(accepted=allow_names, reason=None if allow_names else "proper_name",
                      category="proper_name", source="pfl_name_policy",
                      part_of_speech=["proper noun"],
                      definition="Recognized name or place; not an ordinary-word solution.")
        return result
    if common and not curated:
        result.update(accepted=True, category="english_word", source="curated_common_sense",
                      definition=common)
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
