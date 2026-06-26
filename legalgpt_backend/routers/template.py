from fastapi import APIRouter

from legalgpt_backend.models.schemas import TemplateRequest, TemplateResponse
from legalgpt_backend.services.templates import generate_template

router = APIRouter()


@router.post("/template", response_model=TemplateResponse)
def template(request: TemplateRequest):
    return TemplateResponse(title=request.document_type, content=generate_template(request))
