from game_backend import get_phrase_metadata, grade_word_roles, make_puzzle


def test_rain_delay_roles_are_contextual_nouns():
    puzzle = make_puzzle("rain", "delay", "rain delay")
    result = grade_word_roles(puzzle, "noun", "noun")
    assert result["available"] is True
    assert result["correct_count"] == 2
    assert result["points"] == 10
    assert all(item["ok"] for item in result["items"])


def test_dead_wrong_uses_adverb_and_adjective():
    puzzle = make_puzzle("dead", "wrong", "dead wrong")
    result = grade_word_roles(puzzle, "adverb", "adjective")
    assert result["correct_count"] == 2
    assert result["items"][0]["correct_role"] == "adverb"


def test_incorrect_role_gets_partial_credit_and_explanation():
    puzzle = make_puzzle("rain", "delay", "rain delay")
    result = grade_word_roles(puzzle, "verb", "noun")
    assert result["correct_count"] == 1
    assert result["points"] == 5
    assert result["items"][0]["ok"] is False
    assert "noun" in result["items"][0]["explanation"].lower()


def test_custom_phrase_without_metadata_is_inferred():
    puzzle = make_puzzle("blue", "river", "blue river")
    result = grade_word_roles(puzzle, "adjective", "noun")
    assert result["available"] is True
    assert result["points"] == 10
    assert result["inferred"] is True


def test_pain_point_manual_example_has_curated_roles():
    result = grade_word_roles(make_puzzle("pain", "point"), "noun", "noun")
    assert result["available"] is True
    assert result["points"] == 10


def test_phrase_metadata_has_meaning_and_example():
    metadata = get_phrase_metadata(make_puzzle("rain", "delay"))
    assert metadata
    assert metadata["meaning"]
    assert metadata["example"]
