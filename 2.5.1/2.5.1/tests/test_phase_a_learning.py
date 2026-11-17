from __future__ import annotations

import os
from pathlib import Path

from learning_metadata import word_learning_metadata
import leaderboard_db as db


def test_word_card_metadata_for_curated_word():
    meta = word_learning_metadata("kneeler", "standard")
    assert meta["accepted"] is True
    assert "noun" in meta["part_of_speech"]
    assert meta["frequency"] == "rare"
    assert meta["discovery_points"] == 5
    assert meta["definition"]


def test_word_card_metadata_infers_pos_when_not_curated():
    meta = word_learning_metadata("quickly", "expert")
    assert "adverb" in meta["part_of_speech"]


def test_vocabulary_discovery_is_unique_per_session(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("PHRASE_FORGE_DATABASE_URL", raising=False)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "learning.sqlite3")
    db.init_db()
    meta = {
        "word": "kneeler", "frequency": "rare", "frequency_label": "Rare",
        "part_of_speech": ["noun"], "discovery_points": 5, "definition": "A person who kneels.",
    }
    first = db.record_vocabulary_discovery("s1", "p1", "like never", "kneeler", meta, "Tester")
    second = db.record_vocabulary_discovery("s1", "p1", "like never", "kneeler", meta, "Tester")
    assert first == {"new": True, "discovery_points": 5}
    assert second == {"new": False, "discovery_points": 0}
    summary = db.discovery_summary("s1", "Tester")
    assert summary["words_discovered"] == 1
    assert summary["discovery_score"] == 5
    assert summary["rare_discoveries"] == 1
