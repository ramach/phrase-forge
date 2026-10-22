from theme_journeys import collections, next_record, record_id, progress

RECORDS = [
    {'word1': 'rain', 'word2': 'delay', 'phrase': 'rain delay', 'category': 'core', 'verified': True},
    {'word1': 'pain', 'word2': 'point', 'phrase': 'pain point', 'category': 'core', 'verified': True},
    {'word1': 'bad', 'word2': 'data', 'phrase': 'bad data', 'category': 'business', 'verified': False},
]

def test_collections_only_curated_verified_sources():
    groups = collections(RECORDS)
    assert len(groups['core']) == 2
    assert 'business' not in groups

def test_continue_skips_current_and_completed():
    groups = collections(RECORDS)
    nxt = next_record(groups['core'], {'pain|point'}, 'pain|point')
    assert record_id(nxt) == 'rain|delay'
    assert next_record(groups['core'], {'rain|delay', 'pain|point'}) is None

def test_progress():
    assert progress(collections(RECORDS)['core'], {'rain|delay'}) == (1, 2)
