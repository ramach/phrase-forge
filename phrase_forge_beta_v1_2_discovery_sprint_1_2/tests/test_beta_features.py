from game_backend import pick_puzzle
from leaderboard_db import init_db, submit_feedback, list_feedback


def test_new_random_puzzle_can_exclude_current():
    first = pick_puzzle(5, 4, True)
    second = pick_puzzle(5, 4, True, exclude_words=(first.word1, first.word2))
    assert (second.word1, second.word2) != (first.word1, first.word2)


def test_beta_feedback_round_trip(tmp_path, monkeypatch):
    import leaderboard_db

    monkeypatch.setattr(leaderboard_db, "DB_PATH", tmp_path / "beta.sqlite3")
    init_db()
    saved = submit_feedback(
        session_id="session-test",
        app_version="0.9.0-beta",
        puzzle_id="puzzle-test",
        mode="Practice",
        words="rain delay",
        category="Goal or onboarding",
        comment="The instructions were clear.",
        diagnostic={"ok": True},
        clarity_rating=5,
        enjoyment_rating=4,
        would_play_again="Yes",
    )
    assert saved["status"] == "saved"
    rows = list_feedback()
    assert rows[0]["comment"] == "The instructions were clear."
