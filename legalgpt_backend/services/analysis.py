import re
from typing import Dict, List

from legalgpt_backend.config import settings
from legalgpt_backend.models.schemas import AnalysisResult, RiskFlag
from legalgpt_backend.services.groq_client import generate_json


from legalgpt_backend.config import settings
from legalgpt_backend.models.schemas import AnalysisResult, RiskFlag
from legalgpt_backend.services.groq_client import generate_json

KEYWORDS = {
    "confidentiality": ["confidential", "non-disclosure", "disclose"],
    "termination": ["terminate", "termination", "cancel"],
    "liability": ["liability", "liable", "damages"],
    "indemnification": ["indemnify", "indemnification", "hold harmless"],
    "non_compete": ["non-compete", "noncompete", "compete"],
    "ip_ownership": ["intellectual property", "ip ownership", "work product", "assignment"],
    "payment_terms": ["payment", "fee", "invoice", "compensation"],
}

RISK_PATTERNS = [
    ("High Risk", "Unlimited liability", ["unlimited liability", "without limitation", "all damages"]),
    ("High Risk", "Broad indemnification", ["indemnify", "hold harmless"]),
    ("High Risk", "Automatic renewal", ["automatically renew", "auto-renew", "renewal term"]),
    ("Medium Risk", "Vague termination", ["for any reason", "sole discretion"]),
    ("Medium Risk", "Non-compete restriction", ["non-compete", "noncompete", "not compete"]),
    ("Medium Risk", "Broad IP assignment", ["assigns all", "work product", "intellectual property"]),
]


def analyze_document(text: str) -> AnalysisResult:
    fallback = _heuristic_analysis(text)

    prompt = f"""
Analyze this legal document.

Return ONLY valid JSON.

Required JSON structure:

{{
    "document_type": "string",
    "parties": [
        {{
            "name": "string",
            "role": "string"
        }}
    ],
    "effective_date": "string",
    "expiry_date": "string",
    "governing_law": "string",
    "key_clauses": {{
        "clause_name": "clause_summary"
    }},
    "obligations": ["string"],
    "deadlines": ["string"],
    "risks": [
        {{
            "level": "High Risk",
            "title": "string",
            "clause_text": "string",
            "reason": "string",
            "watch_out": "string"
        }}
    ],
    "summary": "string"
}}

Document:
{text[:settings.max_context_chars]}
"""

    try:
        data = generate_json(prompt, fallback=fallback.model_dump())

        # -----------------------
        # Normalize parties
        # -----------------------
        if isinstance(data.get("parties"), list):
            if data["parties"] and isinstance(data["parties"][0], str):
                data["parties"] = [
                    {
                        "name": party,
                        "role": f"Party {index + 1}",
                    }
                    for index, party in enumerate(data["parties"])
                ]

        # -----------------------
        # Normalize key_clauses
        # -----------------------
        if isinstance(data.get("key_clauses"), list):
            data["key_clauses"] = {
                str(clause): str(clause)
                for clause in data["key_clauses"]
            }

        # -----------------------
        # Normalize deadlines
        # -----------------------
        if isinstance(data.get("deadlines"), list):
            normalized_deadlines = []

            for item in data["deadlines"]:
                if isinstance(item, dict):
                    parts = []

                    if item.get("date"):
                        parts.append(str(item["date"]))

                    if item.get("description"):
                        parts.append(str(item["description"]))

                    if item.get("deadline"):
                        parts.append(str(item["deadline"]))

                    if item.get("clause"):
                        parts.append(f"Clause: {item['clause']}")

                    normalized_deadlines.append(" - ".join(parts))
                else:
                    normalized_deadlines.append(str(item))

            data["deadlines"] = normalized_deadlines

        # -----------------------
        # Normalize risks
        # -----------------------
        if isinstance(data.get("risks"), list):
            normalized_risks = []

            for risk in data["risks"]:
                if isinstance(risk, str):
                    normalized_risks.append(
                        {
                            "level": "Medium Risk",
                            "title": risk,
                            "clause_text": "",
                            "reason": risk,
                            "watch_out": "Review this clause carefully."
                        }
                    )
                else:
                    normalized_risks.append(risk)

            data["risks"] = normalized_risks

        return AnalysisResult.model_validate(data)

    except Exception as exc:
        print(f"AI analysis failed, using fallback: {exc}")
        return fallback


