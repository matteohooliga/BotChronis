"""Réponses aux MP fondées uniquement sur une petite base de connaissances locale."""

import json
import re
import unicodedata
from pathlib import Path


FAQ_PATH = Path(__file__).with_name("faq.json")


def _tokens(value: str):
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return set(re.findall(r"[a-z0-9]+", normalized)) - {
        "a", "au", "aux", "de", "des", "du", "en", "et", "est", "je", "la", "le",
        "les", "ma", "mon", "ne", "pas", "pour", "que", "qui", "sur", "un", "une",
        "comment", "faire", "bot", "chronis", "vous", "the", "how", "do", "i", "to",
    }


def answer_question(question: str, language: str = "fr"):
    """Retourne une réponse documentée si la question ressemble assez à une entrée."""
    words = _tokens(question)
    if not words:
        return None
    data = json.loads(FAQ_PATH.read_text(encoding="utf-8"))
    best = None
    best_score = 0.0
    for entry in data:
        for pattern in entry["questions"]:
            pattern_words = _tokens(pattern)
            if not pattern_words:
                continue
            overlap = len(words & pattern_words)
            score = overlap / len(pattern_words)
            if overlap >= 2 and score >= 0.7 and score > best_score:
                best, best_score = entry, score
    return best["answers"].get(language, best["answers"]["fr"]) if best else None
