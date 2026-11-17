import sys
from types import SimpleNamespace
from game_backend import make_puzzle, grade_solution, all_valid_solutions, build_validated_hint_candidates, explain_answer_attempt
from lexicon.validators import lexicon_info
from ai_theme_collections import create_collection


def test_high_frequency_names_are_not_common_words(monkeypatch):
    monkeypatch.setitem(sys.modules, 'wordfreq', SimpleNamespace(zipf_frequency=lambda *a: 6.0))
    for word in ('shakespeare', 'venice', 'london', 'bassanio', 'alexander', 'ishant', 'jessica'):
        for profile in ('standard', 'expert', 'teacher', 'casual'):
            assert lexicon_info(word, profile)['reason'] == 'proper_name'
        assert lexicon_info(word, 'standard_names')['accepted']


def test_common_senses_and_curated_words_survive():
    for word in ('amazon', 'turkey', 'harmony', 'rosemary', 'abridge', 'enraged', 'already', 'inflame'):
        assert lexicon_info(word)['accepted'], word
        assert lexicon_info(word)['category'] != 'proper_name'
    assert not lexicon_info('herself', 'standard_names')['accepted']
    assert not lexicon_info('zzzzzzzz', 'standard_names')['accepted']


def test_grading_solver_hints_and_mode_cache_agree():
    puzzle = make_puzzle('first', 'hand')
    for profile, expected in [('standard', False), ('standard_names', True), ('standard', False)]:
        grade = grade_solution(puzzle, 'ishant', 7, lexicon_profile=profile)
        assert grade['ok'] == expected
        assert ('ishant' in {r['solution'] for r in all_valid_solutions(puzzle, 7, lexicon_profile=profile)}) == expected
        assert ('ishant' in {r['solution'] for r in build_validated_hint_candidates(puzzle, 7, lexicon_profile=profile)}) == expected
        explanation = explain_answer_attempt(puzzle, grade, min_letters_used=7, lexicon_profile=profile)
        assert explanation
    assert not grade_solution(make_puzzle('first','hand'), 'shakespeare', 7, lexicon_profile='standard_names')['ok']


def test_collection_passes_mode():
    def generator(**kwargs):
        assert kwargs['lexicon_profile'] == 'standard_names'
        return {'puzzle':make_puzzle('first','hand'), 'validated_candidates':['ishant']}
    assert len(create_collection('History', generator=generator, lexicon_profile='standard_names')) == 1


def test_unknown_profile_does_not_enable_names():
    assert not lexicon_info('ishant', 'typo_names')['accepted']


def test_geographic_index_and_common_collision(monkeypatch):
    from lexicon import name_policy
    from lexicon import validators
    fake = SimpleNamespace(get_cities=lambda: {'1': {'name':'Toulouse'}, '2': {'name':'Orange'}},
                           get_countries=lambda: {}, get_us_states=lambda: {})
    monkeypatch.setitem(sys.modules, 'geonamescache', SimpleNamespace(GeonamesCache=lambda:fake))
    name_policy.geographic_names.cache_clear()
    name_policy.extra_names.cache_clear()
    try:
        assert 'toulouse' in name_policy.extra_names()
        assert validators.lexicon_info('toulouse')['reason'] == 'proper_name'
        assert validators.lexicon_info('orange')['accepted']
    finally:
        name_policy.geographic_names.cache_clear()
        name_policy.extra_names.cache_clear()


def test_ai_generator_uses_mode(monkeypatch):
    import ai_puzzle_generator as ai
    import json
    monkeypatch.setenv('OPENAI_API_KEY','test-only')
    response = SimpleNamespace(output_text=json.dumps({'word1':'first','word2':'hand','meaning':'test'}))
    client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs:response))
    monkeypatch.setitem(sys.modules,'openai',SimpleNamespace(OpenAI=lambda:client))
    result = ai.generate_validated_ai_puzzle(lexicon_profile='standard_names', attempts=1)
    assert 'ishant' in {r['solution'] for r in result['validated_candidates']}
    assert result['difficulty']['lexicon_profile'] == 'standard_names'
