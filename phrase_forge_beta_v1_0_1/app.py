from __future__ import annotations

from datetime import date
import json
import os
import uuid
from typing import Dict, Optional

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from game_backend import (
    Puzzle,
    all_valid_solutions,
    apply_bonus_score,
    build_validated_hint_candidates,
    compute_difficulty,
    create_progressive_hint,
    explain_answer_attempt,
    explain_solution,
    grade_solution,
    grade_word_roles,
    get_phrase_metadata,
    get_contextual_phrase_metadata,
    make_puzzle,
    pick_daily_puzzle,
    pick_puzzle,
    puzzle_id_from_words,
    phrase_bank_stats,
    lexicon_profiles,
    get_word_info,
    solver_index_stats,
)
from leaderboard_db import (
    init_db, submit_score, top_scores, submit_feedback, list_feedback,
    db_backend_name, usage_summary, record_event,
)

try:
    from ai_puzzle_generator import generate_validated_ai_puzzle, ai_generation_available
except ImportError:
    generate_validated_ai_puzzle = None
    ai_generation_available = lambda: False

st.set_page_config(page_title="Phrase Forge", page_icon="🔤", layout="wide")

# Streamlit Community Cloud stores secrets in st.secrets. Mirror only the
# application settings we explicitly support into environment variables so
# backend modules can remain Streamlit-independent and Colab-compatible.
for _secret_key in ("DATABASE_URL", "PHRASE_FORGE_DATABASE_URL", "OPENAI_API_KEY",
                    "PHRASE_FORGE_OPENAI_MODEL", "PHRASE_FORGE_AI_SESSION_LIMIT"):
    try:
        if _secret_key in st.secrets and not os.getenv(_secret_key):
            os.environ[_secret_key] = str(st.secrets[_secret_key])
    except Exception:
        pass

init_db()

APP_VERSION = "1.0.1-beta"
BUILD_DATE = "2026.08.09"
AI_SESSION_LIMIT = max(0, int(os.getenv("PHRASE_FORGE_AI_SESSION_LIMIT", "3")))

ROLE_OPTIONS = ["noun", "verb", "adjective", "adverb", "pronoun", "preposition", "conjunction", "determiner", "interjection", "proper noun", "auxiliary", "other"]


def settings_signature(len_a: int, len_b: int, allow_swap: bool, min_letters: int, require_english: bool, lexicon_profile: str) -> str:
    return f"{len_a}:{len_b}:{int(allow_swap)}:{min_letters}:{int(require_english)}:{lexicon_profile.lower()}"


def new_game_state(
    mode: str,
    puzzle: Puzzle,
    min_letters: int,
    require_english: bool,
    signature: str,
    lexicon_profile: str = "standard",
    puzzle_date: Optional[date] = None,
) -> Dict[str, object]:
    puzzle_id = puzzle_id_from_words(
        puzzle.word1,
        puzzle.word2,
        len(puzzle.word1),
        len(puzzle.word2),
        day=puzzle_date if mode == "Daily" else None,
        mode=mode,
    )
    return {
        "mode": mode,
        "puzzle": puzzle,
        "puzzle_id": puzzle_id,
        "puzzle_date": puzzle_date.isoformat() if puzzle_date else None,
        "difficulty": None,
        "settings_signature": signature,
        "min_letters": min_letters,
        "require_english": require_english,
        "lexicon_profile": lexicon_profile.lower(),
        "generation_source": "curated phrase bank",
        "grade_results": [],
        "best_result": None,
        "hint_candidates": [],
        "hint_cache_key": None,
        "hint_level": 0,
        "used_hint_ids": set(),
        "used_hint_solutions": set(),
        "hint_target_solution": None,
        "hint_history": [],
        "leaderboard_status": None,
        "solutions_text": "",
        "bonus_phrase": "",
        "role_result": None,
        "show_all_solutions": False,
        "all_solutions": [],
        "all_solutions_cache_key": None,
    }


def replace_game(mode: str, puzzle: Puzzle, min_letters: int, require_english: bool, signature: str, lexicon_profile: str = "standard") -> None:
    puzzle_date = date.today() if mode == "Daily" else None
    st.session_state.games[mode] = new_game_state(
        mode, puzzle, min_letters, require_english, signature, lexicon_profile, puzzle_date
    )


def ensure_state() -> None:
    pending_mode = st.session_state.pop("pending_active_mode", None)
    if pending_mode in {"Daily", "Practice"}:
        st.session_state["active_mode"] = pending_mode
    else:
        st.session_state.setdefault("active_mode", "Practice")
    st.session_state.setdefault("games", {})
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("manual_word1", "rain")
    st.session_state.setdefault("manual_word2", "delay")
    st.session_state.setdefault("manual_label", "rain delay")
    st.session_state.setdefault("show_welcome", True)
    st.session_state.setdefault("beta_session_id", uuid.uuid4().hex[:12])
    st.session_state.setdefault("ai_generations_used", 0)
    st.session_state.setdefault("feedback_status", None)


