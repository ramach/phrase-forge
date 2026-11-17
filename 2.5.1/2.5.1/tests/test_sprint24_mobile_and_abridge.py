from pathlib import Path
from game_backend import make_puzzle, grade_solution, get_word_info


def test_abridge_accepted_in_standard_profile():
    p = make_puzzle('blind', 'rage')
    result = grade_solution(p, 'abridge', min_letters_used=7, require_english=True)
    assert result['ok'], result
    assert get_word_info('abridge')['accepted']


def test_unrecognized_word_not_automatically_accepted():
    p = make_puzzle('blind', 'rage')
    assert not grade_solution(p, 'zzzzzzz', min_letters_used=7)['ok']


def test_mobile_css_breakpoints_present():
    source = Path('living_prototype.py').read_text()
    assert '@media (max-width: 640px)' in source
    assert 'touch-action:manipulation' in source
    assert 'min-height:48px' in source
