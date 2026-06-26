import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from legalgpt_backend.models.schemas import UploadResponse
from legalgpt_backend.services.analysis import analyze_document
from legalgpt_backend.services.chunker import chunk_legal_text
from legalgpt_backend.services.document_parser import extract_text
from legalgpt_backend.services.vector_store import embed_many
from legalgpt_backend.storage.store import DOCUMENTS, DocumentRecord

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    data = await file.read()
    try:
        text = extract_text(file.filename or "document", data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not text.strip():
        raise HTTPException(status_code=400, detail="The uploaded document did not contain readable text.")

    chunks = chunk_legal_text(text)
    vectors = embed_many(chunks)
    analysis = analyze_document(text)
    document_id = str(uuid.uuid4())
    DOCUMENTS[document_id] = DocumentRecord(
        document_id=document_id,
        filename=file.filename or "document",
        text=text,
        chunks=chunks,
        vectors=vectors,
        analysis=analysis,
    )
    return UploadResponse(
        document_id=document_id,
        filename=file.filename or "document",
        text_preview=text[:1000],
        chunk_count=len(chunks),
        analysis=analysis,
    )
