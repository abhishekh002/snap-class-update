import os
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import streamlit as st
from docx import Document
from docx.opc.exceptions import PackageNotFoundError as DocxPackageNotFoundError
from pptx import Presentation
from pptx.exc import PackageNotFoundError as PptxPackageNotFoundError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from src.ai.digitizer import explain_note_concept
from src.ai.agent import ask_snapclass_ai
from src.components.assessment_flow import render_assessment_tab


MAX_PREVIEW_CHARS = 8000


def _limit_preview(text: str) -> str:
    if len(text) > MAX_PREVIEW_CHARS:
        return text[:MAX_PREVIEW_CHARS].rstrip() + "\n\n*Preview truncated.*"
    return text


def _extract_document_text(file_path: str, suffix: str) -> str:
    if suffix in {".txt", ".md", ".markdown"}:
        with open(file_path, "r", encoding="utf-8-sig", errors="replace") as file:
            return _limit_preview(file.read(MAX_PREVIEW_CHARS + 1))

    if suffix == ".pdf":
        pages = []
        char_count = 0
        for page_number, page in enumerate(PdfReader(file_path).pages, start=1):
            page_text = page.extract_text() or ""
            if not page_text.strip():
                continue
            page_text = f"### Page {page_number}\n\n{page_text.strip()}"
            pages.append(page_text)
            char_count += len(page_text)
            if char_count > MAX_PREVIEW_CHARS:
                break
        return _limit_preview("\n\n".join(pages))

    if suffix == ".docx":
        document = Document(file_path)
        parts = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        for table in document.tables:
            parts.extend(
                " | ".join(cell.text.strip() for cell in row.cells)
                for row in table.rows
            )
        return _limit_preview("\n\n".join(parts))

    if suffix == ".pptx":
        presentation = Presentation(file_path)
        slides = []
        char_count = 0
        for slide_number, slide in enumerate(presentation.slides, start=1):
            parts = []
            for shape in slide.shapes:
                if shape.has_text_frame and shape.text.strip():
                    parts.append(shape.text.strip())
                if shape.has_table:
                    parts.extend(
                        " | ".join(cell.text.strip() for cell in row.cells)
                        for row in shape.table.rows
                    )
            if parts:
                slide_text = f"### Slide {slide_number}\n\n" + "\n\n".join(parts)
                slides.append(slide_text)
                char_count += len(slide_text)
                if char_count > MAX_PREVIEW_CHARS:
                    break
        return _limit_preview("\n\n".join(slides))

    if suffix == ".zip":
        with ZipFile(file_path) as archive:
            names = archive.namelist()
        if not names:
            return "The ZIP archive is empty."
        return _limit_preview(
            "Files in this archive:\n\n" + "\n".join(f"- {name}" for name in names[:200])
        )

    return ""


@st.dialog("📖 Interactive Living Note Reader", width="large")
def interactive_reader_dialog(note: dict):
    st.subheader(f"📖 {note.get('title', 'Study Note')}")
    st.caption(f"Subject: **{note.get('subject_name')}** | Teacher: **{note.get('teacher_name')}** | Uploaded: {note.get('created_at')}")

    note_content = note.get("description", "")
    preview_content = note_content
    file_path = note.get("file_path")
    preview_image = False
    preview_notice = None
    if file_path:
        if not os.path.exists(file_path):
            preview_notice = "The original file is not available on this server."
        else:
            suffix = Path(note.get("file_name") or file_path).suffix.lower()
            if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
                preview_image = True
            elif suffix in {".txt", ".md", ".markdown", ".pdf", ".docx", ".pptx", ".zip"}:
                try:
                    extracted_content = _extract_document_text(file_path, suffix)
                except (
                    BadZipFile,
                    DocxPackageNotFoundError,
                    OSError,
                    PdfReadError,
                    PptxPackageNotFoundError,
                    ValueError,
                ) as error:
                    preview_notice = f"Could not preview this file: {error}"
                else:
                    if extracted_content.strip():
                        preview_content = extracted_content
                        if suffix != ".zip":
                            note_content = extracted_content
                    elif suffix == ".pdf":
                        preview_notice = (
                            "No selectable text was found. This may be a scanned PDF; "
                            "download the original file to view it."
                        )
                    else:
                        preview_notice = "No readable text was found in this file."
            elif suffix == ".ppt":
                preview_notice = (
                    "Legacy PowerPoint files cannot be previewed. Please download "
                    "the original or upload it as a .pptx file."
                )
            else:
                preview_notice = (
                    f"Preview is not supported for {suffix or 'this file type'}. "
                    "You can still download the original file."
                )

    tab_read, tab_assessment, tab_qa = st.tabs(
        ["📖 Read & Explain", "📝 Assessment", "💬 Talk to Note"]
    )

    with tab_read:
        st.markdown("### Document Content")
        with st.container(height=260, border=True):
            if preview_image and file_path:
                st.image(file_path, width="stretch")
                if note_content:
                    st.markdown(note_content)
            else:
                st.markdown(
                    preview_content
                    if preview_content
                    else "*No text preview available for this document.*"
                )
        if preview_notice:
            st.info(preview_notice)

        col_dl, col_eli5 = st.columns([1, 1])
        with col_dl:
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                st.download_button(
                    label="⬇️ Download Original File",
                    data=file_bytes,
                    file_name=note.get("file_name", "note_file"),
                    key=f"reader_dl_{note['id']}",
                    width="stretch",
                )
        with col_eli5:
            if st.button("💡 Explain in Simple Terms (ELI5)", type="primary", key=f"eli5_btn_{note['id']}", width="stretch"):
                with st.spinner("AI Tutor is simplifying the concepts..."):
                    simplified = explain_note_concept(note_content)
                    st.session_state[f"eli5_cache_{note['id']}"] = simplified

        if f"eli5_cache_{note['id']}" in st.session_state:
            st.divider()
            st.markdown("#### 💡 Simplified Explanation")
            st.info(st.session_state[f"eli5_cache_{note['id']}"])

    with tab_assessment:
        render_assessment_tab(note)

    with tab_qa:
        st.markdown("### Ask Any Question About This Note")
        doc_q = st.text_input("Ask AI Tutor about this lecture:", placeholder="e.g. What is the difference between step 2 and step 3?", key=f"doc_q_{note['id']}")
        if st.button("Ask Question", key=f"btn_doc_q_{note['id']}"):
            if doc_q.strip():
                with st.spinner("Analyzing document..."):
                    prompt = f"Regarding the following lecture notes:\n\n{note_content}\n\nStudent asks: {doc_q}\nProvide a clear, direct answer."
                    ans = ask_snapclass_ai(prompt)
                    st.session_state[f"qa_ans_{note['id']}"] = ans

        if f"qa_ans_{note['id']}" in st.session_state:
            st.markdown("#### Answer:")
            st.write(st.session_state[f"qa_ans_{note['id']}"])
