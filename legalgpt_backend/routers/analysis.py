from fastapi import APIRouter, HTTPException

from legalgpt_backend.models.schemas import AnalysisResult
from legalgpt_backend.services.analysis import analyze_document
from legalgpt_backend.storage.store import DOCUMENTS

router = APIRouter()


@router.post("/analysis/{document_id}", response_model=AnalysisResult)
def rerun_analysis(document_id: str):
    record = DOCUMENTS.get(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    record.analysis = analyze_document(record.text)
    return record.analysis