def _heuristic_analysis(text: str) -> AnalysisResult:
    lower = text.lower()

    doc_type = _detect_type(lower)
    clauses = _extract_key_clauses(text)
    risks = _detect_risks(text)
    parties = _detect_parties(text)

    governing_law = _extract_match(
        text,
        r"governed by the laws of ([^.,\n]+)",
        "Not specified",
    )

    effective_date = _extract_match(
        text,
        r"effective\s+(?:as of\s+)?(?:date\s*)?[:\-]?\s*([A-Za-z0-9, ]{6,40})",
        "Not specified",
    )

    expiry_date = _extract_match(
        text,
        r"(?:expires|expiry date|expiration date)\s*[:\-]?\s*([A-Za-z0-9, ]{6,40})",
        "Not specified",
    )

    obligations = _sentences_with(
        lower,
        text,
        ["shall", "must", "agrees to", "responsible for"],
    )[:6]

    deadlines = _sentences_with(
        lower,
        text,
        ["days", "notice", "deadline", "within"],
    )[:6]

    summary = (
        f"This appears to be a {doc_type.lower()}. "
        f"LegalGPT found {len(clauses)} key clause areas "
        f"and {len(risks)} potential risk flag(s)."
    )

    return AnalysisResult(
        document_type=doc_type,
        parties=parties,
        effective_date=effective_date,
        expiry_date=expiry_date,
        governing_law=governing_law,
        key_clauses=clauses,
        obligations=obligations,
        deadlines=deadlines,
        risks=risks,
        summary=summary,
    )


def _detect_type(lower: str) -> str:
    if "non-disclosure" in lower or "confidentiality agreement" in lower:
        return "NDA"

    if "employment" in lower:
        return "Employment Agreement"

    if "lease" in lower or "tenant" in lower or "landlord" in lower:
        return "Rental / Lease Agreement"

    if "service" in lower or "statement of work" in lower:
        return "Service Agreement"

    return "Legal Document"


def _extract_key_clauses(text: str) -> Dict[str, str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)

    clauses: Dict[str, str] = {}

    for name, terms in KEYWORDS.items():
        for sentence in sentences:
            if any(term in sentence.lower() for term in terms):
                clauses[name] = sentence.strip()[:650]
                break

    return clauses


def _detect_risks(text: str) -> List[RiskFlag]:
    lower = text.lower()
    sentences = re.split(r"(?<=[.!?])\s+", text)

    risks: List[RiskFlag] = []

    for level, title, terms in RISK_PATTERNS:
        if any(term in lower for term in terms):
            clause = next(
                (
                    sentence.strip()
                    for sentence in sentences
                    if any(term in sentence.lower() for term in terms)
                ),
                "",
            )

            risks.append(
                RiskFlag(
                    level=level,
                    title=title,
                    clause_text=clause[:700] or "Relevant language detected.",
                    reason=f"The document includes language associated with {title.lower()}.",
                    watch_out="Review whether this term is mutual, capped, time-limited, and commercially reasonable.",
                )
            )

    return risks[:8]


def _detect_parties(text: str) -> List[Dict[str, str]]:
    match = re.search(
        r"between\s+(.{2,80}?)\s+and\s+(.{2,80}?)(?:.|,|\n)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return []

    return [
        {
            "name": match.group(1).strip(),
            "role": "Party A",
        },
        {
            "name": match.group(2).strip(),
            "role": "Party B",
        },
    ]


def _extract_match(text: str, pattern: str, default: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return match.group(1).strip()

    return default


def _sentences_with(lower: str, text: str, terms: List[str]) -> List[str]:
    del lower

    sentences = re.split(r"(?<=[.!?])\s+", text)

    return [
        sentence.strip()[:450]
        for sentence in sentences
        if any(term in sentence.lower() for term in terms)
    ]