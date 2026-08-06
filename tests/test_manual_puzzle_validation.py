from game_backend import build_validated_hint_candidates, make_puzzle


def test_dark_roast_has_no_valid_solution_under_default_rules():
    puzzle = make_puzzle("dark", "roast", "dark roast")
    candidates = build_validated_hint_candidates(
        puzzle,
        min_letters_used=puzzle.total_len - 2,
        require_english=True,
        limit=200,
    )
    assert candidates == []


def test_rain_delay_remains_accepted():
    puzzle = make_puzzle("rain", "delay", "rain delay")
    candidates = build_validated_hint_candidates(
        puzzle,
        min_letters_used=puzzle.total_len - 2,
        require_english=True,
        limit=200,
    )
    assert any(item["solution"] == "already" for item in candidates)
