from collections import Counter
from game_backend import apply_bonus_score, grade_solution, make_puzzle


def test_rain_delay_already_still_valid():
    result = grade_solution(make_puzzle("rain", "delay"), "Already", 7, True)
    assert result["ok"] is True
    assert result["score_base"] == 85


def test_letter_frequency_still_enforced():
    result = grade_solution(make_puzzle("rain", "delay"), "aaaared", 7, False)
    assert result["ok"] is False
    assert result["overuse"]["a"] == 2


def test_bonus_word_boundary_still_exact():
    valid = apply_bonus_score(
        grade_solution(make_puzzle("rain", "delay"), "already", 7, False),
        "I already finished.",
    )
    invalid = apply_bonus_score(
        grade_solution(make_puzzle("rain", "delay"), "already", 7, False),
        "This is alreadyish.",
    )
    assert valid["score_final"] == 95
    assert invalid["score_final"] == 85


def test_like_never_kneeler_is_valid_without_wordfreq():
    result = grade_solution(make_puzzle("like", "never"), "kneeler", 7, True)
    assert result["ok"] is True
    assert result["score_base"] == 80
