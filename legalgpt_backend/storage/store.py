from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from legalgpt_backend.models.schemas import AnalysisResult


@dataclass
class DocumentRecord:
    document_id: str
    filename: str
    text: str
    chunks: List[str]
    vectors: List[Dict[str, float]]
    analysis: AnalysisResult
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    chat_history: List[Dict[str, str]] = field(default_factory=list)


DOCUMENTS: Dict[str, DocumentRecord] = {}
