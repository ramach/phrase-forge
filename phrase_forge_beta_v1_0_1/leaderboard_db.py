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
                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    nickname TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS player_sessions (
                    session_id TEXT PRIMARY KEY,
                    player_id TEXT,
                    nickname TEXT,
                    app_version TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    FOREIGN KEY(player_id) REFERENCES players(player_id)
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS puzzle_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    puzzle_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    words TEXT NOT NULL,
                    difficulty TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    hints_used INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(session_id, puzzle_id, mode)
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    puzzle_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    accepted INTEGER NOT NULL,
                    word_score INTEGER,
                    role_bonus INTEGER,
                    combined_score INTEGER,
                    hints_used INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    nickname TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS player_sessions (
                    session_id TEXT PRIMARY KEY,
                    player_id TEXT,
                    nickname TEXT,
                    app_version TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS puzzle_sessions (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    puzzle_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    words TEXT NOT NULL,
                    difficulty TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    hints_used INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(session_id, puzzle_id, mode)
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS attempts (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    puzzle_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    accepted BOOLEAN NOT NULL,
                    word_score INTEGER,
                    role_bonus INTEGER,
                    combined_score INTEGER,
                    hints_used INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS vocabulary_discoveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    player_id TEXT,
                    nickname TEXT,
                    word TEXT NOT NULL,
                    puzzle_id TEXT NOT NULL,
                    words TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    discovery_points INTEGER NOT NULL DEFAULT 0,
                    first_seen_at TEXT NOT NULL,
                    UNIQUE(session_id, word)
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
                CREATE TABLE IF NOT EXISTS vocabulary_discoveries (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    player_id TEXT,
                    nickname TEXT,
                    word TEXT NOT NULL,
                    puzzle_id TEXT NOT NULL,
                    words TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    discovery_points INTEGER NOT NULL DEFAULT 0,
                    first_seen_at TEXT NOT NULL,
                    UNIQUE(session_id, word)
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
        connection.execute("CREATE INDEX IF NOT EXISTS idx_attempts_puzzle ON attempts(puzzle_id, mode)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_puzzle_sessions_puzzle ON puzzle_sessions(puzzle_id, mode)")


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



def upsert_player(nickname: str) -> dict:
    from nickname_policy import validate_nickname
    import hashlib
    check = validate_nickname(nickname)
    if not check.get("ok"):
        raise ValueError(check.get("reason", "Invalid nickname."))
    nickname = check["nickname"]
    now = datetime.now(timezone.utc).isoformat()
    player_id = hashlib.sha256(nickname.casefold().encode("utf-8")).hexdigest()[:20]
    with _conn() as connection:
        existing = _execute(
            connection,
            "SELECT player_id, nickname FROM players WHERE nickname=? COLLATE NOCASE",
            "SELECT player_id, nickname FROM players WHERE lower(nickname)=lower(%s)",
            (nickname,),
        ).fetchone()
        if existing:
            _execute(connection,
                     "UPDATE players SET last_seen_at=? WHERE player_id=?",
                     "UPDATE players SET last_seen_at=%s WHERE player_id=%s",
                     (now, existing["player_id"]))
            return {"player_id": existing["player_id"], "nickname": existing["nickname"], "status": "existing"}
        _execute(connection,
                 "INSERT INTO players (player_id, nickname, created_at, last_seen_at) VALUES (?, ?, ?, ?)",
                 "INSERT INTO players (player_id, nickname, created_at, last_seen_at) VALUES (%s, %s, %s, %s)",
                 (player_id, nickname, now, now))
        return {"player_id": player_id, "nickname": nickname, "status": "created"}


def register_session(session_id: str, app_version: str, nickname: Optional[str] = None) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    player_id = None
    clean_nickname = None
    if nickname:
        player = upsert_player(nickname)
        player_id = player["player_id"]
        clean_nickname = player["nickname"]
    with _conn() as connection:
        existing = _execute(connection,
                            "SELECT session_id FROM player_sessions WHERE session_id=?",
                            "SELECT session_id FROM player_sessions WHERE session_id=%s",
                            (session_id,)).fetchone()
        if existing:
            _execute(connection,
                     "UPDATE player_sessions SET player_id=?, nickname=?, app_version=?, last_seen_at=? WHERE session_id=?",
                     "UPDATE player_sessions SET player_id=%s, nickname=%s, app_version=%s, last_seen_at=%s WHERE session_id=%s",
                     (player_id, clean_nickname, app_version, now, session_id))
        else:
            _execute(connection,
                     "INSERT INTO player_sessions (session_id, player_id, nickname, app_version, started_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?)",
                     "INSERT INTO player_sessions (session_id, player_id, nickname, app_version, started_at, last_seen_at) VALUES (%s, %s, %s, %s, %s, %s)",
                     (session_id, player_id, clean_nickname, app_version, now, now))
    return {"session_id": session_id, "player_id": player_id, "nickname": clean_nickname}


def start_puzzle_session(session_id: str, puzzle_id: str, mode: str, words: str, difficulty: Optional[str] = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as connection:
        existing = _execute(connection,
                            "SELECT id FROM puzzle_sessions WHERE session_id=? AND puzzle_id=? AND mode=?",
                            "SELECT id FROM puzzle_sessions WHERE session_id=%s AND puzzle_id=%s AND mode=%s",
                            (session_id, puzzle_id, mode)).fetchone()
        if not existing:
            _execute(connection,
                     "INSERT INTO puzzle_sessions (session_id, puzzle_id, mode, words, difficulty, started_at, hints_used) VALUES (?, ?, ?, ?, ?, ?, 0)",
                     "INSERT INTO puzzle_sessions (session_id, puzzle_id, mode, words, difficulty, started_at, hints_used) VALUES (%s, %s, %s, %s, %s, %s, 0)",
                     (session_id, puzzle_id, mode, words, difficulty, now))


def update_puzzle_progress(session_id: str, puzzle_id: str, mode: str, hints_used: int, completed: bool = False) -> None:
    completed_at = datetime.now(timezone.utc).isoformat() if completed else None
    with _conn() as connection:
        if completed:
            _execute(connection,
                     "UPDATE puzzle_sessions SET hints_used=?, completed_at=COALESCE(completed_at, ?) WHERE session_id=? AND puzzle_id=? AND mode=?",
                     "UPDATE puzzle_sessions SET hints_used=%s, completed_at=COALESCE(completed_at, %s) WHERE session_id=%s AND puzzle_id=%s AND mode=%s",
                     (int(hints_used), completed_at, session_id, puzzle_id, mode))
        else:
            _execute(connection,
                     "UPDATE puzzle_sessions SET hints_used=? WHERE session_id=? AND puzzle_id=? AND mode=?",
                     "UPDATE puzzle_sessions SET hints_used=%s WHERE session_id=%s AND puzzle_id=%s AND mode=%s",
                     (int(hints_used), session_id, puzzle_id, mode))


def record_attempt(session_id: str, puzzle_id: str, mode: str, answer: str, accepted: bool,
                   word_score: Optional[int] = None, role_bonus: Optional[int] = None,
                   combined_score: Optional[int] = None, hints_used: int = 0) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as connection:
        _execute(connection,
                 "INSERT INTO attempts (session_id, puzzle_id, mode, answer, accepted, word_score, role_bonus, combined_score, hints_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 "INSERT INTO attempts (session_id, puzzle_id, mode, answer, accepted, word_score, role_bonus, combined_score, hints_used, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                 (session_id, puzzle_id, mode, answer, bool(accepted), word_score, role_bonus, combined_score, int(hints_used), now))


def puzzle_report_cards(limit: int = 100) -> list[dict]:
    token = "%s" if db_backend_name() == "postgresql" else "?"
    with _conn() as connection:
        rows = connection.execute(f"""
            SELECT ps.puzzle_id, ps.mode, MAX(ps.words) AS words,
                   COUNT(*) AS sessions,
                   SUM(CASE WHEN ps.completed_at IS NOT NULL THEN 1 ELSE 0 END) AS completions,
                   AVG(ps.hints_used) AS avg_hints,
                   COUNT(a.id) AS attempts,
                   AVG(CASE WHEN a.accepted THEN a.combined_score END) AS avg_score
            FROM puzzle_sessions ps
            LEFT JOIN attempts a
              ON a.session_id=ps.session_id AND a.puzzle_id=ps.puzzle_id AND a.mode=ps.mode
            GROUP BY ps.puzzle_id, ps.mode
            ORDER BY sessions DESC
            LIMIT {token}
        """, (max(1, int(limit)),)).fetchall()
    out=[]
    for row in rows:
        item=dict(row)
        sessions=int(item.get("sessions") or 0)
        completions=int(item.get("completions") or 0)
        item["completion_rate"] = round((completions / sessions * 100.0), 1) if sessions else 0.0
        item["avg_hints"] = round(float(item.get("avg_hints") or 0), 2)
        item["avg_score"] = round(float(item.get("avg_score") or 0), 2)
        out.append(item)
    return out


def usage_summary() -> dict:
    with _conn() as connection:
        total_scores = connection.execute("SELECT COUNT(*) AS n FROM scores").fetchone()["n"]
        total_feedback = connection.execute("SELECT COUNT(*) AS n FROM beta_feedback").fetchone()["n"]
        total_events = connection.execute("SELECT COUNT(*) AS n FROM usage_events").fetchone()["n"]
        total_players = connection.execute("SELECT COUNT(*) AS n FROM players").fetchone()["n"]
        total_sessions = connection.execute("SELECT COUNT(*) AS n FROM player_sessions").fetchone()["n"]
        total_puzzle_sessions = connection.execute("SELECT COUNT(*) AS n FROM puzzle_sessions").fetchone()["n"]
        total_attempts = connection.execute("SELECT COUNT(*) AS n FROM attempts").fetchone()["n"]
        total_discoveries = connection.execute("SELECT COUNT(*) AS n FROM vocabulary_discoveries").fetchone()["n"]
    return {"scores": int(total_scores), "feedback": int(total_feedback), "events": int(total_events),
            "players": int(total_players), "sessions": int(total_sessions),
            "puzzle_sessions": int(total_puzzle_sessions), "attempts": int(total_attempts), "discoveries": int(total_discoveries),
            "backend": db_backend_name()}



def record_vocabulary_discovery(session_id: str, puzzle_id: str, words: str, word: str,
                                metadata: dict, nickname: Optional[str] = None) -> dict:
    """Persist a unique vocabulary discovery for this browser session.

    Returns {new: bool, discovery_points: int}. Nickname/player_id are stored when
    available so the notebook can span sessions in PostgreSQL or local SQLite.
    """
    now = datetime.now(timezone.utc).isoformat()
    player_id = None
    clean_nickname = None
    if nickname:
        player = upsert_player(nickname)
        player_id = player["player_id"]
        clean_nickname = player["nickname"]
    word = (word or "").strip().lower()
    points = int(metadata.get("discovery_points", 0) or 0)
    payload = json.dumps(metadata or {}, default=str)
    with _conn() as connection:
        if player_id:
            existing = _execute(connection,
                "SELECT id FROM vocabulary_discoveries WHERE player_id=? AND word=?",
                "SELECT id FROM vocabulary_discoveries WHERE player_id=%s AND word=%s",
                (player_id, word)).fetchone()
        else:
            existing = _execute(connection,
                "SELECT id FROM vocabulary_discoveries WHERE session_id=? AND word=?",
                "SELECT id FROM vocabulary_discoveries WHERE session_id=%s AND word=%s",
                (session_id, word)).fetchone()
        if existing:
            return {"new": False, "discovery_points": 0}
        _execute(connection,
            "INSERT INTO vocabulary_discoveries (session_id, player_id, nickname, word, puzzle_id, words, metadata_json, discovery_points, first_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            "INSERT INTO vocabulary_discoveries (session_id, player_id, nickname, word, puzzle_id, words, metadata_json, discovery_points, first_seen_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (session_id, player_id, clean_nickname, word, puzzle_id, words, payload, points, now))
    return {"new": True, "discovery_points": points}


def vocabulary_notebook(session_id: str, nickname: Optional[str] = None, limit: int = 500) -> list[dict]:
    token = "%s" if db_backend_name() == "postgresql" else "?"
    with _conn() as connection:
        if nickname:
            rows = _execute(connection,
                f"SELECT word, puzzle_id, words, metadata_json, discovery_points, first_seen_at FROM vocabulary_discoveries WHERE lower(nickname)=lower(?) ORDER BY first_seen_at DESC LIMIT {token}",
                f"SELECT word, puzzle_id, words, metadata_json, discovery_points, first_seen_at FROM vocabulary_discoveries WHERE lower(nickname)=lower(%s) ORDER BY first_seen_at DESC LIMIT {token}",
                (nickname, max(1, int(limit)))).fetchall()
        else:
            rows = _execute(connection,
                f"SELECT word, puzzle_id, words, metadata_json, discovery_points, first_seen_at FROM vocabulary_discoveries WHERE session_id=? ORDER BY first_seen_at DESC LIMIT {token}",
                f"SELECT word, puzzle_id, words, metadata_json, discovery_points, first_seen_at FROM vocabulary_discoveries WHERE session_id=%s ORDER BY first_seen_at DESC LIMIT {token}",
                (session_id, max(1, int(limit)))).fetchall()
    out=[]
    seen=set()
    for row in rows:
        item=dict(row)
        word_key=str(item.get("word") or "").lower()
        if word_key in seen:
            continue
        seen.add(word_key)
        try:
            item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        except Exception:
            item["metadata"] = {}
        out.append(item)
    return out


def discovery_summary(session_id: str, nickname: Optional[str] = None) -> dict:
    rows = vocabulary_notebook(session_id, nickname, limit=5000)
    return {
        "words_discovered": len({r.get("word") for r in rows}),
        "discovery_score": sum(int(r.get("discovery_points") or 0) for r in rows),
        "rare_discoveries": sum(1 for r in rows if (r.get("metadata") or {}).get("frequency") == "rare"),
    }
