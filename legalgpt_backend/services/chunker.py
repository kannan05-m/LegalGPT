import re
from typing import List


CLAUSE_START = re.compile(
    r"^\s*((section|clause|article)\s+\d+|[0-9]+(\.[0-9]+)*[.)]|[A-Z][A-Z\s]{4,}:)",
    re.IGNORECASE,
)


def chunk_legal_text(text: str, max_chars: int = 1600) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    chunks: List[str] = []
    current: List[str] = []

    for line in lines:
        starts_clause = bool(CLAUSE_START.match(line))
        current_len = sum(len(part) for part in current)
        if current and (starts_clause or current_len + len(line) > max_chars):
            chunks.append(" ".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        chunks.append(" ".join(current).strip())

    return [chunk for chunk in chunks if chunk]
