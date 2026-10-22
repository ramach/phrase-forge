"""Phrase Forge Living Prototype Sprint 1 — separate from the existing beta."""
import html
import random
import os
import streamlit as st
from game_backend import get_word_info, make_puzzle, grade_solution, explain_answer_attempt, PHRASE_RECORDS, build_validated_hint_candidates, all_valid_solutions, grade_word_roles
from learning_metadata import word_learning_metadata
from word_card_content import build_word_card
from ai_lexical_enrichment import enrich_word
from theme_journeys import collections, next_record, record_id, progress
from ai_theme_collections import create_collection, normalize_theme

st.set_page_config(page_title='Phrase Forge · Living Prototype', page_icon='🌿', layout='wide', initial_sidebar_state='collapsed')
st.markdown('''<style>
.stApp{background:#faf6ec;color:#24364a}.block-container{max-width:720px;padding-top:1.8rem}h1,h2,h3{font-family:Georgia,serif;color:#24364a}div.stButton>button[kind="primary"]{background:#285b4b;color:white;border-radius:12px;border:0;min-height:3rem}div.stButton>button{border-radius:12px;min-height:2.8rem}.pf-panel{border:1px solid #e5ddca;background:#fffdf8;padding:1.4rem;border-radius:20px;margin:1rem 0}.pf-eyebrow{color:#8d754a;text-transform:uppercase;letter-spacing:.14em;font-size:.78rem}.pf-words{font:700 2.2rem Georgia,serif;text-align:center;letter-spacing:.02em;color:#284d43;padding:1.5rem 0}.pf-word{font:700 2.5rem Georgia,serif;text-align:center;color:#285b4b}.pf-sub{text-align:center;color:#6d736e}.pf-brand{text-align:center;font:700 2.7rem Georgia,serif;margin:1rem 0 .3rem}.pf-hero{text-align:center;font:1.45rem Georgia,serif;margin:1.6rem auto;max-width:500px;line-height:1.5}.pf-tiny{font-size:.83rem;color:#6d736e}.pf-source-card{border:1px solid #ded5bf;border-radius:14px;padding:16px 10px;background:#fffdf8;min-height:95px;text-align:center}.pf-source-title{font:700 1.45rem Georgia,serif;color:#285b4b}.pf-source-role{font-size:.95rem;color:#283f38;margin-top:8px;font-weight:600}

/* Sprint 2.4: responsive enhancements layered over the approved desktop design. */
.block-container {max-width: 720px; margin-left:auto; margin-right:auto; padding-left:1.5rem; padding-right:1.5rem;}
button, input, select {touch-action:manipulation;}
@media (max-width: 640px) {
  .block-container {max-width:100%; padding:1rem .85rem 5rem !important;}
  .pf-brand {font-size:clamp(1.9rem,9vw,2.5rem); line-height:1.15; margin-top:.6rem;}
  .pf-hero {font-size:1.17rem; line-height:1.42; margin:1rem auto;}
  .pf-panel {padding:1rem .75rem; border-radius:16px; margin:.7rem 0;}
  .pf-words {font-size:clamp(1.35rem,6vw,2rem); padding:1rem 0; overflow-wrap:anywhere;}
  .pf-word {font-size:clamp(1.9rem,9vw,2.5rem); overflow-wrap:anywhere;}
  .pf-source-card {padding:.85rem .35rem; min-height:88px;}
  .pf-source-title {font-size:clamp(1.05rem,5vw,1.4rem); overflow-wrap:anywhere;}
  .pf-source-role {font-size:.83rem; overflow-wrap:anywhere;}
  [data-testid="stHorizontalBlock"] {gap:.5rem !important;}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {min-width:0 !important;}
  div.stButton > button, div.stFormSubmitButton > button {min-height:46px; padding:.55rem .4rem; white-space:normal; overflow-wrap:anywhere;}
  div[data-testid="stTextInput"] input {font-size:16px; min-height:48px;}
  [data-testid="stSelectbox"] {min-width:0;}
  [data-testid="stSelectbox"] div[data-baseweb="select"] {min-height:46px;}
  h1 {font-size:1.75rem;} h2 {font-size:1.45rem;} h3 {font-size:1.18rem;}
}
@media (max-width: 380px) {
  .block-container {padding-left:.55rem !important; padding-right:.55rem !important;}
  div.stButton > button {font-size:.79rem;}
}
</style>''', unsafe_allow_html=True)