def render_results(game: Dict[str, object]) -> None:
    results = game.get("grade_results", [])
    if not results:
        st.info("Grade one or more solutions to see results here.")
        return

    puzzle = game["puzzle"]
    min_letters = int(game.get("min_letters", max(1, puzzle.total_len - 2)))
    require_english = bool(game.get("require_english", True))
    bonus_phrase = str(game.get("bonus_phrase", ""))

    for result in results:
        solution = result.get("solution", "")
        attempted = result.get("raw_input", solution)
        if result.get("ok"):
            score = result.get("combined_score", result.get("score_final", result.get("score_base", 0)))
            st.markdown(f"### ✅ `{solution}` — **{score} points**")
        else:
            st.markdown(f"### ❌ `{attempted or '(empty)'}`")
            st.error(result.get("reason", "Invalid solution."))

        analysis = explain_answer_attempt(
            puzzle,
            result,
            min_letters_used=min_letters,
            require_english=require_english,
            bonus_phrase=bonus_phrase,
            lexicon_profile=lexicon_profile_for_game,
        )
        with st.expander(f"🔎 Explain My Answer: {attempted or '(empty)'}", expanded=not result.get("ok")):
            st.write(analysis.get("summary", ""))
            for check in analysis.get("checks", []):
                icon = "✅" if check.get("passed") else "❌"
                st.markdown(f"**{icon} {check.get('label')}**")
                st.caption(check.get("detail", ""))

            if result.get("ok"):
                st.divider()
                st.markdown("**Score breakdown**")
                st.write(f"Base score: **{analysis.get('base_score')}**")
                st.write(f"Forged-word score: **{analysis.get('word_score')}**")
                st.write(f"Grammar role bonus: **+{analysis.get('role_bonus', 0)}**")
                st.write(f"Combined score: **{analysis.get('combined_score')}**")
                word_meta = result.get("lexicon") or get_word_info(solution, lexicon_profile_for_game)
                if word_meta:
                    st.write(f"Lexicon: **{word_meta.get('profile', lexicon_profile_for_game).title()}** · {word_meta.get('frequency') or 'frequency unknown'} · source: {word_meta.get('source')}")
                    if word_meta.get("definition"):
                        st.caption(word_meta["definition"])
                explanation = explain_solution(puzzle, result)
                for reason in explanation.get("score_reason", []):
                    st.write(f"• {reason}")

            left, right = st.columns(2)
            with left:
                st.markdown("**Letters used**")
                st.json(analysis.get("letters_used", {}))
            with right:
                st.markdown("**Letters remaining**")
                st.json(analysis.get("letters_remaining", {}))

            if analysis.get("overuse"):
                st.markdown("**Excess letters**")
                st.json(analysis["overuse"])


def current_game() -> Dict[str, object]:
    return st.session_state.games[st.session_state.active_mode]


ensure_state()

st.title("🔤 Phrase Forge")
st.caption("Discover the language hidden inside language. · Beta 1.0")
st.caption(f"Version {APP_VERSION} · Build {BUILD_DATE}")

with st.container(border=True):
    st.subheader("How to play")
    st.markdown(
        """
**Your goal:** start with a familiar two-word phrase, then forge a different English word from its letters.

1. Identify the grammatical role of each phrase word.
2. Build a new English word using only the available letters; repeated letters may be used only as often as they appear.
3. Your answer may not contain either complete input word.
4. A consonant-starting answer normally needs `total letters − 2`; a vowel-starting answer may be one letter shorter.
5. Use your answer as a standalone word in a sentence for the sentence bonus.

**Example:** `RAIN DELAY` → `ALREADY`
        """
    )
    st.info(
        "Practice starts each fresh browser session with a curated random puzzle. "
        "Use **New random puzzle** for another. Daily intentionally gives everyone the same puzzle for that date."
    )

