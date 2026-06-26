from difflib import SequenceMatcher
from typing import List

from legalgpt_backend.services.chunker import chunk_legal_text
from legalgpt_backend.services.groq_client import GroqUnavailable, generate_text


def compare_documents(text_a: str, text_b: str) -> tuple[List[str], List[str], str]:
    chunks_a = chunk_legal_text(text_a)
    chunks_b = chunk_legal_text(text_b)
    added = _unique_chunks(chunks_b, chunks_a)
    removed = _unique_chunks(chunks_a, chunks_b)
    prompt = f"""
Summarize the practical legal impact of these contract changes in plain English.

Added clauses:
{added[:8]}

Removed clauses:
{removed[:8]}
"""
    try:
        summary = generate_text(prompt)
    except GroqUnavailable:
        summary = f"Detected {len(added)} added clause(s) and {len(removed)} removed clause(s). Configure GROQ_API_KEY for a deeper impact summary."
    return added[:12], removed[:12], summary


def _unique_chunks(source: List[str], target: List[str]) -> List[str]:
    unique = []
    for chunk in source:
        best = max((SequenceMatcher(None, chunk, other).ratio() for other in target), default=0)
        if best < 0.62:
            unique.append(chunk)
    return unique
