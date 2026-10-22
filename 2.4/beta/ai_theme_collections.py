"""Session-level AI theme collections; candidate acceptance remains local."""
import re
from ai_puzzle_generator import generate_validated_ai_puzzle

DIFFICULTIES = {"Gentle": (4, 4), "Balanced": (5, 4), "Challenge": (6, 5)}

def normalize_theme(theme):
    theme = " ".join(theme.strip().split())
    if not (2 <= len(theme) <= 80) or not re.fullmatch(r"[\w ,&'()\-]+", theme, re.UNICODE):
        raise ValueError("Enter a theme of 2–80 characters using ordinary words and punctuation.")
    return theme

def create_collection(theme, count=3, difficulty="Balanced", generator=None):
    theme = normalize_theme(theme)
    if difficulty not in DIFFICULTIES or count not in (3, 5, 10):
        raise ValueError("Invalid collection settings.")
    generator = generator or generate_validated_ai_puzzle
    len_a, len_b = DIFFICULTIES[difficulty]
    items, seen = [], set()
    # Bounded retries: do not label a partial collection as complete.
    for _ in range(count * 4):
        if len(items) == count:
            break
        try:
            result = generator(len_a=len_a, len_b=len_b, min_letters=7, theme=theme, attempts=3)
        except Exception:
            continue
        puzzle = result["puzzle"]
        key = (puzzle.word1.lower(), puzzle.word2.lower())
        if key in seen or not result.get("validated_candidates"):
            continue
        seen.add(key)
        items.append({"word1": puzzle.word1, "word2": puzzle.word2,
                      "phrase": puzzle.phrase_label, "theme": theme,
                      "metadata": result.get("metadata", {}),
                      "validated_count": len(result["validated_candidates"])})
    return items
