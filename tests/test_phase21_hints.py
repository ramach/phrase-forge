from game_backend import create_progressive_hint


def test_progressive_hints_have_eight_unique_levels():
    candidates = [{"solution": "already", "starts_with_vowel": True, "len": 7, "score_base": 85}]
    hints = [create_progressive_hint(candidates, level, set()) for level in range(8)]
    assert [h["type"] for h in hints] == [
        "strategy", "start_type", "length", "distribution",
        "useful_letter", "first_letter", "pattern", "reveal",
    ]
    assert len({h["id"] for h in hints}) == 8
    assert "ALREADY" not in hints[0]["text"]
    assert "ALREADY" in hints[-1]["text"]


def test_hint_never_uses_empty_candidate():
    hint = create_progressive_hint([], 0, set())
    assert hint["type"] == "none"
