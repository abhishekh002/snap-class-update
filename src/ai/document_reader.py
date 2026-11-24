"""Extract readable text from common study documents uploaded to SnapClass."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path


MAX_DOCUMENT_CHARS = 30_000


def extract_document_text(filename: str, payload: bytes) -> str:
    """Read supported document formats, returning bounded plain text."""
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        text = payload.decode("utf-8-sig", errors="replace")
    elif suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(payload))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix == ".docx":
        from docx import Document

        document = Document(BytesIO(payload))
        parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        for table in document.tables:
            parts.extend(" | ".join(cell.text.strip() for cell in row.cells) for row in table.rows)
        text = "\n".join(parts)
    elif suffix == ".pptx":
        from pptx import Presentation

        presentation = Presentation(BytesIO(payload))
        slides = []
        for number, slide in enumerate(presentation.slides, start=1):
            lines = [shape.text.strip() for shape in slide.shapes if getattr(shape, "has_text_frame", False) and shape.text.strip()]
            if lines:
                slides.append(f"Slide {number}:\n" + "\n".join(lines))
        text = "\n\n".join(slides)
    else:
        raise ValueError(
            "Supported files: PDF, DOCX, PPTX, TXT, Markdown, and CSV. "
            "Legacy .doc/.ppt files and other formats must be saved as DOCX/PPTX first."
        )

    text = text.strip()
    if not text:
        raise ValueError("No readable text was found. Scanned PDFs or image-only pages need OCR first.")
    if len(text) > MAX_DOCUMENT_CHARS:
        text = text[:MAX_DOCUMENT_CHARS] + "\n\n[Document text shortened to fit the AI context.]"
    return text