def navigate(page):
    st.session_state.page=page
    st.rerun()

def panel(title, body):
    st.markdown(f'<div class="pf-panel"><div class="pf-eyebrow">{html.escape(title)}</div><p>{html.escape(body)}</p></div>', unsafe_allow_html=True)

def ai_enrichment_controls(words, key):
    """Opt-in enrichment, never invoked implicitly during a page rerun."""
    missing = [w for w in dict.fromkeys(words) if not build_word_card(w)['role_verified'] and build_word_card(w)['source'] != 'AI-assisted · unverified']
    if missing:
        if st.button('✨ Identify roles & meanings with AI', key=key, use_container_width=True):
            with st.spinner('Preparing Word Cards…'):
                success = 0
                for word in missing:
                    try:
                        enrich_word(word)
                        success += 1
                    except Exception as exc:
                        st.warning(f'Could not enrich {word.upper()}: {exc}')
                if success:
                    st.rerun()
    elif any(build_word_card(w)['source'] == 'AI-assisted · unverified' for w in words):
        st.caption('✨ AI-assisted Word Cards are cached locally; classifications are not dictionary-verified.')


def show_source_word_roles(word1, word2):
    """Readable source cards, with expandable definitions and usage examples."""
    st.markdown('#### Explore your source words')
    ai_enrichment_controls((word1,word2), 'enrich_sources_' + st.session_state.get('page','play'))
    cols = st.columns(2)
    for col, source_word in zip(cols, (word1, word2)):
        with col:
            card = build_word_card(source_word)
            roles = ' · '.join(role.title() for role in card['roles']) if card['roles'] else 'Role not yet verified'
            st.markdown(f'<div class="pf-source-card"><div class="pf-source-title">{html.escape(source_word.upper())}</div><div class="pf-source-role">{html.escape(roles)}</div></div>', unsafe_allow_html=True)
            if card['roles'] and not card['role_verified']:
                st.caption('AI-identified roles · Not independently verified' if card['source'] == 'AI-assisted · unverified' else 'Suggested roles · Not independently verified')
            with st.expander(f'Explore {source_word.title()}'):
                st.markdown('**Meaning**')
                st.write(card['meaning'] or 'Definition not yet curated.')
                if card['examples']:
                    st.markdown('**Examples**')
                    for example in card['examples']:
                        st.write('“' + example + '”')
                if card['usage']:
                    st.markdown('**Usage**')
                    st.write(card['usage'])
                if card['origin']:
                    st.markdown('**Origin**')
                    st.write(card['origin'])
                if card['source'] != 'AI-assisted · unverified':
                    st.caption('Content: ' + card['source'])


ROLE_OPTIONS = ['Choose a role', 'noun', 'verb', 'adjective', 'adverb', 'preposition', 'conjunction', 'interjection', 'pronoun', 'determiner']

def show_role_selector(puzzle):
    st.markdown('#### Identify the source-word roles')
    st.caption('Select the grammatical role of each source word in the phrase. You can check your answers independently of solving.')
    if any(build_word_card(w)['source'] == 'AI-assisted · unverified' for w in (puzzle.word1, puzzle.word2)):
        st.caption('AI Word Cards list possible word roles; the role quiz uses its separate contextual grammar rules, which may differ.')
    # New widget keys per puzzle avoid modifying instantiated Streamlit widgets.
    epoch = st.session_state.get('role_widget_epoch', 0)
    a, b = st.columns(2)
    with a:
        role1 = st.selectbox(f'Role of {puzzle.word1.upper()}', ROLE_OPTIONS, key=f'role_1_{epoch}')
    with b:
        role2 = st.selectbox(f'Role of {puzzle.word2.upper()}', ROLE_OPTIONS, key=f'role_2_{epoch}')
    if st.button('Check Word Roles', use_container_width=True):
        if 'Choose a role' in (role1, role2):
            st.warning('Please select both roles.')
        else:
            st.session_state.role_result = grade_word_roles(puzzle, role1, role2)
    result = st.session_state.get('role_result')
    if result:
        for item in result['items']:
            st.write(('✅ ' if item['ok'] else '⚠️ ') + f"**{item['word'].upper()}**: {item['correct_role'].title()} — {item['explanation']}")
        if result.get('inferred'):
            st.caption('These classifications are inferred, not editorially verified.')
        if not result.get('bonus_eligible', True):
            st.info(result.get('bonus_withheld_reason'))
        else:
            st.success(f"Role bonus: +{result['points']} points")

