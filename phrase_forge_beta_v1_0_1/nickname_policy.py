from __future__ import annotations

import re

NICKNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{1,22}[A-Za-z0-9]$")

# Conservative beta block list. Keep deliberately small to reduce false positives.
# Matching is normalized and token-aware where practical.
_BLOCKED_EXACT = {
    "admin", "administrator", "moderator", "phraseforge", "phrase forge", "system",
    "fuck", "fucker", "fucking", "shit", "bitch", "cunt", "asshole",
    "nigger", "nigga", "faggot", "retard",
}
_BLOCKED_PARTS = {
    "nigger", "nigga", "faggot", "cunt", "fuck", "porn", "nazi",
}


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower()).strip()


def validate_nickname(value: str) -> dict:
    raw = (value or "").strip()
    normalized = _normalized(raw)
    if not raw:
        return {"ok": False, "reason": "Enter a nickname."}
    if len(raw) < 3 or len(raw) > 24:
        return {"ok": False, "reason": "Nickname must be 3–24 characters."}
    if not NICKNAME_RE.fullmatch(raw):
        return {"ok": False, "reason": "Use letters, numbers, spaces, dot, dash, or underscore only."}
    if normalized in _BLOCKED_EXACT:
        return {"ok": False, "reason": "Please choose a different nickname."}
    compact = normalized.replace(" ", "")
    if any(part in compact for part in _BLOCKED_PARTS):
        return {"ok": False, "reason": "Please choose a different nickname."}
    return {"ok": True, "nickname": raw}
