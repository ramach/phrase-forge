from __future__ import annotations

import json
import os
from typing import Any, Dict

from game_backend import (
    build_validated_hint_candidates,
    compute_difficulty,
    make_puzzle,
)


def ai_generation_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)


def generate_validated_ai_puzzle(
    len_a: int = 5,
    len_b: int = 4,
    allow_swap: bool = True,
    min_letters: int = 7,
    require_english: bool = True,
    attempts: int = 5,
) -> Dict[str, Any]:
    """Ask AI for candidates, but trust only Phrase Forge's local validator."""
    if not ai_generation_available():
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    from openai import OpenAI

    client = OpenAI()
    lengths = f"{len_a}+{len_b}"
    if allow_swap:
        lengths += f" or {len_b}+{len_a}"

    for _ in range(attempts):
        response = client.responses.create(
            model=os.getenv("PHRASE_FORGE_OPENAI_MODEL", "gpt-5-mini"),
            input=(
                "Return only one JSON object with keys word1, word2, phrase, category, "
                "meaning, example. Propose a recognized natural English two-word phrase. "
                f"Word lengths must be {lengths}. Use alphabetic lowercase words only. "
                "Prefer phrases likely to yield at least one English anagram-like solution using "
                f"at least {min_letters} letters, with a one-letter discount for vowel-starting answers. "
                "Do not include a proposed solution; the application will validate independently."
            ),
        )
        data = _extract_json(response.output_text)
        puzzle = make_puzzle(data["word1"], data["word2"], data.get("phrase") or f"{data['word1']} {data['word2']}")
        candidates = build_validated_hint_candidates(
            puzzle,
            min_letters_used=min_letters,
            require_english=require_english,
            limit=200,
        )
        if candidates:
            return {
                "puzzle": puzzle,
                "validated_candidates": candidates,
                "difficulty": compute_difficulty(puzzle, min_consonant_len=min_letters),
                "metadata": data,
            }

    raise RuntimeError(f"No locally valid puzzle was found after {attempts} AI attempts.")
