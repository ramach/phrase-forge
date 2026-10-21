from game_backend import Puzzle, grade_solution, is_valid_english_word, all_valid_solutions

def test_kneeler_is_guaranteed_english_word():
    assert is_valid_english_word("kneeler") is True

def test_like_never_accepts_kneeler():
    puzzle = Puzzle("like", "never", "like never")
    result = grade_solution(puzzle, "kneeler", min_letters_used=7, require_english=True)
    assert result["ok"] is True
    assert result["score_base"] == 80

def test_solver_discovers_kneeler():
    puzzle = Puzzle("like", "never", "like never")
    words = {r["solution"] for r in all_valid_solutions(puzzle, min_consonant_len=7, limit=500)}
    assert "kneeler" in words