with st.sidebar:
    st.header("Game settings")
    mode = st.radio(
        "Mode",
        ["Practice", "Daily"],
        key="active_mode",
        format_func=lambda value: "Practice — random puzzle for me" if value == "Practice" else "Daily — same puzzle for everyone today",
    )
    len_a = int(st.number_input("Word length A", 2, 12, 5, 1))
    len_b = int(st.number_input("Word length B", 2, 12, 4, 1))
    allow_swap = st.checkbox("Allow swapped lengths", True)
    min_mode = st.radio("Minimum solution length", ["total - 2", "custom"])
    configured_min = (
        int(st.number_input("Custom consonant minimum", 1, 24, max(1, len_a + len_b - 2), 1))
        if min_mode == "custom"
        else max(1, len_a + len_b - 2)
    )
    require_english = st.checkbox("Require Phrase Forge Lexicon word", True)
    profile_map = lexicon_profiles()
    lexicon_profile = st.selectbox(
        "Lexicon profile",
        list(profile_map.keys()),
        index=list(profile_map.keys()).index("standard") if "standard" in profile_map else 0,
        format_func=lambda key: profile_map[key].get("label", key.title()),
        help="Casual uses common words; Standard is the beta default; Expert/Teacher allow rarer vocabulary. Names and pronouns remain excluded by default.",
    )
    st.caption(profile_map[lexicon_profile].get("description", ""))
    signature = settings_signature(len_a, len_b, allow_swap, configured_min, require_english, lexicon_profile)

    if mode not in st.session_state.games:
        try:
            initial = pick_daily_puzzle(date.today(), len_a, len_b, allow_swap) if mode == "Daily" else pick_puzzle(len_a, len_b, allow_swap)
        except ValueError:
            initial = make_puzzle("rain", "delay", "rain delay")
        replace_game(mode, initial, configured_min, require_english, signature, lexicon_profile)

    game = current_game()
    settings_changed = game.get("settings_signature") != signature
    if settings_changed:
        st.warning("Settings changed. Generate a compatible puzzle to apply them.")

    if st.button("🎲 New random puzzle" if mode == "Practice" else "📅 Load today’s Daily puzzle", use_container_width=True):
        try:
            if mode == "Daily":
                generated = pick_daily_puzzle(date.today(), len_a, len_b, allow_swap)
            else:
                existing_puzzle = current_game().get("puzzle")
                exclude = (existing_puzzle.word1, existing_puzzle.word2) if existing_puzzle else None
                generated = pick_puzzle(len_a, len_b, allow_swap, exclude_words=exclude)
            replace_game(mode, generated, configured_min, require_english, signature, lexicon_profile)
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("AI puzzle generator — Beta")
    st.caption("AI suggests a phrase, but Phrase Forge accepts it only after the local solver proves that at least one legal answer exists.")
    if ai_generation_available():
        remaining_ai = max(0, AI_SESSION_LIMIT - int(st.session_state.ai_generations_used))
        st.caption(f"Optional AI generations remaining this session: {remaining_ai} of {AI_SESSION_LIMIT}")
        if st.button(
            "✨ Generate AI puzzle",
            use_container_width=True,
            disabled=remaining_ai <= 0,
            help="AI proposes a phrase; the deterministic Phrase Forge engine must validate it before play.",
        ):
            try:
                with st.spinner("Generating and validating a fresh puzzle..."):
                    generated_ai = generate_validated_ai_puzzle(
                        len_a=len_a,
                        len_b=len_b,
                        allow_swap=allow_swap,
                        min_letters=configured_min,
                        require_english=require_english,
                        lexicon_profile=lexicon_profile,
                    )
                custom = generated_ai["puzzle"]
                replace_game("Practice", custom, configured_min, require_english, signature, lexicon_profile)
                ai_game = st.session_state.games["Practice"]
                ai_game["hint_candidates"] = generated_ai["validated_candidates"]
                ai_game["difficulty"] = generated_ai["difficulty"]
                ai_game["generation_source"] = "OpenAI beta generator; locally validated"
                st.session_state.ai_generations_used += 1
                st.session_state["pending_active_mode"] = "Practice"
                st.rerun()
            except Exception as exc:
                st.error(f"AI generation could not produce a valid puzzle: {exc}")
    else:
        st.info("AI generation is optional. Add `OPENAI_API_KEY` to Streamlit secrets to enable it. Curated random Practice puzzles continue to work without an API key.")

    st.divider()
    st.subheader("Use your own words")
    st.caption("Custom word pairs are created as Practice puzzles.")
    manual_word1 = st.text_input("Word 1", key="manual_word1")
    manual_word2 = st.text_input("Word 2", key="manual_word2")
    manual_label = st.text_input("Phrase label", key="manual_label")
    if st.button("🛠️ Forge these words", use_container_width=True):
        try:
            custom = make_puzzle(manual_word1, manual_word2, manual_label)
            custom_min = max(1, custom.total_len - 2) if min_mode == "total - 2" else configured_min
            custom_signature = settings_signature(len(custom.word1), len(custom.word2), False, custom_min, require_english, lexicon_profile)

            validated_candidates = build_validated_hint_candidates(
                custom,
                min_letters_used=custom_min,
                require_english=require_english,
                limit=200,
                lexicon_profile=lexicon_profile,
            )
            if not validated_candidates:
                consonant_min = custom_min
                vowel_min = max(1, custom_min - 1)
                raise ValueError(
                    "No valid solution was found for this word pair under the current rules. "
                    f"A consonant-starting answer needs at least {consonant_min} letters, "
                    f"and a vowel-starting answer needs at least {vowel_min}. "
                    "Try another pair or adjust the minimum-length/dictionary setting."
                )

            replace_game("Practice", custom, custom_min, require_english, custom_signature, lexicon_profile)
            practice_game = st.session_state.games["Practice"]
            practice_game["hint_candidates"] = validated_candidates
            practice_game["hint_cache_key"] = (
                practice_game["puzzle_id"],
                custom_min,
                require_english,
            )
            practice_game["difficulty"] = compute_difficulty(
                custom,
                min_consonant_len=custom_min,
                lexicon_profile=lexicon_profile,
            )
            st.session_state["pending_active_mode"] = "Practice"
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

