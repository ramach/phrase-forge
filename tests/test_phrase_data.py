import json
from pathlib import Path

import pytest

from game_backend import (
    PhraseDataError,
    load_phrase_records,
    make_puzzle,
    get_phrase_metadata,
    grade_word_roles,
    phrase_bank_stats,
    validate_phrase_records,
)


def test_external_phrase_bank_loads_and_is_expanded():
    stats = phrase_bank_stats()
    assert stats["total_records"] >= 100
    assert stats["verified_records"] >= 100
    assert stats["random_enabled_records"] >= 20


def test_went_ahead_metadata_and_roles():
    puzzle = make_puzzle(" Went ", "AHEAD")
    metadata = get_phrase_metadata(puzzle)
    assert metadata is not None
    assert metadata["category"] == "phrasal verb"
    assert metadata["roles"] == ("verb", "adverb")
    result = grade_word_roles(puzzle, "verb", "adverb")
    assert result["available"] is True
    assert result["points"] == 10


def test_long_river_metadata_is_available_for_manual_entry():
    metadata = get_phrase_metadata(make_puzzle("long", "river"))
    assert metadata is not None
    assert metadata["roles"] == ("adjective", "noun")


def test_duplicate_pair_is_rejected():
    record = {
        "word1": "rain", "word2": "delay", "phrase": "rain delay",
        "category": "test", "roles": ["noun", "noun"],
        "role_explanations": ["one", "two"], "meaning": "x",
        "example": "y", "verified": True,
    }
    with pytest.raises(PhraseDataError, match="duplicate"):
        validate_phrase_records([record, dict(record)])


def test_missing_required_field_is_rejected():
    with pytest.raises(PhraseDataError, match="missing"):
        validate_phrase_records([{"word1": "rain", "word2": "delay"}])


def test_loader_accepts_an_alternate_valid_file(tmp_path: Path):
    record = {
        "word1": "test", "word2": "case", "phrase": "test case",
        "category": "software", "roles": ["noun", "noun"],
        "role_explanations": ["Test modifies case.", "Case is the head noun."],
        "meaning": "A set of conditions used to verify behavior.",
        "example": "The test case passed.", "verified": True,
        "enabled_for_random": False, "known_solutions": [],
    }
    path = tmp_path / "phrases.json"
    path.write_text(json.dumps([record]), encoding="utf-8")
    loaded = load_phrase_records(str(path))
    assert loaded[0]["word1"] == "test"
