from fastapi import APIRouter, File, HTTPException, UploadFile

from legalgpt_backend.models.schemas import CompareResponse
from legalgpt_backend.services.compare import compare_documents
from legalgpt_backend.services.document_parser import extract_text

router = APIRouter()


@router.post("/compare", response_model=CompareResponse)
async def compare(file_a: UploadFile = File(...), file_b: UploadFile = File(...)):
    try:
        text_a = extract_text(file_a.filename or "first", await file_a.read())
        text_b = extract_text(file_b.filename or "second", await file_b.read())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    added, removed, modified_summary = compare_documents(text_a, text_b)
    return CompareResponse(added=added, removed=removed, modified_summary=modified_summary)
