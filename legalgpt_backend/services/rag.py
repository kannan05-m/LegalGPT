from legalgpt_backend.services.groq_client import GroqUnavailable, generate_text
from legalgpt_backend.services.vector_store import search
from legalgpt_backend.storage.store import DocumentRecord


def answer_question(record: DocumentRecord, question: str) -> tuple[str, list[str], list[str]]:
    retrieved = search(question, record.chunks, record.vectors, limit=4)
    chunks = [chunk for chunk, score in retrieved if score > 0]
    if not chunks:
        chunks = record.chunks[:3]

    context = "\n\n".join(f"[Chunk {index + 1}]\n{chunk}" for index, chunk in enumerate(chunks))
    prompt = f"""
Answer the user's question using only this document context.
Cite chunks or clauses by name when possible.
If the context does not answer the question, say the document does not specify it.

Context:
{context}

Question: {question}
"""
    try:
        answer = generate_text(prompt)
    except GroqUnavailable:
        answer = _fallback_answer(question, chunks)
    citations = [f"Chunk {index + 1}" for index in range(len(chunks))]
    return answer, citations, chunks


def _fallback_answer(question: str, chunks: list[str]) -> str:
    preview = " ".join(chunks)[:900]
    return (
        "I found the most relevant document language below, but GROQ_API_KEY is not configured, "
        "so this is retrieval-only rather than a full AI answer.\n\n"
        f"Question: {question}\n\nRelevant text: {preview}"
    )
