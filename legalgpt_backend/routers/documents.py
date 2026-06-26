from fastapi import APIRouter, HTTPException

from legalgpt_backend.models.schemas import DocumentView
from legalgpt_backend.storage.store import DOCUMENTS

router = APIRouter()


@router.get("/documents/{document_id}", response_model=DocumentView)
def get_document(document_id: str):
    record = DOCUMENTS.get(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentView(
        document_id=record.document_id,
        filename=record.filename,
        text=record.text,
        chunks=record.chunks,
        analysis=record.analysis,
        chat_history=record.chat_history,
    )
