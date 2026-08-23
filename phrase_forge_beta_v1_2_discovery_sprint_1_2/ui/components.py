from __future__ import annotations
from typing import Any, Mapping, Optional
import streamlit as st


def render_brand_header(version: str, build_date: str) -> None:
    st.markdown(f"""
    <div class="pf-hero">
      <div class="pf-kicker">Beta 1.2 · Discovery</div>
      <h1>🔤 Phrase Forge</h1>
      <div class="pf-tagline">Discover the language hidden inside language.</div>
      <div class="pf-muted" style="margin-top:.45rem;font-size:.78rem">{version} · Build {build_date}</div>
    </div>
    """, unsafe_allow_html=True)


def render_how_to_play(expanded: bool = True) -> None:
    with st.expander("❓ How to Play", expanded=expanded):
        st.markdown("""
### `RAIN DELAY` → `ALREADY`

1. **Forge a different English word** from letters in the two-word phrase.
2. **Letter counts matter** — use each letter no more often than it appears.
3. Your answer **cannot contain either complete phrase word**.
4. Meet the displayed minimum length; a **vowel-starting word may qualify one letter shorter**.
5. Identify the phrase words' grammatical roles for an optional grammar bonus.

**Why play?** Discover vocabulary, understand grammar, recognize phrases, and grow your personal language journey.
        """)


def _nav(target: str) -> None:
    st.session_state["pending_main_view"] = target
    st.rerun()


def render_home(*, nickname: str, journey: Optional[Mapping[str, Any]], ai_enabled: bool, ai_remaining: int) -> None:
    st.markdown("## What would you like to do?")
    play, explore, learn = st.columns(3)
    with play:
        st.markdown('<div class="pf-card"><div class="pf-kicker">PLAY</div><h3>Forge something</h3><div class="pf-muted">Jump into a puzzle or create a fresh challenge.</div></div>', unsafe_allow_html=True)
        if st.button("▶ Continue", use_container_width=True, type="primary", key="home_continue"):
            _nav("Play")
        if st.button("🎲 Random Puzzle", use_container_width=True, key="home_random"):
            st.session_state["home_action"] = "random"
            _nav("Play")
        if st.button("📅 Daily Puzzle", use_container_width=True, key="home_daily"):
            st.session_state["home_action"] = "daily"
            _nav("Play")
        ai_label = "✨ Create a Puzzle" if ai_enabled else "✨ Create a Puzzle · setup needed"
        if st.button(ai_label, use_container_width=True, key="home_ai"):
            st.session_state["home_action"] = "ai"
            _nav("Play")
        if ai_enabled:
            st.caption(f"AI requests remaining this session: {ai_remaining}")
    with explore:
        st.markdown('<div class="pf-card"><div class="pf-kicker">EXPLORE</div><h3>Follow your curiosity</h3><div class="pf-muted">Themes, discoveries, and friendly competition.</div></div>', unsafe_allow_html=True)
        if st.button("🪄 Theme Packs", use_container_width=True, key="home_themes"):
            st.session_state["explore_section"] = "Theme Packs"
            _nav("Explore")
        if st.button("📚 My Journey", use_container_width=True, key="home_journey"):
            st.session_state["explore_section"] = "My Journey"
            _nav("Explore")
        if st.button("🏆 Leaderboard", use_container_width=True, key="home_leader"):
            st.session_state["explore_section"] = "Leaderboard"
            _nav("Explore")
    with learn:
        st.markdown('<div class="pf-card"><div class="pf-kicker">LEARN</div><h3>Understand language</h3><div class="pf-muted">See why words work and build lasting vocabulary.</div></div>', unsafe_allow_html=True)
        if st.button("❓ How to Play", use_container_width=True, key="home_how"):
            st.session_state["learn_section"] = "How to Play"
            _nav("Learn")
        if st.button("📖 Learn", use_container_width=True, key="home_learn"):
            st.session_state["learn_section"] = "Learn"
            _nav("Learn")
        if st.button("⚙ Settings", use_container_width=True, key="home_settings"):
            st.info("Game settings live in the sidebar under **Game settings**.")

    if journey:
        st.markdown("### Your Journey")
        a,b,c = st.columns(3)
        a.metric("Words discovered", journey.get("words_discovered", 0))
        b.metric("Discovery score", journey.get("discovery_score", 0))
        c.metric("Rare discoveries", journey.get("rare_discoveries", 0))
    elif not nickname:
        st.caption("Choose a nickname in the sidebar to keep a persistent journey when the cloud database is enabled.")


def render_puzzle_card(puzzle: Any, game: Mapping[str, Any], grammar_confidence: int, grammar_band: str) -> None:
    diff = game.get("difficulty") or {}
    st.markdown(f"""
    <div class="pf-card">
      <div class="pf-kicker">{str(game.get('mode','Practice')).upper()} · {str(game.get('generation_source','curated phrase bank')).upper()}</div>
      <div class="pf-phrase">{puzzle.word1.upper()} {puzzle.word2.upper()}</div>
      <div style="text-align:center">
        <span class="pf-pill">Difficulty: {diff.get('tier','Analyzing…')}</span>
        <span class="pf-pill">{diff.get('solutions_found',0)} validated solutions</span>
        <span class="pf-pill">Grammar: {grammar_confidence}% · {grammar_band}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_celebration(best_result: Mapping[str, Any]) -> None:
    word = str(best_result.get("solution", "")).upper()
    score = best_result.get("combined_score", best_result.get("score_final", best_result.get("score_base", 0)))
    learning = best_result.get("learning") or {}
    label = learning.get("discovery_label", "Vocabulary Discovery")
    st.markdown(f"""
    <div class="pf-success">
      <div style="font-size:1.8rem">🎉</div>
      <h3 style="margin:.2rem 0">Great Find!</h3>
      <div class="pf-success-word">{word}</div>
      <div><strong>{score} points</strong></div>
      <div class="pf-muted" style="margin-top:.3rem">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_learning_card(word: str, learning: Mapping[str, Any]) -> None:
    roles = ", ".join(learning.get("part_of_speech") or []) or "Not yet classified"
    definition = learning.get("definition") or "Definition not yet curated in the Phrase Forge Lexicon."
    st.markdown(f"""
    <div class="pf-card">
      <div class="pf-kicker">WORD CARD</div>
      <h3>{word.upper()}</h3>
      <span class="pf-pill">{roles}</span>
      <span class="pf-pill">{learning.get('frequency_label','Frequency unknown')}</span>
      <span class="pf-pill">+{learning.get('discovery_points',0)} discovery</span>
      <p style="margin-top:.8rem"><strong>Definition</strong><br>{definition}</p>
    </div>
    """, unsafe_allow_html=True)


def render_theme_hub(categories: Mapping[str, Any]) -> None:
    st.markdown("## 🪄 Theme Packs")
    st.caption("Explore curated language worlds. Theme selection changes content, not Phrase Forge rules.")
    names = sorted(categories, key=lambda x: str(x).lower())
    if not names:
        st.info("Theme packs are being prepared from the curated phrase bank.")
        return
    cols = st.columns(3)
    for i, name in enumerate(names[:12]):
        count = categories[name]
        with cols[i % 3]:
            st.markdown(f'<div class="pf-card"><div class="pf-kicker">THEME</div><h3>{str(name).title()}</h3><div class="pf-muted">{count} curated phrase records</div></div>', unsafe_allow_html=True)
    st.markdown("### ✨ Create a Theme")
    st.info("AI-assisted theme generation is planned for the next content sprint. AI will inspire candidates; Phrase Forge will validate every playable puzzle.")
