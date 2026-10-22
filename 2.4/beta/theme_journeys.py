"""Curated collection journeys for the Phrase Forge living prototype."""
from collections import defaultdict


def collections(records):
    grouped = defaultdict(list)
    for record in records:
        if record.get('verified') and record.get('word1') and record.get('word2'):
            grouped[record.get('category') or 'other'].append(record)
    return {category: sorted(items, key=lambda r: r.get('phrase', ''))
            for category, items in sorted(grouped.items())}


def record_id(record):
    return f"{record['word1'].lower()}|{record['word2'].lower()}"


def next_record(records, completed_ids, current_id=None):
    """Choose next unsolved record, skipping the current one when possible."""
    if not records:
        return None
    pending = [r for r in records if record_id(r) not in completed_ids]
    if not pending:
        return None
    different = [r for r in pending if record_id(r) != current_id]
    return (different or pending)[0]


def progress(records, completed_ids):
    return sum(record_id(r) in completed_ids for r in records), len(records)