# Refresh after sidebar actions.
game = current_game()
puzzle: Puzzle = game["puzzle"]
min_letters = int(game["min_letters"])
require_english_for_game = bool(game["require_english"])
lexicon_profile_for_game = str(game.get("lexicon_profile", "standard"))

play_tab, leaderboard_tab, feedback_tab, admin_tab = st.tabs(["🎮 Play", "🏆 Leaderboard", "💬 Feedback", "🧰 Admin"])

with play_tab:
    if game.get("difficulty") is None:
        with st.spinner("Analyzing puzzle difficulty..."):
            game["difficulty"] = compute_difficulty(puzzle, min_letters, lexicon_profile=lexicon_profile_for_game)
    phrase_metadata = get_contextual_phrase_metadata(puzzle)
    grammar_confidence = int(round(float(phrase_metadata.get("confidence", 1.0)) * 100))
    grammar_band = str(phrase_metadata.get("confidence_band", "curated")).title()

    top_left, top_mid, top_right, confidence_col = st.columns([2, 1, 1, 1])
    with top_left:
        st.subheader(puzzle.phrase_label)
        st.markdown(f"## **{puzzle.word1.upper()} {puzzle.word2.upper()}**")
    with top_mid:
        st.metric("Puzzle ID", game["puzzle_id"])
        st.write(f"Mode: **{game['mode']}**")
        if game.get("puzzle_date"):
            st.write(f"Date: **{game['puzzle_date']}**")
    with top_right:
        if game.get("difficulty"):
            difficulty = game["difficulty"]
            st.metric("Difficulty", difficulty["tier"])
            st.caption(f"{difficulty.get('solutions_found', 0)} validated solutions found")
        else:
            st.metric("Difficulty", "Unavailable")
            st.caption("Difficulty analysis could not be completed.")
        st.write(f"Available letters: **{puzzle.total_len}**")
    with confidence_col:
        st.metric("Grammar confidence", f"{grammar_confidence}%")
        st.caption(f"{grammar_band} · {phrase_metadata.get('source', 'curated phrase bank')}")

    st.caption(f"Phrase Forge Lexicon profile: **{lexicon_profile_for_game.title()}** · Database: **{db_backend_name()}**")

    normal_min = min_letters
    vowel_min = max(1, normal_min - 1)
    st.info(
        f"Minimum length: **{normal_min}** for consonant-starting solutions; "
        f"**{vowel_min}** for vowel-starting solutions."
    )
    st.code(" ".join(sorted(puzzle.word1 + puzzle.word2)).upper(), language="text")

    # Spoiler-controlled solution list. This uses the same grader and rule
    # configuration as difficulty, hints, and player submissions.
    solution_cache_key = (
        str(game["puzzle_id"]),
        int(min_letters),
        bool(require_english_for_game),
        lexicon_profile_for_game,
    )
    spoiler_left, spoiler_right = st.columns([1, 3])
    with spoiler_left:
        spoiler_label = "🙈 Hide all solutions" if game.get("show_all_solutions") else "👀 Show all solutions"
        if st.button(
            spoiler_label,
            key=f"toggle_all_solutions_{game['puzzle_id']}",
            use_container_width=True,
            help="Spoiler: reveals every solution validated under the current rules.",
        ):
            game["show_all_solutions"] = not bool(game.get("show_all_solutions"))
            if game["show_all_solutions"]:
                stored_solution_key = game.get("all_solutions_cache_key")
                if isinstance(stored_solution_key, list):
                    stored_solution_key = tuple(stored_solution_key)
                if stored_solution_key != solution_cache_key or not game.get("all_solutions"):
                    with st.spinner("Finding every validated solution..."):
                        game["all_solutions"] = all_valid_solutions(
                            puzzle,
                            min_consonant_len=min_letters,
                            require_english=require_english_for_game,
                            limit=5000,
                            lexicon_profile=lexicon_profile_for_game,
                        )
                    game["all_solutions_cache_key"] = solution_cache_key
                    game["difficulty"] = {
                        "solutions_found": len(game["all_solutions"]),
                        "tier": (game.get("difficulty") or {}).get("tier"),
                        "capped_at": 5000,
                    }
                    # Recompute the tier through the shared difficulty function so
                    # the displayed count and difficulty remain synchronized.
                    game["difficulty"] = compute_difficulty(puzzle, min_letters, lexicon_profile=lexicon_profile_for_game)
            st.session_state.games[game["mode"]] = game
            st.rerun()

    if game.get("show_all_solutions"):
        stored_solution_key = game.get("all_solutions_cache_key")
        if isinstance(stored_solution_key, list):
            stored_solution_key = tuple(stored_solution_key)
        if stored_solution_key != solution_cache_key or not game.get("all_solutions"):
            game["all_solutions"] = all_valid_solutions(
                puzzle,
                min_consonant_len=min_letters,
                require_english=require_english_for_game,
                limit=5000,
                lexicon_profile=lexicon_profile_for_game,
            )
            game["all_solutions_cache_key"] = solution_cache_key
            st.session_state.games[game["mode"]] = game

        solution_rows = [
            {
                "Solution": item["solution"],
                "Length": item.get("len", len(item["solution"])),
                "Starts with": "Vowel" if item.get("starts_with_vowel") else "Consonant",
                "Base score": item.get("score_base", 0),
            }
            for item in game.get("all_solutions", [])
        ]
        with st.expander(
            f"⚠️ Spoiler — all {len(solution_rows)} validated solutions",
            expanded=True,
        ):
            if solution_rows:
                st.dataframe(solution_rows, use_container_width=True, hide_index=True)
                st.caption(
                    "These answers passed the same letter, length, substring, and dictionary checks used when grading player submissions."
                )
            else:
                st.info("No validated solutions were found under the current rules.")

    if phrase_metadata.get("meaning") or phrase_metadata.get("example"):
        with st.expander("📘 Phrase meaning and usage", expanded=False):
            st.write(f"**Meaning:** {phrase_metadata.get('meaning') or 'Not available.'}")
            st.write(f"**Example:** {phrase_metadata.get('example') or 'Not available.'}")
    if phrase_metadata.get("inferred"):
        confidence = int(round(float(phrase_metadata.get("confidence", 0)) * 100))
        band = phrase_metadata.get("confidence_band", "unknown").title()
        st.caption(
            f"Grammar roles will be automatically inferred using {phrase_metadata.get('source', 'the grammar engine')} "
            f"(estimated confidence: {confidence}% — {band})."
        )

    role_left, role_right = st.columns(2)
    with role_left:
        role1 = st.selectbox(f"Role of '{puzzle.word1}'", ROLE_OPTIONS, key=f"role1_{game['puzzle_id']}")
    with role_right:
        role2 = st.selectbox(f"Role of '{puzzle.word2}'", ROLE_OPTIONS, key=f"role2_{game['puzzle_id']}")

    solutions_text = st.text_area(
        "Enter one solution per line",
        value=game.get("solutions_text", ""),
        height=140,
        key=f"solutions_{game['puzzle_id']}",
    )
    bonus_phrase = st.text_input(
        "Bonus sentence or phrase",
        value=game.get("bonus_phrase", ""),
        key=f"bonus_{game['puzzle_id']}",
        help="The solution must appear as an exact standalone word.",
    )

    grade_col, hint_col, difficulty_col = st.columns(3)
    with grade_col:
        if st.button("✅ Grade solutions", type="primary", use_container_width=True):
            lines = [line.strip() for line in solutions_text.splitlines() if line.strip()]
            if not lines:
                st.warning("Enter at least one solution.")
            else:
                role_result = grade_word_roles(puzzle, role1, role2)
                results = [
                    apply_bonus_score(
                        grade_solution(puzzle, line, min_letters, require_english_for_game, lexicon_profile=lexicon_profile_for_game),
                        bonus_phrase,
                    )
                    for line in lines
                ]
                role_points = int(role_result.get("points", 0))
                for result in results:
                    if result.get("ok"):
                        word_score = int(result.get("score_final", result.get("score_base", 0)))
                        result["word_score"] = word_score
                        result["role_bonus"] = role_points
                        result["combined_score"] = word_score + role_points
                valid = [result for result in results if result.get("ok")]
                best = max(valid, key=lambda item: item.get("combined_score", item.get("score_final", 0)), default=None)
                game["solutions_text"] = solutions_text
                game["bonus_phrase"] = bonus_phrase
                game["grade_results"] = results
                game["role_result"] = role_result
                game["best_result"] = best
                game["leaderboard_status"] = None
                st.session_state.grade_results = results
                st.session_state.history.append({
                    "mode": game["mode"],
                    "puzzle_id": game["puzzle_id"],
                    "words": f"{puzzle.word1} {puzzle.word2}",
                    "roles": (role1, role2),
                    "solutions": results,
                    "bonus": bonus_phrase,
                })
                st.success("Grading complete." if valid else "Grading complete; no valid solutions found.")

    with hint_col:
        if st.button("💡 Next hint", use_container_width=True):
            cache_key = (
                str(game["puzzle_id"]),
                int(min_letters),
                bool(require_english_for_game),
                lexicon_profile_for_game,
            )

            # Rebuild only when the puzzle or grading rules actually change.
            # A normal Streamlit rerun must preserve hint level and history.
            stored_key = game.get("hint_cache_key")
            if isinstance(stored_key, list):
                stored_key = tuple(stored_key)
            if stored_key != cache_key or not game.get("hint_candidates"):
                game["hint_candidates"] = build_validated_hint_candidates(
                    puzzle, min_letters, require_english_for_game, limit=200,
                    lexicon_profile=lexicon_profile_for_game,
                )
                game["hint_cache_key"] = cache_key
                game["hint_level"] = 0
                game["used_hint_ids"] = set()
                game["used_hint_solutions"] = set()
                game["hint_target_solution"] = None
                game["hint_history"] = []
                game["hint_complete"] = False

            level = int(game.get("hint_level", 0))
            if level >= 8:
                game["hint_complete"] = True
            elif not game.get("hint_candidates"):
                game["hint_complete"] = True
                if not game.get("hint_history"):
                    game["hint_history"] = [{
                        "id": "none",
                        "type": "none",
                        "text": "No validated hint candidate exists for this puzzle and rule configuration.",
                    }]
            else:
                if game.get("hint_target_solution") is None:
                    game["hint_target_solution"] = game["hint_candidates"][0]["solution"]

                target = game["hint_target_solution"]
                ordered_candidates = sorted(
                    game["hint_candidates"],
                    key=lambda item: item["solution"] != target,
                )
                hint = create_progressive_hint(
                    ordered_candidates,
                    level,
                    set(game.get("used_hint_solutions", set())),
                )
                if hint["id"] not in set(game.get("used_hint_ids", set())):
                    game.setdefault("hint_history", []).append(hint)
                    game.setdefault("used_hint_ids", set()).add(hint["id"])
                game["hint_level"] = level + 1
                game["hint_complete"] = game["hint_level"] >= 8

            # Persist the mutated game explicitly for hosted Streamlit sessions.
            st.session_state.games[game["mode"]] = game
            st.rerun()

    with difficulty_col:
        difficulty_label = "📊 Recalculate difficulty" if game.get("difficulty") else "📊 Calculate difficulty"
        if st.button(difficulty_label, use_container_width=True):
            with st.spinner("Checking validated solutions..."):
                game["difficulty"] = compute_difficulty(puzzle, min_letters, lexicon_profile=lexicon_profile_for_game)
            st.rerun()

    if game.get("hint_history"):
        st.subheader("Hint progression")
        for number, hint in enumerate(game["hint_history"], 1):
            st.write(f"**Hint {number}:** {hint['text']}")
        if game.get("hint_complete"):
            st.info("All progressive hint levels have been shown for this puzzle.")

    role_result = game.get("role_result")
    if role_result:
        st.divider()
        st.subheader("Grammar role result")
        if role_result.get("available"):
            if role_result.get("inferred"):
                confidence = int(round(float(role_result.get("confidence", 0)) * 100))
                band = role_result.get("confidence_band", "unknown").title()
                st.warning(
                    f"Automatically inferred grammar via {role_result.get('source', 'grammar engine')} "
                    f"(estimated confidence: {confidence}% — {band}). Curated metadata remains authoritative when available."
                )
            st.metric(
                "Role-identification bonus",
                f"+{role_result.get('points', 0)} / {role_result.get('max_points', 10)}",
            )
            if not role_result.get("bonus_eligible", True):
                st.info(role_result.get("bonus_withheld_reason"))
            with st.expander("Why the grammar engine chose these roles", expanded=False):
                st.write(f"**Rule fired:** {role_result.get('rule_label') or role_result.get('rule_id') or 'Not recorded'}")
                st.write(f"**Reasoning:** {role_result.get('reasoning') or 'No diagnostic reasoning is available.'}")
                st.write(f"**Confidence band:** {str(role_result.get('confidence_band', 'unknown')).title()}")
            for item in role_result.get("items", []):
                mark = "✅" if item.get("ok") else "❌"
                st.markdown(
                    f"{mark} **{item.get('word', '').upper()}** — "
                    f"selected **{item.get('selected')}**; correct role: **{item.get('correct_role')}**"
                )
                st.caption(item.get("explanation", ""))
        else:
            st.info(role_result.get("reason", "No curated role key is available for this phrase."))

    st.divider()
    st.subheader("Submitted solutions")
    render_results(game)

    best_result = game.get("best_result")
    if best_result:
        st.divider()
        st.subheader("Submit best result")
        st.write(
            f"Best result: **{best_result['solution']}** — "
            f"**{best_result.get('combined_score', best_result.get('score_final', best_result.get('score_base')))} points**"
        )
        player = st.text_input("Player name", key=f"player_{game['puzzle_id']}")
        if st.button("🏆 Submit to leaderboard", use_container_width=True):
            try:
                response = submit_score(
                    day=game.get("puzzle_date"),
                    puzzle_id=str(game["puzzle_id"]),
                    words=f"{puzzle.word1} {puzzle.word2}",
                    difficulty=(game.get("difficulty") or {}).get("tier"),
                    player=player,
                    score=int(best_result.get("combined_score", best_result.get("score_final", best_result.get("score_base", 0)))),
                    solution=str(best_result["solution"]),
                    mode=str(game["mode"]),
                )
                game["leaderboard_status"] = response
            except ValueError as exc:
                st.error(str(exc))

        status = game.get("leaderboard_status")
        if status:
            if status["status"] == "kept_existing":
                st.info(f"Existing best score of {status['score']} was retained.")
            else:
                st.success(f"Leaderboard saved: {status['status'].replace('_', ' ')}.")

