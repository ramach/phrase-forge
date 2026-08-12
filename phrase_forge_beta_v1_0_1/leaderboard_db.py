from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(os.getenv("PHRASE_FORGE_DB", Path(__file__).with_name("leaderboard.sqlite3")))


def _database_url() -> str:
    return (os.getenv("DATABASE_URL") or os.getenv("PHRASE_FORGE_DATABASE_URL") or "").strip()


def db_backend_name() -> str:
    return "postgresql" if _database_url().startswith(("postgres://", "postgresql://")) else "sqlite"


@contextmanager
def _conn():
    if db_backend_name() == "postgresql":
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("PostgreSQL is configured but psycopg is not installed.") from exc
        connection = psycopg.connect(_database_url(), row_factory=dict_row)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
    else:
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()


def _execute(connection, sqlite_sql: str, pg_sql: Optional[str] = None, params=()):
    sql = pg_sql if db_backend_name() == "postgresql" and pg_sql else sqlite_sql
    return connection.execute(sql, params)


def init_db() -> None:
    with _conn() as connection:
        if db_backend_name() == "sqlite":
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
            connection.execute("""
                CREATE TABLE IF NOT EXISTS usage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    puzzle_id TEXT,
                    words TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
        else:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id BIGSERIAL PRIMARY KEY,
                    puzzle_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    puzzle_date TEXT,
                    words TEXT NOT NULL,
                    difficulty TEXT,
                    player TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    solution TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(puzzle_id, mode, player)
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS beta_feedback (
                    id BIGSERIAL PRIMARY KEY,
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
            connection.execute("""
                CREATE TABLE IF NOT EXISTS usage_events (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    puzzle_id TEXT,
                    words TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_scores_puzzle ON scores(puzzle_id, mode)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_scores_date ON scores(puzzle_date)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_feedback_created ON beta_feedback(created_at)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON usage_events(created_at)")


def submit_score(day: Optional[str], puzzle_id: str, words: str, difficulty: Optional[str],
                 player: str, score: int, solution: str, mode: str = "Daily") -> dict:
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
        existing = _execute(
            connection,
            "SELECT score, solution FROM scores WHERE puzzle_id=? AND mode=? AND player=? COLLATE NOCASE",
            "SELECT score, solution FROM scores WHERE puzzle_id=%s AND mode=%s AND lower(player)=lower(%s)",
            (puzzle_id, mode, player),
        ).fetchone()
        if existing is None:
            _execute(
                connection,
                """INSERT INTO scores (puzzle_id, mode, puzzle_date, words, difficulty, player, score, solution, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                """INSERT INTO scores (puzzle_id, mode, puzzle_date, words, difficulty, player, score, solution, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (puzzle_id, mode, day, words, difficulty, player, int(score), solution, now, now),
            )
            return {"status": "inserted", "score": int(score)}
        existing_score = int(existing["score"])
        if int(score) <= existing_score:
            return {"status": "kept_existing", "score": existing_score, "solution": existing["solution"]}
        _execute(
            connection,
            """UPDATE scores SET puzzle_date=?, words=?, difficulty=?, score=?, solution=?, updated_at=?
               WHERE puzzle_id=? AND mode=? AND player=? COLLATE NOCASE""",
            """UPDATE scores SET puzzle_date=%s, words=%s, difficulty=%s, score=%s, solution=%s, updated_at=%s
               WHERE puzzle_id=%s AND mode=%s AND lower(player)=lower(%s)""",
            (day, words, difficulty, int(score), solution, now, puzzle_id, mode, player),
        )
        return {"status": "updated_best", "score": int(score)}


def top_scores(day: Optional[str] = None, puzzle_id: Optional[str] = None,
               mode: Optional[str] = None, limit: int = 20) -> list[dict]:
    clauses, params = [], []
    token = "%s" if db_backend_name() == "postgresql" else "?"
    if day:
        clauses.append(f"puzzle_date={token}"); params.append(day)
    if puzzle_id:
        clauses.append(f"puzzle_id={token}"); params.append(puzzle_id)
    if mode:
        clauses.append(f"mode={token}"); params.append(mode.title())
    query = "SELECT puzzle_id, mode, puzzle_date, words, difficulty, player, score, solution, created_at, updated_at FROM scores"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += f" ORDER BY score DESC, updated_at ASC LIMIT {token}"
    params.append(max(1, int(limit)))
    with _conn() as connection:
        return [dict(row) for row in connection.execute(query, params).fetchall()]


def submit_feedback(session_id: str, app_version: str, puzzle_id: str, mode: str, words: str,
                    category: str, comment: str, diagnostic: dict,
                    clarity_rating: Optional[int] = None, enjoyment_rating: Optional[int] = None,
                    would_play_again: Optional[str] = None) -> dict:
    comment = (comment or "").strip()
    if not comment:
        raise ValueError("Please enter a short feedback comment.")
    now = datetime.now(timezone.utc).isoformat()
    params = (session_id, app_version, puzzle_id, mode, words, clarity_rating, enjoyment_rating,
              would_play_again, category, comment, json.dumps(diagnostic, ensure_ascii=False, default=str), now)
    with _conn() as connection:
        cursor = _execute(
            connection,
            """INSERT INTO beta_feedback (session_id, app_version, puzzle_id, mode, words, clarity_rating,
               enjoyment_rating, would_play_again, category, comment, diagnostic_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            """INSERT INTO beta_feedback (session_id, app_version, puzzle_id, mode, words, clarity_rating,
               enjoyment_rating, would_play_again, category, comment, diagnostic_json, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            params,
        )
        if db_backend_name() == "postgresql":
            feedback_id = int(cursor.fetchone()["id"])
        else:
            feedback_id = int(cursor.lastrowid)
        return {"status": "saved", "feedback_id": feedback_id, "created_at": now}


def list_feedback(limit: int = 200) -> list[dict]:
    token = "%s" if db_backend_name() == "postgresql" else "?"
    with _conn() as connection:
        rows = connection.execute(
            f"""SELECT id, session_id, app_version, puzzle_id, mode, words, clarity_rating,
                 enjoyment_rating, would_play_again, category, comment, diagnostic_json, created_at
                 FROM beta_feedback ORDER BY created_at DESC LIMIT {token}""",
            (max(1, int(limit)),),
        ).fetchall()
    return [dict(row) for row in rows]


def record_event(session_id: str, event_type: str, puzzle_id: Optional[str] = None,
                 words: Optional[str] = None, payload: Optional[dict] = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    params = (session_id, event_type, puzzle_id, words, json.dumps(payload or {}, default=str), now)
    with _conn() as connection:
        _execute(
            connection,
            "INSERT INTO usage_events (session_id, event_type, puzzle_id, words, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            "INSERT INTO usage_events (session_id, event_type, puzzle_id, words, payload_json, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            params,
        )


def usage_summary() -> dict:
    with _conn() as connection:
        total_scores = connection.execute("SELECT COUNT(*) AS n FROM scores").fetchone()["n"]
        total_feedback = connection.execute("SELECT COUNT(*) AS n FROM beta_feedback").fetchone()["n"]
        total_events = connection.execute("SELECT COUNT(*) AS n FROM usage_events").fetchone()["n"]
    return {"scores": int(total_scores), "feedback": int(total_feedback), "events": int(total_events), "backend": db_backend_name()}
