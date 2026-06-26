import cgi
import io
import json
import math
import os
import re
import uuid
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).parent
FRONTEND = ROOT / "legalgpt_frontend"
DOCUMENTS = {}
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]+")


def json_response(handler, data, status=200):
    payload = json.dumps(data).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def text_response(handler, data, filename="legalgpt-report.txt"):
    payload = data.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Content-Disposition", f'attachment; filename="{filename}"')
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    return json.loads(handler.rfile.read(length).decode("utf-8") or "{}")


def read_upload(handler):
    form = cgi.FieldStorage(
        fp=handler.rfile,
        headers=handler.headers,
        environ={
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": handler.headers.get("Content-Type"),
            "CONTENT_LENGTH": handler.headers.get("Content-Length", "0"),
        },
    )
    file_item = form["file"]
    filename = Path(file_item.filename or "document.txt").name
    data = file_item.file.read()
    return filename, extract_text(filename, data)


def read_compare_upload(handler):
    form = cgi.FieldStorage(
        fp=handler.rfile,
        headers=handler.headers,
        environ={
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": handler.headers.get("Content-Type"),
            "CONTENT_LENGTH": handler.headers.get("Content-Length", "0"),
        },
    )
    a = form["file_a"]
    b = form["file_b"]
    return (
        extract_text(Path(a.filename or "first.txt").name, a.file.read()),
        extract_text(Path(b.filename or "second.txt").name, b.file.read()),
    )


def extract_text(filename, data):
    suffix = Path(filename).suffix.lower()
    if suffix in {"", ".txt", ".md"}:
        return data.decode("utf-8", errors="ignore").strip()
    raise ValueError("This zero-dependency runner supports TXT/MD uploads. Install optional PDF/DOCX libraries for binary document parsing.")


def tokenize(text):
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def embed(text):
    counts = Counter(tokenize(text))
    norm = math.sqrt(sum(value * value for value in counts.values())) or 1
    return {term: value / norm for term, value in counts.items()}


