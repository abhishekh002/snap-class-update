import os
import io
import json
import asyncio
import streamlit as st
from google import genai
from google.genai import types

def _get_client():
    api_key = None
    try:
        if hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Configure GOOGLE_API_KEY in Streamlit secrets or environment variables.")
    return genai.Client(api_key=api_key)

async def _digitize_async(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    client = _get_client()
    prompt = """You are an expert academic digitizer for classroom blackboards and whiteboards.
Convert this classroom blackboard/whiteboard photo into a clean, comprehensive study guide:
1. Format all mathematical and physical equations in clean LaTeX notation using $...$ for inline or $$...$$ for display equations.
2. Format all code snippets in properly highlighted markdown code blocks (e.g. ```python, ```c, etc.).
3. Organize the content with clear Markdown Headings (#, ##, ###), bullet points, and numbered lists.
4. If there are flowcharts or diagrams, describe them clearly or represent them as text/mermaid diagrams.
5. Add a short "Key Concepts Summary" section at the end.
Be accurate, pedagogical, and clean."""

    res = await client.aio.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt,
        ],
    )
    return res.text or "Could not transcribe blackboard contents."

def digitize_blackboard_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Synchronous wrapper to digitize blackboard image."""
    return asyncio.run(_digitize_async(image_bytes, mime_type))

async def _explain_note_async(note_text: str) -> str:
    client = _get_client()
    prompt = f"""You are a patient, encouraging academic tutor.
Explain the following lecture notes in simple terms (ELI5 style).
Use real-world analogies, highlight why these concepts matter, and break down any complex formulas or steps.

Notes:
{note_text}"""

    res = await client.aio.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=[prompt],
    )
    return res.text or "No explanation generated."

def explain_note_concept(note_text: str) -> str:
    """Explains lecture note concepts simply."""
    return asyncio.run(_explain_note_async(note_text))

async def _generate_quiz_async(note_text: str) -> list:
    client = _get_client()
    prompt = f"""Based on the following lecture notes, generate exactly 3 high-quality multiple choice review questions.
Return ONLY a valid JSON array of objects without markdown formatting or code blocks:
[
  {{
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer_index": 0,
    "explanation": "Why this answer is correct."
  }}
]

Notes:
{note_text}"""

    res = await client.aio.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=[prompt],
    )
    raw = (res.text or "").strip()
    if "```json" in raw:
        raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in raw:
        raw = raw.split("```", 1)[1].split("```", 1)[0].strip()
    start_idx = raw.find("[")
    end_idx = raw.rfind("]")
    if start_idx != -1 and end_idx != -1:
        raw = raw[start_idx : end_idx + 1]
    try:
        return json.loads(raw)
    except Exception:
        return []

def generate_note_quiz(note_text: str) -> list:
    """Generates 3 interactive MCQs based on note text."""
    return asyncio.run(_generate_quiz_async(note_text))
