from fastapi import APIRouter, HTTPException

from legalgpt_backend.models.schemas import ChatRequest, ChatResponse
from legalgpt_backend.services.rag import answer_question
from legalgpt_backend.storage.store import DOCUMENTS

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    record = DOCUMENTS.get(request.document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    answer, citations, chunks = answer_question(record, request.question)
    record.chat_history.append({"role": "user", "content": request.question})
    record.chat_history.append({"role": "assistant", "content": answer})
    return ChatResponse(answer=answer, citations=citations, retrieved_chunks=chunks)
