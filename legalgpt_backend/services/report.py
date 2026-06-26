import io

from legalgpt_backend.storage.store import DocumentRecord


def build_text_report(record: DocumentRecord) -> bytes:
    lines = [
        "LegalGPT Analysis Report",
        f"Document: {record.filename}",
        f"Document type: {record.analysis.document_type}",
        "",
        "Summary",
        record.analysis.summary,
        "",
        "Risk Flags",
    ]
    for risk in record.analysis.risks:
        lines.extend([f"- {risk.level}: {risk.title}", f"  {risk.reason}", f"  Watch out: {risk.watch_out}"])
    lines.extend(["", "Q&A Transcript"])
    for item in record.chat_history:
        lines.append(f"{item.get('role', 'message').title()}: {item.get('content', '')}")
    lines.extend(["", "Disclaimer: LegalGPT is not a lawyer and does not provide legal advice."])
    return "\n".join(lines).encode("utf-8")


def build_pdf_report(record: DocumentRecord) -> bytes:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        return build_text_report(record)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 54
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(54, y, "LegalGPT Analysis Report")
    y -= 28
    pdf.setFont("Helvetica", 10)

    for line in build_text_report(record).decode("utf-8").splitlines():
        if y < 54:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 54
        pdf.drawString(54, y, line[:105])
        y -= 14

    pdf.save()
    return buffer.getvalue()
