from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class RiskFlag(BaseModel):
    level: str
    title: str
    clause_text: str
    reason: str
    watch_out: str


class AnalysisResult(BaseModel):
    document_type: str = "Unknown legal document"
    parties: List[Dict[str, str]] = Field(default_factory=list)
    effective_date: str = "Not specified"
    expiry_date: str = "Not specified"
    governing_law: str = "Not specified"
    key_clauses: Dict[str, str] = Field(default_factory=dict)
    obligations: List[str] = Field(default_factory=list)
    deadlines: List[str] = Field(default_factory=list)
    risks: List[RiskFlag] = Field(default_factory=list)
    summary: str = ""


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    text_preview: str
    chunk_count: int
    analysis: AnalysisResult


class ChatRequest(BaseModel):
    document_id: str
    question: str
    history: List[Dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    citations: List[str] = Field(default_factory=list)
    retrieved_chunks: List[str] = Field(default_factory=list)


class CompareResponse(BaseModel):
    added: List[str]
    removed: List[str]
    modified_summary: str


class TemplateRequest(BaseModel):
    document_type: str
    party_a: str
    party_b: str
    jurisdiction: str
    duration: Optional[str] = ""
    terms: Optional[str] = ""


class TemplateResponse(BaseModel):
    title: str
    content: str


class DocumentView(BaseModel):
    document_id: str
    filename: str
    text: str
    chunks: List[str]
    analysis: AnalysisResult
    chat_history: List[Dict[str, str]]