def show_solutions(puzzle):
    st.markdown('#### Identified solutions')
    found = st.session_state.get('found_solutions', [])
    if found:
        st.write('Your discoveries: ' + ', '.join(w.upper() for w in found))
    else:
        st.caption('Your accepted answers will appear here.')
    if st.button('Find all verified solutions', use_container_width=True):
        with st.spinner('Searching the local lexicon…'):
            st.session_state.solution_results = all_valid_solutions(puzzle, min_consonant_len=7, limit=200)
    if st.session_state.get('solution_results') is not None:
        results = st.session_state.solution_results
        st.caption(f'{len(results)} locally validated solutions shown (lexicon-dependent).')
        if results:
            st.write(', '.join(item['solution'].upper() for item in results))
        else:
            st.info('No solutions were found in the configured local lexicon.')

def custom_puzzle():
    with st.form('custom_puzzle_form'):
        a = st.text_input('First source word', max_chars=30)
        b = st.text_input('Second source word', max_chars=30)
        submitted = st.form_submit_button('Play My Puzzle', type='primary', use_container_width=True)
    if submitted:
        import re
        if not re.fullmatch(r'[A-Za-z]{2,30}', a.strip()) or not re.fullmatch(r'[A-Za-z]{2,30}', b.strip()):
            st.error('Please enter two alphabetic words, at least two letters each.')
        else:
            st.session_state.puzzle_words = (a.lower().strip(), b.lower().strip(), f'{a.lower().strip()} {b.lower().strip()}')
            st.session_state.active_theme = None
            st.session_state.puzzle_origin = 'Your own puzzle'
            start()

THEMES = collections(PHRASE_RECORDS)

def open_collection(category):
    if category not in THEMES:
        st.error('Collection unavailable.')
        return
    st.session_state.active_ai_collection = None
    st.session_state.active_theme = category
    st.session_state.page = 'collection'
    st.rerun()

def play_theme_record(record):
    st.session_state.puzzle_words = (record['word1'], record['word2'], record.get('phrase') or f"{record['word1']} {record['word2']}")
    st.session_state.puzzle_origin = f"{st.session_state.active_theme.title()} collection"
    start()

def next_theme_puzzle():
    theme = st.session_state.get('active_theme')
    records = THEMES.get(theme, [])
    completed = set(st.session_state.get('theme_completed', {}).get(theme, []))
    current = f"{st.session_state.puzzle_words[0]}|{st.session_state.puzzle_words[1]}"
    record = next_record(records, completed, current)
    if record is None:
        st.session_state.page = 'collection'
        st.rerun()
    else:
        play_theme_record(record)

def start():
    st.session_state.page='play'; st.session_state.attempt=None; st.session_state.answer=''; st.session_state.role_result=None; st.session_state.solution_results=None; st.session_state.found_solutions=[]; st.session_state.role_widget_epoch = st.session_state.get('role_widget_epoch', 0) + 1; st.rerun()

def random_puzzle():
    candidates = [r for r in PHRASE_RECORDS if r.get('enabled_for_random') and r.get('verified')]
    if not candidates:
        candidates = [r for r in PHRASE_RECORDS if r.get('verified') and r.get('known_solutions')]
    if not candidates:
        st.error('No eligible puzzles in the phrase bank.')
        return
    seen = st.session_state.setdefault('seen_puzzles', [])
    unseen = [r for r in candidates if (r['word1'],r['word2']) not in seen]
    if not unseen:
        seen.clear()
        unseen = candidates
    record = random.choice(unseen)
    seen.append((record['word1'],record['word2']))
    st.session_state.puzzle_words=(record['word1'],record['word2'],record['phrase'])
    st.session_state.active_theme=None
    st.session_state.active_ai_collection=None
    st.session_state.puzzle_origin='Random collection'
    start()

