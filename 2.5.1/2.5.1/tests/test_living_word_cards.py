from word_card_content import build_word_card

def test_curated_card_has_roles_and_examples():
    card=build_word_card("already")
    assert card["roles"] == ["adverb"]
    assert card["role_verified"]
    assert card["examples"]
    assert card["origin"] is None

def test_unknown_word_never_fabricates_origin_or_example():
    card=build_word_card("kneeler")
    assert card["origin"] is None
    assert card["examples"] == []
