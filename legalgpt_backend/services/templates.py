from legalgpt_backend.models.schemas import TemplateRequest
from legalgpt_backend.services.groq_client import GroqUnavailable, generate_text


def generate_template(request: TemplateRequest) -> str:
    prompt = f"""
Create a complete, plain-English legal document template.
Document type: {request.document_type}
Party A: {request.party_a}
Party B: {request.party_b}
Jurisdiction: {request.jurisdiction}
Duration: {request.duration}
Specific terms: {request.terms}

Include structured sections and a final disclaimer that this is not legal advice.
"""
    try:
        return generate_text(prompt, temperature=0.2)
    except GroqUnavailable:
        return f"""# {request.document_type}

This {request.document_type} is between {request.party_a} and {request.party_b}.

1. Purpose
The parties agree to the purpose and scope described here: {request.terms or "Not specified"}.

2. Term
The agreement duration is {request.duration or "not specified"}.

3. Governing Law
This agreement is governed by the laws of {request.jurisdiction}.

4. Confidentiality
Each party will protect confidential information received from the other party.

5. Termination
Either party may terminate according to written notice terms to be completed by the parties.

Disclaimer: This generated template is not legal advice and should be reviewed by a qualified lawyer."""
