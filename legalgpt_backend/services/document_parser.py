from pathlib import Path


def extract_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        return data.decode("utf-8", errors="ignore")
    if suffix == ".pdf":
        return _extract_pdf(data)
    if suffix == ".docx":
        return _extract_docx(data)
    raise ValueError("Unsupported file type. Upload a PDF, DOCX, or TXT file.")


def _extract_pdf(data: bytes) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise ValueError("PDF parsing requires PyMuPDF. Install requirements.txt first.") from exc

    text_parts = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts).strip()


def _extract_docx(data: bytes) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise ValueError("DOCX parsing requires python-docx. Install requirements.txt first.") from exc

    import io

    doc = Document(io.BytesIO(data))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()
