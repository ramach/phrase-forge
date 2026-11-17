from word_card_content import build_word_card

def test_rain_roles_and_meaning():
    card = build_word_card("rain")
    assert card["roles"] == ["noun", "verb"]
    assert card["role_verified"]
    assert card["meaning"] and len(card["examples"]) == 2

def test_delay_roles_and_examples():
    card = build_word_card("delay")
    assert card["roles"] == ["noun", "verb"]
    assert card["role_verified"]
    assert card["examples"]
