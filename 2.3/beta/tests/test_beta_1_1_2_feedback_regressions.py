from game_backend import (
    Puzzle, all_valid_solutions, grade_solution, get_contextual_phrase_metadata
)


def test_spare_time_roles_adjective_noun():
    meta = get_contextual_phrase_metadata(Puzzle("spare", "time", "spare time"))
    assert tuple(meta["roles"]) == ("adjective", "noun")
    assert meta["confidence"] >= 0.90


def test_call_again_roles_verb_adverb():
    meta = get_contextual_phrase_metadata(Puzzle("call", "again", "call again"))
    assert tuple(meta["roles"]) == ("verb", "adverb")
    assert meta["confidence"] >= 0.90


def test_open_heart_accepts_earthen():
    p = Puzzle("open", "heart", "open heart")
    r = grade_solution(p, "earthen", min_letters_used=7, require_english=True, lexicon_profile="standard")
    assert r["ok"] is True
    assert r["score_base"] == 85
    sols = {x["solution"] for x in all_valid_solutions(p, 7, True, 500, lexicon_profile="standard")}
    assert "earthen" in sols


def test_data_entry_accepts_ardent_vowel_exception():
    p = Puzzle("data", "entry", "data entry")
    r = grade_solution(p, "ardent", min_letters_used=7, require_english=True, lexicon_profile="standard")
    assert r["ok"] is True
    assert r["starts_with_vowel"] is True
    assert r["score_base"] == 75
    sols = {x["solution"] for x in all_valid_solutions(p, 7, True, 500, lexicon_profile="standard")}
    assert "ardent" in sols


def test_green_room_has_no_standard_playable_solution_in_bundled_lexicon():
    p = Puzzle("green", "room", "green room")
    sols = all_valid_solutions(p, 7, True, 500, lexicon_profile="standard")
    assert sols == []
