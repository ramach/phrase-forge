import pytest
import ai_lexical_enrichment as ai
from word_card_content import build_word_card


def test_parse_roles_and_provenance():
    card = ai.parse_card('forest', {'roles':['noun','invalid','NOUN'], 'meaning':'A wooded area.', 'examples':['A forest grew.']})
    assert card['roles'] == ['noun']
    assert not card['role_verified']
    assert 'unverified' in card['source']


def test_bad_payload_rejected():
    with pytest.raises(ValueError):
        ai.parse_card('forest', {'roles':[], 'meaning':'A wooded area.'})


def test_sqlite_cache(tmp_path, monkeypatch):
    monkeypatch.setenv('PHRASE_FORGE_LEXICAL_DB', str(tmp_path/'cache.sqlite3'))
    card = ai.parse_card('forest', {'roles':['noun'], 'meaning':'A wooded area.'})
    ai.save_card('forest',card)
    assert ai.cached_card('forest') == card
    assert build_word_card('forest')['source'] == 'AI-assisted · unverified'


def test_curated_priority(tmp_path, monkeypatch):
    monkeypatch.setenv('PHRASE_FORGE_LEXICAL_DB', str(tmp_path/'cache.sqlite3'))
    ai.save_card('final', ai.parse_card('final', {'roles':['noun'], 'meaning':'A test'}))
    assert build_word_card('final')['source'] == 'Phrase Forge editorial'


def test_retry_incomplete_ai_response(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace
    monkeypatch.setenv('PHRASE_FORGE_LEXICAL_DB', str(tmp_path/'cache.sqlite3'))
    monkeypatch.setenv('OPENAI_API_KEY', 'test-only')
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return SimpleNamespace(output_text='{"roles":[],"meaning":""}')
        return SimpleNamespace(output_text='{"roles":["verb"],"meaning":"To awaken interest.","examples":[]}')
    monkeypatch.setitem(sys.modules, 'openai', SimpleNamespace(OpenAI=lambda: SimpleNamespace(responses=SimpleNamespace(create=create))))
    card = ai.enrich_word('arouse')
    assert card['roles'] == ['verb']
    assert len(calls) == 2
    assert ai.cached_card('arouse') == card