def ai_puzzle(theme=""):
    theme = theme.strip()
    from ai_puzzle_generator import generate_validated_ai_puzzle, ai_generation_available
    if not ai_generation_available():
        st.warning('AI generation needs OPENAI_API_KEY. Random puzzles work without it.')
        return
    try:
        with st.spinner('Generating and validating a new puzzle…'):
            result=generate_validated_ai_puzzle(min_letters=7, theme=theme)
        p=result['puzzle']
        st.session_state.puzzle_words=(p.word1,p.word2,p.phrase_label)
        st.session_state.active_theme=None
        st.session_state.active_ai_collection=None
        st.session_state.puzzle_origin=('AI · '+theme if theme else 'AI-generated')+' · locally validated'
        start()
    except Exception as exc:
        st.error(f'AI generation could not complete: {exc}')


def play_ai_collection_item(index):
    collection = st.session_state.get('active_ai_collection')
    if not collection or not 0 <= index < len(collection['items']):
        st.error('No AI collection puzzle is available.')
        return
    item = collection['items'][index]
    st.session_state.ai_collection_index = index
    st.session_state.puzzle_words = (item['word1'], item['word2'], item['phrase'])
    st.session_state.active_theme = None
    st.session_state.puzzle_origin = f"AI · {collection['theme']} ({index+1}/{len(collection['items'])})"
    start()

def ai_collection_controls():
    st.markdown('### Create Your Own Discovery Collection')
    with st.form('ai_collection_form'):
        theme = st.text_input('Theme', placeholder='Nature, Shakespeare, Indian wildlife…', max_chars=80)
        difficulty = st.selectbox('Difficulty', ['Gentle', 'Balanced', 'Challenge'], index=1)
        count = st.selectbox('Number of puzzles', [3, 5, 10])
        submitted = st.form_submit_button('✨ Create Collection', type='primary', use_container_width=True)
    if submitted:
        try:
            theme = normalize_theme(theme)
            with st.spinner('Generating and locally validating themed puzzles…'):
                items = create_collection(theme, count, difficulty)
            if not items:
                st.warning('No valid puzzles were generated. Try another theme or difficulty.')
                return
            st.session_state.active_ai_collection = {'theme':theme, 'items':items, 'completed':[]}
            st.session_state.ai_collection_index = 0
            if len(items) < count:
                st.warning(f'Generated {len(items)} of {count} requested puzzles. Only validated puzzles were retained.')
            play_ai_collection_item(0)
        except Exception as exc:
            st.error(f'Collection generation could not complete: {exc}')

def ai_collection_progress():
    collection = st.session_state.get('active_ai_collection')
    if not collection:
        return
    done = len(collection['completed'])
    total = len(collection['items'])
    st.caption(f"{collection['theme']} · {done} of {total} discoveries")
    st.progress(done/total if total else 0)
    pending = [i for i in range(total) if i not in collection['completed']]
    if pending:
        if st.button('Continue AI Collection →', type='primary', use_container_width=True):
            play_ai_collection_item(pending[0])
    else:
        st.success('Collection complete!')

for key, default in [('active_theme',None),('active_ai_collection',None),('ai_collection_index',0),('theme_completed',{}),('page','home'),('attempt',None),('answer',''),('puzzle_words',('rain','delay','rain delay')),('puzzle_origin','Practice')]:
    st.session_state.setdefault(key,default)
puzzle=make_puzzle(*st.session_state.puzzle_words)
page=st.session_state.page
if page=='home':
    st.markdown('<div class="pf-brand">🌿 Phrase Forge</div><div class="pf-sub">DISCOVER · EXPLORE · LEARN</div>',unsafe_allow_html=True)
    st.markdown('<div class="pf-hero">Two ordinary words can hide an extraordinary discovery.</div>',unsafe_allow_html=True)
    panel('Your next discovery','Begin with two words. Find the unexpected word hidden in their letters.')
    if st.button('Begin Your First Discovery →',type='primary',use_container_width=True): start()
    panel('How Phrase Forge Works','A gentle introduction to the rules, with a worked example.')
    if st.button('Explore How to Play →',use_container_width=True): navigate('rules')
    if st.button('🎲 New Random Puzzle',use_container_width=True): random_puzzle()
    with st.expander('✨ Generate AI Puzzle'):
        single_theme = st.text_input('Optional theme for one AI puzzle', key='single_ai_theme_home')
        if st.button('Generate Puzzle', key='single_ai_home'): ai_puzzle(single_theme)
    with st.expander('✍️ Create your own puzzle'):
        custom_puzzle()
    panel('Explore collections', 'Choose a theme and follow a curated journey of source phrases.')
    if st.button('Browse Theme Packs →', use_container_width=True): navigate('themes')
    ai_collection_controls()
