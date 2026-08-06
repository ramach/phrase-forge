from __future__ import annotations

from datetime import date
from typing import Dict, Optional

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from game_backend import (
    Puzzle,
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
)
from leaderboard_db import init_db, submit_score, top_scores

st.set_page_config(page_title="Phrase Forge", page_icon="🔤", layout="wide")
init_db()

ROLE_OPTIONS = ["noun", "verb", "adjective", "adverb", "pronoun", "preposition", "conjunction", "determiner", "interjection", "proper noun", "auxiliary", "other"]


def settings_signature(len_a: int, len_b: int, allow_swap: bool, min_letters: int, require_english: bool) -> str:
    return f"{len_a}:{len_b}:{int(allow_swap)}:{min_letters}:{int(require_english)}"


def new_game_state(
    mode: str,
    puzzle: Puzzle,
    min_letters: int,
    require_english: bool,
    signature: str,
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
    }


def replace_game(mode: str, puzzle: Puzzle, min_letters: int, require_english: bool, signature: str) -> None:
    puzzle_date = date.today() if mode == "Daily" else None
    st.session_state.games[mode] = new_game_state(
        mode, puzzle, min_letters, require_english, signature, puzzle_date
    )


def ensure_state() -> None:
    pending_mode = st.session_state.pop("pending_active_mode", None)
    if pending_mode in {"Daily", "Practice"}:
        st.session_state["active_mode"] = pending_mode
    else:
        st.session_state.setdefault("active_mode", "Daily")
    st.session_state.setdefault("games", {})
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("manual_word1", "rain")
    st.session_state.setdefault("manual_word2", "delay")
    st.session_state.setdefault("manual_label", "rain delay")


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
st.caption("Forge a valid English word from the letters in a recognized phrase or your own word pair.")

with st.sidebar:
    st.header("Game settings")
    mode = st.radio("Mode", ["Daily", "Practice"], key="active_mode")
    len_a = int(st.number_input("Word length A", 2, 12, 5, 1))
    len_b = int(st.number_input("Word length B", 2, 12, 4, 1))
    allow_swap = st.checkbox("Allow swapped lengths", True)
    min_mode = st.radio("Minimum solution length", ["total - 2", "custom"])
    configured_min = (
        int(st.number_input("Custom consonant minimum", 1, 24, max(1, len_a + len_b - 2), 1))
        if min_mode == "custom"
        else max(1, len_a + len_b - 2)
    )
    require_english = st.checkbox("Require English dictionary word", True)
    signature = settings_signature(len_a, len_b, allow_swap, configured_min, require_english)

    if mode not in st.session_state.games:
        try:
            initial = pick_daily_puzzle(date.today(), len_a, len_b, allow_swap) if mode == "Daily" else pick_puzzle(len_a, len_b, allow_swap)
        except ValueError:
            initial = make_puzzle("rain", "delay", "rain delay")
        replace_game(mode, initial, configured_min, require_english, signature)

    game = current_game()
    settings_changed = game.get("settings_signature") != signature
    if settings_changed:
        st.warning("Settings changed. Generate a compatible puzzle to apply them.")

    if st.button("🎲 Generate compatible puzzle", use_container_width=True):
        try:
            generated = pick_daily_puzzle(date.today(), len_a, len_b, allow_swap) if mode == "Daily" else pick_puzzle(len_a, len_b, allow_swap)
            replace_game(mode, generated, configured_min, require_english, signature)
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

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
            custom_signature = settings_signature(len(custom.word1), len(custom.word2), False, custom_min, require_english)

            validated_candidates = build_validated_hint_candidates(
                custom,
                min_letters_used=custom_min,
                require_english=require_english,
                limit=200,
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

            replace_game("Practice", custom, custom_min, require_english, custom_signature)
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

play_tab, leaderboard_tab, admin_tab = st.tabs(["🎮 Play", "🏆 Leaderboard", "🧰 Admin"])

with play_tab:
    top_left, top_mid, top_right = st.columns([2, 1, 1])
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
            st.metric("Difficulty", game["difficulty"]["tier"])
        else:
            st.metric("Difficulty", "Not calculated")
        st.write(f"Available letters: **{puzzle.total_len}**")

    normal_min = min_letters
    vowel_min = max(1, normal_min - 1)
    st.info(
        f"Minimum length: **{normal_min}** for consonant-starting solutions; "
        f"**{vowel_min}** for vowel-starting solutions."
    )
    st.code(" ".join(sorted(puzzle.word1 + puzzle.word2)).upper(), language="text")

    phrase_metadata = get_contextual_phrase_metadata(puzzle)
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
                        grade_solution(puzzle, line, min_letters, require_english_for_game),
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
            cache_key = f"{game['puzzle_id']}:{min_letters}:{int(require_english_for_game)}"
            if game.get("hint_cache_key") != cache_key:
                game["hint_candidates"] = build_validated_hint_candidates(
                    puzzle, min_letters, require_english_for_game, limit=200
                )
                game["hint_cache_key"] = cache_key
                game["hint_level"] = 0
                game["used_hint_ids"] = set()
                game["used_hint_solutions"] = set()
                game["hint_target_solution"] = None
                game["hint_history"] = []
                game["hint_complete"] = False

            if int(game["hint_level"]) >= 6:
                game["hint_complete"] = True
            else:
                if game.get("hint_target_solution") is None and game["hint_candidates"]:
                    game["hint_target_solution"] = game["hint_candidates"][0]["solution"]
                target = game.get("hint_target_solution")
                ordered_candidates = sorted(
                    game["hint_candidates"],
                    key=lambda item: item["solution"] != target,
                )
                hint = create_progressive_hint(
                    ordered_candidates,
                    int(game["hint_level"]),
                    set(),
                )
                if hint["id"] not in game["used_hint_ids"]:
                    game["hint_history"].append(hint)
                    game["used_hint_ids"].add(hint["id"])
                game["hint_level"] = int(game["hint_level"]) + 1

    with difficulty_col:
        if st.button("📊 Calculate difficulty", use_container_width=True):
            game["difficulty"] = compute_difficulty(puzzle, min_letters)

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
        "difficulty": game.get("difficulty"),
        "validated_hint_candidates": len(game.get("hint_candidates", [])),
    })
    if st.button("Generate validated solutions", key="admin_generate"):
        game["hint_candidates"] = build_validated_hint_candidates(
            puzzle, min_letters, require_english_for_game, limit=200
        )
        game["hint_cache_key"] = f"{game['puzzle_id']}:{min_letters}:{int(require_english_for_game)}"
    if game.get("hint_candidates"):
        st.dataframe(game["hint_candidates"], use_container_width=True, hide_index=True)

    st.divider()
    with st.expander("Session history"):
        if not st.session_state.history:
            st.write("No plays yet.")
        for item in reversed(st.session_state.history):
            st.write(
                f"{item['mode']} · {item['puzzle_id']} · {item['words']} · "
                f"{len(item['solutions'])} submitted solution(s)"
            )