def similarity(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(value * b.get(term, 0) for term, value in a.items())


def chunk_text(text, max_chars=1600):
    clause_start = re.compile(r"^\s*((section|clause|article)\s+\d+|[0-9]+(\.[0-9]+)*[.)]|[A-Z][A-Z\s]{4,}:)", re.I)
    chunks, current = [], []
    for line in [line.strip() for line in text.splitlines() if line.strip()]:
        current_len = sum(len(part) for part in current)
        if current and (clause_start.match(line) or current_len + len(line) > max_chars):
            chunks.append(" ".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append(" ".join(current))
    return chunks or [text]


def groq_text(prompt, temperature=0.1):
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    payload = {
        "model": os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
        "messages": [
            {
                "role": "system",
                "content": "You are LegalGPT. Explain legal documents in plain English. You are not a lawyer. Use only the provided context.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"].get("content", "")


def analyze(text):
    fallback = heuristic_analysis(text)
    if not os.getenv("GROQ_API_KEY"):
        return fallback
    prompt = f"""Return JSON only with keys document_type, parties, effective_date, expiry_date,
governing_law, key_clauses, obligations, deadlines, risks, summary.
Each risk must include level, title, clause_text, reason, watch_out.

Document:
{text[:14000]}"""
    try:
        raw = groq_text(prompt)
        start, end = raw.find("{"), raw.rfind("}")
        return json.loads(raw[start : end + 1])
    except Exception:
        return fallback


def heuristic_analysis(text):
    lower = text.lower()
    doc_type = "Legal Document"
    if "non-disclosure" in lower or "confidentiality agreement" in lower:
        doc_type = "NDA"
    elif "employment" in lower:
        doc_type = "Employment Agreement"
    elif "lease" in lower or "tenant" in lower:
        doc_type = "Rental / Lease Agreement"

    key_terms = {
        "confidentiality": ["confidential", "non-disclosure", "disclose"],
        "termination": ["terminate", "termination", "cancel"],
        "liability": ["liability", "liable", "damages"],
        "indemnification": ["indemnify", "indemnification", "hold harmless"],
        "non_compete": ["non-compete", "noncompete", "compete"],
        "ip_ownership": ["intellectual property", "work product", "assignment"],
        "payment_terms": ["payment", "fee", "invoice", "compensation"],
    }
    sentences = re.split(r"(?<=[.!?])\s+", text)
    clauses = {}
    for name, terms in key_terms.items():
        found = next((s.strip() for s in sentences if any(term in s.lower() for term in terms)), "")
        if found:
            clauses[name] = found[:650]

    risks = []
    risk_patterns = [
        ("High Risk", "Unlimited liability", ["unlimited liability", "without limitation", "all damages"]),
        ("High Risk", "Broad indemnification", ["indemnify", "hold harmless"]),
        ("High Risk", "Automatic renewal", ["automatically renew", "auto-renew", "renewal term"]),
        ("Medium Risk", "Vague termination", ["sole discretion", "for any reason"]),
        ("Medium Risk", "Non-compete restriction", ["non-compete", "noncompete", "not compete"]),
        ("Medium Risk", "Broad IP assignment", ["assigns all", "work product", "intellectual property"]),
    ]
    for level, title, terms in risk_patterns:
        clause = next((s.strip() for s in sentences if any(term in s.lower() for term in terms)), "")
        if clause:
            risks.append(
                {
                    "level": level,
                    "title": title,
                    "clause_text": clause[:700],
                    "reason": f"The document includes language associated with {title.lower()}.",
                    "watch_out": "Review whether this term is mutual, capped, time-limited, and commercially reasonable.",
                }
            )

    parties = []
    match = re.search(r"between\s+(.{2,80}?)\s+and\s+(.{2,80}?)(?:\.|,|\n)", text, re.I)
    if match:
        parties = [{"name": match.group(1).strip(), "role": "Party A"}, {"name": match.group(2).strip(), "role": "Party B"}]

    governing = re.search(r"governed by the laws of ([^.,\n]+)", text, re.I)
    effective = re.search(
        r"effective\s+(?:as of\s+)?(?:date\s*)?[:\-]?\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})",
        text,
        re.I,
    )
    summary = f"This appears to be a {doc_type.lower()}. LegalGPT found {len(clauses)} key clause area(s) and {len(risks)} potential risk flag(s)."
    if not os.getenv("GROQ_API_KEY"):
        summary += " Add GROQ_API_KEY for live Groq analysis."

    return {
        "document_type": doc_type,
        "parties": parties,
        "effective_date": effective.group(1).strip() if effective else "Not specified",
        "expiry_date": "Not specified",
        "governing_law": governing.group(1).strip() if governing else "Not specified",
        "key_clauses": clauses,
        "obligations": [s.strip()[:450] for s in sentences if any(t in s.lower() for t in ["shall", "must", "agrees to"])][:6],
        "deadlines": [s.strip()[:450] for s in sentences if any(t in s.lower() for t in ["days", "notice", "deadline", "within"])][:6],
        "risks": risks[:8],
        "summary": summary,
    }


def answer(document, question):
    query = embed(question)
    scored = [(chunk, similarity(query, vector)) for chunk, vector in zip(document["chunks"], document["vectors"])]
    scored.sort(key=lambda item: item[1], reverse=True)
    chunks = [chunk for chunk, score in scored[:4] if score > 0] or document["chunks"][:3]
    context = "\n\n".join(f"[Chunk {index + 1}]\n{chunk}" for index, chunk in enumerate(chunks))
    if os.getenv("GROQ_API_KEY"):
        try:
            text = groq_text(f"Answer using only this context:\n{context}\n\nQuestion: {question}")
        except Exception:
            text = fallback_answer(question, chunks)
    else:
        text = fallback_answer(question, chunks)
    return {"answer": text, "citations": [f"Chunk {i + 1}" for i in range(len(chunks))], "retrieved_chunks": chunks}


def fallback_answer(question, chunks):
    return (
        "GROQ_API_KEY is not configured, so this is retrieval-only rather than a full AI answer.\n\n"
        f"Question: {question}\n\nRelevant text: {' '.join(chunks)[:900]}"
    )


def compare_texts(a, b):
    chunks_a, chunks_b = chunk_text(a), chunk_text(b)
    added = [chunk for chunk in chunks_b if max([similarity(embed(chunk), embed(other)) for other in chunks_a] or [0]) < 0.62]
    removed = [chunk for chunk in chunks_a if max([similarity(embed(chunk), embed(other)) for other in chunks_b] or [0]) < 0.62]
    summary = f"Detected {len(added)} added clause(s) and {len(removed)} removed clause(s)."
    if os.getenv("GROQ_API_KEY"):
        try:
            summary = groq_text(f"Summarize these legal changes.\nAdded: {added[:8]}\nRemoved: {removed[:8]}")
        except Exception:
            pass
    return {"added": added[:12], "removed": removed[:12], "modified_summary": summary}


def template(payload):
    prompt = f"Create a legal template for: {json.dumps(payload)}. Include sections and a legal-review disclaimer."
    if os.getenv("GROQ_API_KEY"):
        try:
            content = groq_text(prompt, temperature=0.2)
            return {"title": payload.get("document_type", "Template"), "content": content}
        except Exception:
            pass
    content = f"""# {payload.get('document_type', 'Agreement')}

This agreement is between {payload.get('party_a', 'Party A')} and {payload.get('party_b', 'Party B')}.

1. Purpose
The parties agree to the following terms: {payload.get('terms') or 'Not specified'}.

2. Term
Duration: {payload.get('duration') or 'Not specified'}.

3. Governing Law
This agreement is governed by the laws of {payload.get('jurisdiction', 'the selected jurisdiction')}.

4. Confidentiality
Each party will protect confidential information received from the other party.

5. Termination
Termination terms should be completed and reviewed by counsel.

Disclaimer: This generated template is not legal advice and should be reviewed by a qualified lawyer."""
    return {"title": payload.get("document_type", "Template"), "content": content}


def report(document):
    lines = [
        "LegalGPT Analysis Report",
        f"Document: {document['filename']}",
        f"Document type: {document['analysis'].get('document_type', 'Unknown')}",
        "",
        "Summary",
        document["analysis"].get("summary", ""),
        "",
        "Risk Flags",
    ]
    for risk in document["analysis"].get("risks", []):
        lines.append(f"- {risk.get('level')}: {risk.get('title')} - {risk.get('reason')}")
    lines.extend(["", "Q&A Transcript"])
    for item in document["chat_history"]:
        lines.append(f"{item['role'].title()}: {item['content']}")
    lines.append("\nDisclaimer: LegalGPT is not a lawyer and does not provide legal advice.")
    return "\n".join(lines)


class LegalGPTHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        clean = parsed.path.lstrip("/") or "index.html"
        if clean.startswith("api/"):
            return str(FRONTEND / "index.html")
        return str(FRONTEND / clean)

    def do_POST(self):
        try:
            if self.path == "/api/upload":
                filename, text = read_upload(self)
                if not text:
                    return json_response(self, {"detail": "The uploaded file did not contain readable text."}, 400)
                chunks = chunk_text(text)
                doc_id = str(uuid.uuid4())
                analysis = analyze(text)
                DOCUMENTS[doc_id] = {
                    "document_id": doc_id,
                    "filename": filename,
                    "text": text,
                    "chunks": chunks,
                    "vectors": [embed(chunk) for chunk in chunks],
                    "analysis": analysis,
                    "chat_history": [],
                }
                return json_response(
                    self,
                    {
                        "document_id": doc_id,
                        "filename": filename,
                        "text_preview": text[:1000],
                        "chunk_count": len(chunks),
                        "analysis": analysis,
                    },
                )
            if self.path.startswith("/api/analysis/"):
                doc_id = self.path.rsplit("/", 1)[-1]
                document = DOCUMENTS.get(doc_id)
                if not document:
                    return json_response(self, {"detail": "Document not found."}, 404)
                document["analysis"] = analyze(document["text"])
                return json_response(self, document["analysis"])
            if self.path == "/api/chat":
                payload = read_json(self)
                document = DOCUMENTS.get(payload.get("document_id"))
                if not document:
                    return json_response(self, {"detail": "Document not found."}, 404)
                result = answer(document, payload.get("question", ""))
                document["chat_history"].append({"role": "user", "content": payload.get("question", "")})
                document["chat_history"].append({"role": "assistant", "content": result["answer"]})
                return json_response(self, result)
            if self.path == "/api/compare":
                a, b = read_compare_upload(self)
                return json_response(self, compare_texts(a, b))
            if self.path == "/api/template":
                return json_response(self, template(read_json(self)))
            return json_response(self, {"detail": "Not found."}, 404)
        except ValueError as exc:
            return json_response(self, {"detail": str(exc)}, 400)
        except Exception as exc:
            return json_response(self, {"detail": f"Server error: {exc}"}, 500)

    def do_GET(self):
        if self.path.startswith("/api/documents/"):
            doc_id = self.path.rsplit("/", 1)[-1]
            document = DOCUMENTS.get(doc_id)
            if not document:
                return json_response(self, {"detail": "Document not found."}, 404)
            return json_response(
                self,
                {
                    "document_id": document["document_id"],
                    "filename": document["filename"],
                    "text": document["text"],
                    "chunks": document["chunks"],
                    "analysis": document["analysis"],
                    "chat_history": document["chat_history"],
                },
            )
        if self.path.startswith("/api/export/"):
            doc_id = self.path.rsplit("/", 1)[-1]
            document = DOCUMENTS.get(doc_id)
            if not document:
                return json_response(self, {"detail": "Document not found."}, 404)
            return text_response(self, report(document), f"{document['filename']}-legalgpt-report.txt")
        return super().do_GET()


if __name__ == "__main__":
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), LegalGPTHandler)
    print(f"LegalGPT running at http://{host}:{port}")
    server.serve_forever()
