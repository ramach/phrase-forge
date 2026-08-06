from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json

DB_PATH = Path(os.getenv("PHRASE_FORGE_DB", Path(__file__).with_name("leaderboard.sqlite3")))


def _conn() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _conn() as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(scores)").fetchall()}
        required = {"puzzle_id", "mode", "puzzle_date", "difficulty"}
        if columns and not required.issubset(columns):
            connection.execute("ALTER TABLE scores RENAME TO scores_legacy")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                puzzle_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                puzzle_date TEXT,
                words TEXT NOT NULL,
                difficulty TEXT,
                player TEXT NOT NULL COLLATE NOCASE,
                score INTEGER NOT NULL,
                solution TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(puzzle_id, mode, player)
            )
        """)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_scores_puzzle ON scores(puzzle_id, mode)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_scores_date ON scores(puzzle_date)")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS beta_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                app_version TEXT NOT NULL,
                puzzle_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                words TEXT NOT NULL,
                clarity_rating INTEGER,
                enjoyment_rating INTEGER,
                would_play_again TEXT,
                category TEXT NOT NULL,
                comment TEXT NOT NULL,
                diagnostic_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_feedback_created ON beta_feedback(created_at)")


def submit_score(
    day: Optional[str],
    puzzle_id: str,
    words: str,
    difficulty: Optional[str],
    player: str,
    score: int,
    solution: str,
    mode: str = "Daily",
) -> dict:
    player = (player or "").strip()
    if not player:
        raise ValueError("Enter a player name before submitting.")
    if not puzzle_id:
        raise ValueError("Puzzle ID is required.")
    mode = mode.title()
    if mode not in {"Daily", "Practice"}:
        raise ValueError("Mode must be Daily or Practice.")

    now = datetime.now(timezone.utc).isoformat()
    with _conn() as connection:
        existing = connection.execute(
            "SELECT score, solution FROM scores WHERE puzzle_id=? AND mode=? AND player=?",
            (puzzle_id, mode, player),
        ).fetchone()
        if existing is None:
            connection.execute(
                """INSERT INTO scores
                   (puzzle_id, mode, puzzle_date, words, difficulty, player, score, solution, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (puzzle_id, mode, day, words, difficulty, player, int(score), solution, now, now),
            )
            return {"status": "inserted", "score": int(score)}
        if int(score) <= int(existing["score"]):
            return {"status": "kept_existing", "score": int(existing["score"]), "solution": existing["solution"]}
        connection.execute(
            """UPDATE scores SET puzzle_date=?, words=?, difficulty=?, score=?, solution=?, updated_at=?
               WHERE puzzle_id=? AND mode=? AND player=?""",
            (day, words, difficulty, int(score), solution, now, puzzle_id, mode, player),
        )
        return {"status": "updated_best", "score": int(score)}


def top_scores(
    day: Optional[str] = None,
    puzzle_id: Optional[str] = None,
    mode: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    clauses = []
    params = []
    if day:
        clauses.append("puzzle_date=?")
        params.append(day)
    if puzzle_id:
        clauses.append("puzzle_id=?")
        params.append(puzzle_id)
    if mode:
        clauses.append("mode=?")
        params.append(mode.title())
    query = "SELECT puzzle_id, mode, puzzle_date, words, difficulty, player, score, solution, created_at, updated_at FROM scores"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY score DESC, updated_at ASC LIMIT ?"
    params.append(max(1, int(limit)))
    with _conn() as connection:
        return [dict(row) for row in connection.execute(query, params).fetchall()]


def submit_feedback(
    session_id: str,
    app_version: str,
    puzzle_id: str,
    mode: str,
    words: str,
    category: str,
    comment: str,
    diagnostic: dict,
    clarity_rating: Optional[int] = None,
    enjoyment_rating: Optional[int] = None,
    would_play_again: Optional[str] = None,
) -> dict:
    comment = (comment or "").strip()
    if not comment:
        raise ValueError("Please enter a short feedback comment.")
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as connection:
        cursor = connection.execute(
            """INSERT INTO beta_feedback
               (session_id, app_version, puzzle_id, mode, words, clarity_rating,
                enjoyment_rating, would_play_again, category, comment, diagnostic_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, app_version, puzzle_id, mode, words, clarity_rating,
             enjoyment_rating, would_play_again, category, comment,
             json.dumps(diagnostic, ensure_ascii=False, default=str), now),
        )
        return {"status": "saved", "feedback_id": int(cursor.lastrowid), "created_at": now}


def list_feedback(limit: int = 200) -> list[dict]:
    with _conn() as connection:
        rows = connection.execute(
            """SELECT id, session_id, app_version, puzzle_id, mode, words,
                      clarity_rating, enjoyment_rating, would_play_again, category,
                      comment, diagnostic_json, created_at
               FROM beta_feedback ORDER BY created_at DESC LIMIT ?""",
            (max(1, int(limit)),),
        ).fetchall()
    return [dict(row) for row in rows]
