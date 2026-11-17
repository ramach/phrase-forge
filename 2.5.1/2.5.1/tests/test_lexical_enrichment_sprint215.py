from word_card_content import build_word_card


def test_final_mile_inflame_cards():
    final = build_word_card('FINAL')
    mile = build_word_card('mile')
    inflame = build_word_card('inflame')
    assert {'adjective', 'noun'} <= set(final['roles'])
    assert mile['roles'] == ['noun']
    assert inflame['roles'] == ['verb']
    assert inflame['meaning'] and inflame['examples']
    assert all(card['role_verified'] for card in (final, mile, inflame))


def test_uncurated_word_does_not_invent_etymology():
    assert build_word_card('kneeler')['origin'] is None
