import math
import re
from collections import Counter
from typing import Dict, Iterable, List, Tuple


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]+")


def tokenize(text: str) -> List[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def embed_text(text: str) -> Dict[str, float]:
    counts = Counter(tokenize(text))
    total = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {term: value / total for term, value in counts.items()}


def embed_many(chunks: Iterable[str]) -> List[Dict[str, float]]:
    return [embed_text(chunk) for chunk in chunks]


def similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(value * b.get(term, 0.0) for term, value in a.items())


def search(query: str, chunks: List[str], vectors: List[Dict[str, float]], limit: int = 4) -> List[Tuple[str, float]]:
    query_vector = embed_text(query)
    scored = [(chunk, similarity(query_vector, vector)) for chunk, vector in zip(chunks, vectors)]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]
