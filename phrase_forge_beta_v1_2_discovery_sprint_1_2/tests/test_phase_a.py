import os
from pathlib import Path

from nickname_policy import validate_nickname


def test_nickname_accepts_normal_beta_name():
    result = validate_nickname("WordFan_27")
    assert result["ok"] is True


def test_nickname_rejects_reserved_and_offensive_names():
    assert validate_nickname("admin")["ok"] is False
    assert validate_nickname("nazi-fan")["ok"] is False


def test_phase_a_sqlite_analytics(tmp_path, monkeypatch):
    db_path = tmp_path / "phase_a.sqlite3"
    monkeypatch.setenv("PHRASE_FORGE_DB", str(db_path))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("PHRASE_FORGE_DATABASE_URL", raising=False)

    import importlib
    import leaderboard_db
    db = importlib.reload(leaderboard_db)

    db.init_db()
    player = db.upsert_player("Tester_01")
    assert player["nickname"] == "Tester_01"

    db.register_session("sess-a", "1.1.0", "Tester_01")
    db.start_puzzle_session("sess-a", "p1", "Practice", "rain delay", "Medium")
    db.record_attempt("sess-a", "p1", "Practice", "already", True, 90, 10, 100, 1)
    db.update_puzzle_progress("sess-a", "p1", "Practice", 1, completed=True)

    summary = db.usage_summary()
    assert summary["players"] == 1
    assert summary["sessions"] == 1
    assert summary["puzzle_sessions"] == 1
    assert summary["attempts"] == 1

    reports = db.puzzle_report_cards()
    assert reports[0]["completion_rate"] == 100.0
    assert reports[0]["avg_score"] == 100.0