with leaderboard_tab:
    st.subheader("Leaderboard")
    scope = st.radio("View", ["Current puzzle", "All scores"], horizontal=True)
    rows = top_scores(
        puzzle_id=str(game["puzzle_id"]) if scope == "Current puzzle" else None,
        mode=str(game["mode"]) if scope == "Current puzzle" else None,
        limit=100,
    )
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No leaderboard entries yet.")

with feedback_tab:
    st.subheader("Beta feedback")
    st.write("Your feedback is most useful when it is tied to the exact puzzle and engine result shown here.")
    st.caption("The diagnostic snapshot is attached automatically; do not include private or sensitive information.")

    diagnostic = {
        "session_id": st.session_state.beta_session_id,
        "app_version": APP_VERSION,
        "build_date": BUILD_DATE,
        "mode": game.get("mode"),
        "puzzle_id": game.get("puzzle_id"),
        "words": f"{puzzle.word1} {puzzle.word2}",
        "phrase_label": puzzle.phrase_label,
        "settings": {
            "minimum_consonant_length": min_letters,
            "minimum_vowel_length": max(1, min_letters - 1),
            "require_english": require_english_for_game,
        },
        "difficulty": game.get("difficulty"),
        "grammar": get_contextual_phrase_metadata(puzzle),
        "submitted_text": game.get("solutions_text", ""),
        "grade_results": game.get("grade_results", []),
        "role_result": game.get("role_result"),
        "hint_history": game.get("hint_history", []),
        "generation_source": game.get("generation_source", "curated phrase bank"),
    }

    category = st.selectbox(
        "What kind of feedback is this?",
        ["Goal or onboarding", "Accepted/rejected word", "Grammar roles", "Hints", "Difficulty", "User interface", "Other"],
    )
    clarity = st.slider("How clear was the goal?", 1, 5, 4)
    enjoyment = st.slider("How enjoyable was this puzzle?", 1, 5, 4)
    play_again = st.radio("Would you play another five puzzles?", ["Yes", "Maybe", "No"], horizontal=True)
    comment = st.text_area(
        "What happened, or what should improve?",
        placeholder="For example: I entered KNEELER for LIKE NEVER, but the app rejected it...",
        height=130,
    )

    feedback_left, feedback_right = st.columns(2)
    with feedback_left:
        if st.button("Send beta feedback", type="primary", use_container_width=True):
            try:
                st.session_state.feedback_status = submit_feedback(
                    session_id=st.session_state.beta_session_id,
                    app_version=APP_VERSION,
                    puzzle_id=str(game["puzzle_id"]),
                    mode=str(game["mode"]),
                    words=f"{puzzle.word1} {puzzle.word2}",
                    category=category,
                    comment=comment,
                    diagnostic=diagnostic,
                    clarity_rating=clarity,
                    enjoyment_rating=enjoyment,
                    would_play_again=play_again,
                )
            except ValueError as exc:
                st.error(str(exc))
    with feedback_right:
        st.download_button(
            "Download diagnostic report",
            data=json.dumps(diagnostic, indent=2, ensure_ascii=False, default=str),
            file_name=f"phrase_forge_feedback_{game['puzzle_id']}.json",
            mime="application/json",
            use_container_width=True,
        )

    if st.session_state.feedback_status:
        st.success(
            f"Feedback saved for this beta session (ID {st.session_state.feedback_status['feedback_id']}). Thank you."
        )
    st.info(
        "On Streamlit Community Cloud, the current SQLite feedback store may reset after a restart or redeploy. "
        "The downloadable diagnostic report is a backup until a persistent cloud database is connected."
    )