elif page=='themes':
    st.title('Explore Discovery Collections')
    st.caption('Curated source phrases. Some are open challenges without a preverified solution.')
    for category, records in THEMES.items():
        done, total = progress(records, set(st.session_state.theme_completed.get(category, [])))
        with st.container(border=True):
            st.markdown(f"**{category.title()}** · {total} discoveries")
            st.caption(f'{done} completed · {total-done} to explore')
            if st.button('Explore this collection →', key=f'theme_{category}', use_container_width=True): open_collection(category)
    if st.button('✨ Create an AI Discovery Collection', use_container_width=True): navigate('ai_collections')
    if st.button('← Home'): navigate('home')
elif page=='ai_collections':
    st.title('AI Discovery Collections')
    ai_collection_controls()
    ai_collection_progress()
    if st.button('← Explore'): navigate('themes')
elif page=='collection':
    theme = st.session_state.get('active_theme')
    records = THEMES.get(theme, [])
    if not records:
        navigate('themes')
    st.caption('DISCOVERY COLLECTION')
    st.title(theme.title())
    completed = set(st.session_state.theme_completed.get(theme, []))
    done, total = progress(records, completed)
    st.progress(done / total if total else 0, text=f'{done} of {total} discoveries completed')
    if done == total:
        st.success('You have explored every source phrase in this collection!')
    else:
        if st.button('Continue Journey →', type='primary', use_container_width=True): next_theme_puzzle()
    with st.expander('View source phrases'):
        for record in records:
            mark = '✓' if record_id(record) in completed else '○'
            st.write(f"{mark} {record.get('phrase', record['word1']+' '+record['word2']).title()}")
    if st.button('← All Collections'): navigate('themes')
elif page=='rules':
    st.title('How Phrase Forge Works')
    st.markdown('**Start with two source words.** Forge a different valid English word using only their available letters, without using any letter more often than it appears.')
    st.markdown('**Your answer must not contain either complete source word.**')
    st.markdown('**Minimum length:** 6 letters for a vowel-starting answer; 7 letters for a consonant-starting answer.')
    panel('Worked example','RAIN + DELAY → ALREADY')
    if st.button('Try the Puzzle →',type='primary',use_container_width=True): start()
    if st.button('← Home'): navigate('home')
elif page=='play':
    st.caption('YOUR DISCOVERY · '+st.session_state.puzzle_origin.upper())
    st.title('What can you forge?')
    st.markdown(f'<div class="pf-panel"><div class="pf-words">{html.escape(puzzle.word1.upper())} &nbsp; + &nbsp; {html.escape(puzzle.word2.upper())}</div><div class="pf-sub">Use only the available letters.</div></div>',unsafe_allow_html=True)
    show_source_word_roles(puzzle.word1, puzzle.word2)
    show_role_selector(puzzle)
    with st.expander('✍️ Enter a different puzzle'):
        custom_puzzle()
    if st.button('ⓘ How to Play'): navigate('rules')
    with st.form('forge',clear_on_submit=False):
        answer=st.text_input('Your discovery',value=st.session_state.answer,placeholder='Enter an English word')
        submitted=st.form_submit_button('Forge →',type='primary',use_container_width=True)
    if submitted:
        st.session_state.answer=answer
        grade=grade_solution(puzzle,answer,min_letters_used=7,require_english=True)
        st.session_state.attempt=grade
        if grade['ok']:
            found = st.session_state.setdefault('found_solutions', [])
            if grade['solution'] not in found: found.append(grade['solution'])
            theme = st.session_state.get('active_theme')
            if theme:
                completed = st.session_state.theme_completed.setdefault(theme, [])
                current_id = f'{puzzle.word1}|{puzzle.word2}'
                if current_id not in completed:
                    completed.append(current_id)
            if st.session_state.get('active_ai_collection'):
                col = st.session_state.active_ai_collection
                idx = st.session_state.get('ai_collection_index', 0)
                if idx not in col['completed']: col['completed'].append(idx)
            navigate('discovery')
    grade=st.session_state.attempt
    if grade and not grade['ok']:
        st.warning(grade.get('reason','Please try another answer.'))
        explanation=explain_answer_attempt(puzzle,grade,min_letters_used=7)
        with st.expander('Understand the rules',expanded=True):
            for check in explanation.get('checks',[]):
                st.markdown(('✅' if check.get('passed') else '⚠️')+' **'+check.get('label','Rule')+'** — '+check.get('detail',''))
    with st.expander('🔎 Solutions for this puzzle'):
        show_solutions(puzzle)
    a,b,c=st.columns(3)
    with a:
        if st.button('🎲 Random',use_container_width=True): random_puzzle()
    with b:
        if st.button('✨ AI Puzzle',use_container_width=True): ai_puzzle()
    with c:
        if st.button('↻ Replay',use_container_width=True): start()
    if st.session_state.get('active_ai_collection'):
        ai_collection_progress()
    if st.session_state.get('active_theme') and st.button('← Collection'): navigate('collection')
    if st.button('← Home'): navigate('home')
