from game_backend import (
    Puzzle,
    all_valid_solutions,
    compute_difficulty,
    grade_solution,
    get_word_info,
    solver_index_stats,
)
from leaderboard_db import db_backend_name, init_db, submit_score, top_scores


def test_pfl_rejects_pronouns_and_seeded_names():
    assert get_word_info("they", "standard")["accepted"] is False
    assert get_word_info("they", "standard")["reason"] == "pronoun"
    assert get_word_info("paris", "standard")["accepted"] is False
    assert get_word_info("paris", "standard")["reason"] == "proper_name"


def test_pfl_keeps_curated_rare_words():
    for word in ("kneeler", "wheaten", "claimer"):
        assert get_word_info(word, "standard")["accepted"] is True


def test_indexed_solver_discovers_known_solution():
    puzzle = Puzzle("like", "never", "like never")
    solutions = all_valid_solutions(puzzle, 7, True, limit=500, lexicon_profile="standard")
    assert "kneeler" in {item["solution"] for item in solutions}
    stats = solver_index_stats()
    assert stats["indexed_words"] >= 3


def test_difficulty_contains_beta_1_analytics():
    puzzle = Puzzle("like", "never", "like never")
    result = compute_difficulty(puzzle, 7, lexicon_profile="standard")
    assert "solutions_found" in result
    assert "longest_solution" in result
    assert "highest_base_score" in result
    assert result["lexicon_profile"] == "standard"


def test_sqlite_fallback_best_score(tmp_path, monkeypatch):
    import leaderboard_db
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("PHRASE_FORGE_DATABASE_URL", raising=False)
    monkeypatch.setattr(leaderboard_db, "DB_PATH", tmp_path / "beta1.sqlite3")
    assert db_backend_name() == "sqlite"
    init_db()
    submit_score(None, "p1", "like never", "Hard", "Tester", 80, "kneeler", mode="Practice")
    submit_score(None, "p1", "like never", "Hard", "Tester", 75, "other", mode="Practice")
    rows = top_scores(puzzle_id="p1", mode="Practice")
    assert rows[0]["score"] == 80
    assert rows[0]["solution"] == "kneeler"


def test_pfl_blocks_reported_names_in_every_profile():
    for profile in ("casual", "standard", "expert", "teacher"):
        for word in ("ishtar", "ishant"):
            info = get_word_info(word, profile)
            assert info["accepted"] is False
            assert info["reason"] == "proper_name"


def test_pfl_blocks_extended_pronouns_in_every_profile():
    for profile in ("casual", "standard", "expert", "teacher"):
        for word in ("herself", "themselves", "whoever", "someone", "anything"):
            info = get_word_info(word, profile)
            assert info["accepted"] is False
            assert info["reason"] == "pronoun"


def test_pfl_profiles_broaden_rarity_not_gameplay_exclusions():
    for word in ("ishtar", "ishant", "herself", "whoever"):
        assert get_word_info(word, "expert")["accepted"] is False
        assert get_word_info(word, "teacher")["accepted"] is False


def test_first_hand_reported_names_cannot_be_graded():
    puzzle = Puzzle("first", "hand", "first hand")
    for word in ("ishtar", "ishant"):
        result = grade_solution(puzzle, word, min_letters_used=7, require_english=True, lexicon_profile="standard")
        assert result["ok"] is False
        assert result.get("lexicon", {}).get("reason") == "proper_name"