with admin_tab:
    st.subheader("Phrase bank")
    bank_stats = phrase_bank_stats()
    bank_left, bank_mid, bank_right = st.columns(3)
    bank_left.metric("Curated records", bank_stats["total_records"])
    bank_mid.metric("Verified records", bank_stats["verified_records"])
    bank_right.metric("Random-enabled", bank_stats["random_enabled_records"])
    with st.expander("Phrase-bank categories and source"):
        st.write(f"Data file: `{bank_stats['data_path']}`")
        st.json(bank_stats["categories"])

    st.divider()
    st.subheader("Phrase Forge Lexicon Inspector")
    st.caption("Inspect the final gameplay decision for any word. Proper names and pronouns are excluded in every profile; profiles broaden rarity only.")
    inspect_word = st.text_input("Inspect a word", key="pfl_inspect_word", placeholder="e.g. ishtar, kneeler, whoever")
    if inspect_word.strip():
        inspection_rows = []
        for profile_name in lexicon_profiles():
            info = get_word_info(inspect_word, profile_name)
            inspection_rows.append({
                "profile": profile_name.title(),
                "accepted": bool(info.get("accepted")),
                "reason": info.get("reason") or "accepted",
                "category": info.get("category"),
                "frequency": info.get("frequency"),
                "zipf": info.get("zipf"),
                "source": info.get("source"),
            })
        st.dataframe(inspection_rows, use_container_width=True, hide_index=True)
        active_info = get_word_info(inspect_word, lexicon_profile_for_game)
        if active_info.get("accepted"):
            st.success(f"Accepted in {lexicon_profile_for_game.title()} profile.")
        else:
            st.warning(
                f"Rejected in {lexicon_profile_for_game.title()} profile: "
                f"{str(active_info.get('reason') or 'not accepted').replace('_', ' ')}."
            )

    st.divider()
    st.subheader("Current puzzle administration")
    st.caption("Admin intentionally references the same puzzle currently shown in Play.")
    st.json({
        "mode": game["mode"],
        "puzzle_id": game["puzzle_id"],
        "word1": puzzle.word1,
        "word2": puzzle.word2,
        "phrase_label": puzzle.phrase_label,
        "minimum_consonant_length": min_letters,
        "minimum_vowel_length": max(1, min_letters - 1),
        "require_english": require_english_for_game,
        "lexicon_profile": lexicon_profile_for_game,
        "difficulty": game.get("difficulty"),
        "validated_hint_candidates": len(game.get("hint_candidates", [])),
    })
    if st.button("Generate validated solutions", key="admin_generate"):
        game["hint_candidates"] = build_validated_hint_candidates(
            puzzle, min_letters, require_english_for_game, limit=200,
            lexicon_profile=lexicon_profile_for_game,
        )
        game["hint_cache_key"] = (game['puzzle_id'], min_letters, require_english_for_game, lexicon_profile_for_game)
    if game.get("hint_candidates"):
        st.dataframe(game["hint_candidates"], use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Beta diagnostics")
    diagnostics_payload = {
        "app_version": APP_VERSION,
        "build_date": BUILD_DATE,
        "session_id": st.session_state.beta_session_id,
        "ai_generations_used": st.session_state.ai_generations_used,
        "ai_session_limit": AI_SESSION_LIMIT,
        "current_game": {
            "mode": game.get("mode"),
            "puzzle_id": game.get("puzzle_id"),
            "generation_source": game.get("generation_source", "curated phrase bank"),
            "difficulty": game.get("difficulty"),
            "grammar": get_contextual_phrase_metadata(puzzle),
            "validated_candidates_cached": len(game.get("hint_candidates", [])),
            "graded_answers": len(game.get("grade_results", [])),
        },
    }
    st.json(diagnostics_payload)
    feedback_rows = list_feedback(limit=100)
    if feedback_rows:
        st.write(f"Feedback records in this app instance: **{len(feedback_rows)}**")
        st.dataframe(feedback_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No beta feedback has been saved in this app instance yet.")

    st.divider()
    with st.expander("Session history"):
        if not st.session_state.history:
            st.write("No plays yet.")
        for item in reversed(st.session_state.history):
            st.write(
                f"{item['mode']} · {item['puzzle_id']} · {item['words']} · "
                f"{len(item['solutions'])} submitted solution(s)"
            )
