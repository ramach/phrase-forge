from game_backend import (
    Puzzle,
    build_validated_hint_candidates,
    create_progressive_hint,
    grade_solution,
)


def test_claimer_is_valid_for_inner_calm():
    puzzle = Puzzle("inner", "calm", "inner calm")
    result = grade_solution(puzzle, "claimer", min_letters_used=7, require_english=True)
    assert result["ok"] is True
    assert result["score_base"] == 80


def test_claimer_is_discovered_by_hint_solver():
    puzzle = Puzzle("inner", "calm", "inner calm")
    candidates = build_validated_hint_candidates(
        puzzle, min_letters_used=7, require_english=True, limit=500
    )
    assert "claimer" in {item["solution"] for item in candidates}


def test_progressive_hints_have_eight_distinct_levels():
    candidates = [{
        "solution": "claimer",
        "starts_with_vowel": False,
        "len": 7,
        "score_base": 80,
    }]
    hints = [create_progressive_hint(candidates, level, set()) for level in range(8)]
    assert len({hint["id"] for hint in hints}) == 8
    assert hints[0]["type"] == "strategy"
    assert hints[-1]["type"] == "reveal"
