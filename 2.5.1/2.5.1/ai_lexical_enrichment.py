"""AI-assisted, explicitly unverified lexical cards with persistent SQLite caching."""
import json
import os
import re
import sqlite3
from pathlib import Path

ROLES = {'noun','verb','adjective','adverb','preposition','conjunction','interjection','pronoun','determiner'}
DB_PATH = lambda: Path(os.getenv('PHRASE_FORGE_LEXICAL_DB', str(Path.home() / '.phrase_forge' / 'lexical_cache.sqlite3')))


def normalize_word(word):
    value = (word or '').strip().lower()
    if not re.fullmatch(r'[a-z]{2,40}', value):
        raise ValueError('Expected a single alphabetic word')
    return value


def _db():
    path = DB_PATH()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), timeout=10)
    connection.execute('CREATE TABLE IF NOT EXISTS lexical_cards (word TEXT PRIMARY KEY, payload TEXT NOT NULL, model TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
    return connection


def cached_card(word):
    word = normalize_word(word)
    with _db() as db:
        row = db.execute('SELECT payload FROM lexical_cards WHERE word=?', (word,)).fetchone()
    return json.loads(row[0]) if row else None


def save_card(word, card, model='ai'):
    word = normalize_word(word)
    with _db() as db:
        db.execute('INSERT OR REPLACE INTO lexical_cards(word,payload,model,updated_at) VALUES(?,?,?,CURRENT_TIMESTAMP)', (word,json.dumps(card),model))


def parse_card(word, payload):
    word = normalize_word(word)
    if not isinstance(payload, dict):
        raise ValueError('Expected a JSON object')
    raw_roles = payload.get('roles', [])
    if not isinstance(raw_roles, list):
        raise ValueError('Roles must be a list')
    roles = [r.lower().strip() for r in raw_roles if isinstance(r,str) and r.lower().strip() in ROLES]
    meaning = payload.get('meaning')
    if not roles or not isinstance(meaning,str) or not meaning.strip():
        raise ValueError('Missing grammatical roles or meaning')
    examples = payload.get('examples', [])
    if not isinstance(examples,list):
        examples = []
    return {'word':word,'roles':list(dict.fromkeys(roles))[:5], 'meaning':meaning.strip()[:600],
            'examples':[x.strip()[:250] for x in examples if isinstance(x,str) and x.strip()][:2],
            'usage':str(payload.get('usage') or '')[:350], 'origin':None,
            'source':'AI-assisted · unverified', 'frequency':None, 'role_verified':False}


def enrich_word(word, force=False):
    """Fetch/cache a card. Never call this automatically on a Streamlit rerun."""
    word = normalize_word(word)
    if not force:
        card = cached_card(word)
        if card:
            return card
    if not os.getenv('OPENAI_API_KEY'):
        raise RuntimeError('Set OPENAI_API_KEY to enable AI Word Cards.')
    from openai import OpenAI
    model = os.getenv('PHRASE_FORGE_OPENAI_MODEL', 'gpt-5-mini')
    client = OpenAI()
    instruction = (
        'Return ONLY a JSON object with keys roles (list of standard parts of speech: '
        'noun, verb, adjective, adverb, preposition, conjunction, interjection, pronoun, determiner), '
        'meaning (nonempty concise string), examples (list of two natural sentences), usage (short note). '
        'For the English word '+json.dumps(word)+'. Do not invent etymology. '
        'Only list grammatically defensible roles. Use lowercase singular role names. '
        'If the word is rare, describe it accurately rather than omitting fields. '
        'This is educational assistance, not dictionary verification.'
    )
    last_error = None
    for attempt in range(2):
        response = client.responses.create(
            model=model,
            input=instruction + (' IMPORTANT: Previous response was incomplete or malformed; include both roles and meaning.' if attempt else ''),
        )
        raw = (response.output_text or '').strip()
        if raw.startswith('```'):
            raw = raw.split('\n',1)[1].rsplit('```',1)[0]
        try:
            card = parse_card(word, json.loads(raw))
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            continue
        save_card(word, card, model)
        return card
    raise ValueError(f'AI returned incomplete lexical information after two attempts: {last_error}')
