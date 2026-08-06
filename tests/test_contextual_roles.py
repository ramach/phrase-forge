from game_backend import make_puzzle, get_contextual_phrase_metadata, grade_word_roles


def test_unknown_manual_phrase_gets_inferred_roles():
    puzzle = make_puzzle("went", "beyond", "went beyond")
    meta = get_contextual_phrase_metadata(puzzle)
    assert meta["inferred"] is True
    assert len(meta["roles"]) == 2
    assert 0 < meta["confidence"] <= 1


def test_went_ahead_uses_curated_metadata():
    puzzle = make_puzzle("went", "ahead", "went ahead")
    meta = get_contextual_phrase_metadata(puzzle)
    assert meta["source"] == "curated"
    assert meta["roles"] == ("verb", "adverb")


def test_unknown_roles_can_receive_credit():
    puzzle = make_puzzle("long", "journey", "long journey")
    meta = get_contextual_phrase_metadata(puzzle)
    result = grade_word_roles(puzzle, *meta["roles"])
    assert result["available"] is True
    assert result["points"] == 10
    assert result["inferred"] is True


def test_inferred_result_exposes_rule_and_reasoning():
    puzzle = make_puzzle("long", "journey", "long journey")
    meta = get_contextual_phrase_metadata(puzzle)
    assert meta["rule_id"] == "ADJECTIVE_PLUS_NOUN"
    assert meta["rule_label"] == "Adjective + noun"
    assert meta["reasoning"]
    assert meta["confidence_band"] == "high"


def test_low_confidence_inference_withholds_bonus():
    puzzle = make_puzzle("garden", "table", "garden table")
    meta = get_contextual_phrase_metadata(puzzle)
    assert meta["confidence_band"] == "low"
    result = grade_word_roles(puzzle, *meta["roles"])
    assert result["correct_count"] == 2
    assert result["raw_points"] == 10
    assert result["points"] == 0
    assert result["bonus_eligible"] is False
    assert result["bonus_withheld_reason"]


def test_medium_confidence_inference_can_award_bonus():
    puzzle = make_puzzle("under", "bridge", "under bridge")
    meta = get_contextual_phrase_metadata(puzzle)
    assert meta["confidence_band"] == "medium"
    result = grade_word_roles(puzzle, *meta["roles"])
    assert result["points"] == 10
    assert result["bonus_eligible"] is True


def test_curated_result_exposes_authoritative_diagnostic():
    puzzle = make_puzzle("went", "ahead", "went ahead")
    result = grade_word_roles(puzzle, "verb", "adverb")
    assert result["confidence_band"] == "curated"
    assert result["rule_id"] == "CURATED_METADATA"
    assert result["points"] == 10
