from fastapi import APIRouter, HTTPException, Response

from legalgpt_backend.services.report import build_text_report
from legalgpt_backend.storage.store import DOCUMENTS

router = APIRouter()


@router.get("/export/{document_id}")
def export_report(document_id: str):
    record = DOCUMENTS.get(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    content = build_text_report(record)
    return Response(
        content,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{record.filename}-legalgpt-report.txt"'},
    )