elif page=='discovery':
    grade=st.session_state.attempt
    if not grade or not grade.get('ok'): navigate('play')
    st.markdown('<div class="pf-sub">🌱 A NEW DISCOVERY</div>',unsafe_allow_html=True)
    st.markdown('<div class="pf-word">'+html.escape(grade['solution'].upper())+'</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="pf-sub">Beautifully forged from {html.escape(puzzle.word1.upper())} + {html.escape(puzzle.word2.upper())}</div>',unsafe_allow_html=True)
    st.success(f"Valid discovery · {grade['score_base']} points")
    if st.button('See What You Discovered →',type='primary',use_container_width=True): navigate('word')
    if st.button('Try Again'): start()
elif page=='word':
    grade=st.session_state.attempt
    if not grade or not grade.get('ok'): navigate('play')
    word=grade['solution']
    st.caption('WORD CARD')
    st.title(word.title())
    ai_enrichment_controls((word,), 'enrich_answer')
    card = build_word_card(word)
    if card['roles']:
        st.caption(' · '.join(role.title() for role in card['roles']))
    panel('Meaning', card['meaning'] or 'Definition not yet available in the local lexicon.')
    if card['examples']:
        st.markdown('**Examples in context**')
        for example in card['examples']:
            st.write('“' + example + '”')
    if card['usage']:
        st.markdown('**Usage note**')
        st.write(card['usage'])
    if not card['role_verified'] and card['roles']:
        st.caption('AI-identified roles · Not independently verified' if card['source'] == 'AI-assisted · unverified' else 'Suggested roles · Not independently verified')
    elif card['source'] == 'Phrase Forge editorial':
        st.caption('Phrase Forge editorial')
    st.markdown('### Explore the two source words')
    show_source_word_roles(puzzle.word1, puzzle.word2)
    if word=='already': st.markdown('**Example:** “The discovery has already begun.”')
    else: st.markdown('Keep exploring the language behind your discovery.')
    if st.button('Continue Exploring →',type='primary',use_container_width=True): navigate('continue')
elif page=='continue':
    st.title('Curiosity continues 🌱')
    theme = st.session_state.get('active_theme')
    if st.session_state.get('active_ai_collection'):
        ai_collection_progress()
    if theme:
        records = THEMES.get(theme, [])
        done, total = progress(records, set(st.session_state.theme_completed.get(theme, [])))
        panel(f'{theme.title()} collection', f'{done} of {total} discoveries completed. Continue your journey whenever you are ready.')
        if done < total and st.button('Continue This Collection →', type='primary', use_container_width=True): next_theme_puzzle()
        if st.button('View Collection →', use_container_width=True): navigate('collection')
    else:
        panel('Your discovery', 'You have completed a discovery. Continue with another puzzle, or explore a curated collection.')
        if st.button('Browse Theme Packs →', use_container_width=True): navigate('themes')
    if st.button('🎲 New Random Puzzle',type='primary',use_container_width=True): random_puzzle()
    if st.button('✨ Generate AI Puzzle',use_container_width=True): ai_puzzle()
    if st.button('↻ Replay Current Puzzle',use_container_width=True): start()
    if st.button('← Home'): navigate('home')
