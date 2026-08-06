from game_backend import (
    apply_bonus_score,
    explain_answer_attempt,
    grade_solution,
    make_puzzle,
)


def test_explain_valid_answer_has_all_checks():
    puzzle = make_puzzle("rain", "delay", "rain delay")
    grade = apply_bonus_score(grade_solution(puzzle, "already", 7, True), "I already finished.")
    grade["word_score"] = grade["score_final"]
    grade["role_bonus"] = 10
    grade["combined_score"] = grade["word_score"] + 10
    explanation = explain_answer_attempt(puzzle, grade, 7, True, "I already finished.")
    assert explanation["valid"] is True
    assert all(check["passed"] for check in explanation["checks"])
    assert explanation["combined_score"] == 105
    assert explanation["letters_used"]["a"] == 2


def test_explain_duplicate_letter_shortage():
    puzzle = make_puzzle("rain", "delay", "rain delay")
    grade = grade_solution(puzzle, "aaaared", 7, False)
    explanation = explain_answer_attempt(puzzle, grade, 7, False)
    letter_check = next(c for c in explanation["checks"] if c["key"] == "letters")
    assert letter_check["passed"] is False
    assert "only 2 are available" in letter_check["detail"]
    assert explanation["overuse"]["a"] == 2


def test_explain_punctuation_failure_preserves_raw_input():
    puzzle = make_puzzle("rain", "delay", "rain delay")
    grade = grade_solution(puzzle, "al-ready", 7, True)
    explanation = explain_answer_attempt(puzzle, grade, 7, True)
    assert explanation["raw_input"] == "al-ready"
    input_check = next(c for c in explanation["checks"] if c["key"] == "input")
    assert input_check["passed"] is False


def test_explain_too_short_reports_vowel_exception():
    puzzle = make_puzzle("rain", "delay", "rain delay")
    grade = grade_solution(puzzle, "air", 7, False)
    explanation = explain_answer_attempt(puzzle, grade, 7, False)
    length_check = next(c for c in explanation["checks"] if c["key"] == "length")
    assert length_check["passed"] is False
    assert explanation["effective_minimum"] == 6
    assert "vowel-start exception" in length_check["detail"]
