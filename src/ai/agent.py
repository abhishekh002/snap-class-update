import os
import asyncio
import streamlit as st
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner

def _get_api_key():
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        api_key = None
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Configure GOOGLE_API_KEY in Streamlit secrets or environment variables."
        )
    return str(api_key)


def _create_runner():
    os.environ["GOOGLE_API_KEY"] = _get_api_key()
    agent = Agent(
        model="gemini-flash-lite-latest",
        name="snapclass_tutor",
        description="SnapClass AI Assistant & Academic Tutor",
        instruction="""You are the AI Assistant & Study Tutor for SnapClass (AI-Powered Classroom Attendance & Management).
Your role:
1. Help teachers and students understand SnapClass features (facial recognition attendance, subject enrollment, notes).
2. Act as an intelligent Study Tutor: answer questions about classroom subjects, explain uploaded course notes, clarify complex academic concepts, and help students prepare for exams.
3. Keep answers clear, encouraging, educational, and structured with bullet points where helpful.""",
    )
    return InMemoryRunner(agent=agent)


_runner = None


def _get_runner():
    global _runner
    if _runner is None:
        _runner = _create_runner()
    return _runner

async def _ask_agent(message: str) -> str:
    events = await _get_runner().run_debug(message)
    for event in events:
        if event.content and event.content.parts:
            text = "".join(p.text for p in event.content.parts if p.text)
            if text:
                return text
    return "I am here to help you with SnapClass and your course study materials!"

def ask_snapclass_ai(message: str) -> str:
    """Synchronous caller for Streamlit UI."""
    return asyncio.run(_ask_agent(message))
