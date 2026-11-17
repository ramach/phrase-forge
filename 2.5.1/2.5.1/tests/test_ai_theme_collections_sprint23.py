import pytest
from types import SimpleNamespace
from ai_theme_collections import create_collection, normalize_theme

def test_theme_validation():
    assert normalize_theme('  Nature   & Wildlife ') == 'Nature & Wildlife'
    with pytest.raises(ValueError): normalize_theme('')

def test_deduplication_and_partial_results():
    def fake_generator(**kwargs):
        assert kwargs['theme'] == 'Nature'
        assert (kwargs['len_a'], kwargs['len_b']) == (5,4)
        return {'puzzle':SimpleNamespace(word1='rain',word2='delay',phrase_label='rain delay'),
                'validated_candidates':['already'], 'metadata':{'meaning':'test'}}
    items = create_collection('Nature', 3, 'Balanced', fake_generator)
    assert len(items) == 1
    assert items[0]['validated_count'] == 1

def test_rejects_unvalidated_puzzles():
    def fake_generator(**kwargs):
        return {'puzzle':SimpleNamespace(word1='rain',word2='delay',phrase_label='rain delay'),
                'validated_candidates':[], 'metadata':{}}
    assert create_collection('Nature', 3, 'Gentle', fake_generator) == []
