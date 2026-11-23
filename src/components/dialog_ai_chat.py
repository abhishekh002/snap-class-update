import logging
import streamlit as st
from google.genai.errors import APIError

logger = logging.getLogger(__name__)
from src.ai.agent import ask_snapclass_ai
from src.components.anam_avatar import render_anam_avatar
from src.components.markdown_utils import sanitize_mermaid_blocks
from src.components.tts_player import render_tts_player


def _request_ai_response(message: str):
    try:
        return ask_snapclass_ai(message)
    except RuntimeError as error:
        st.error(str(error))
        return None
    except APIError as error:
        status_code = getattr(error, "code", None)
        logger.warning("Gemini tutor request failed with HTTP status %s", status_code)
        if status_code == 429:
            return "The AI tutor has reached its Gemini usage limit. Please try again later."
        if status_code in {500, 502, 503, 504}:
            return "Gemini is temporarily unavailable. Please try again in a moment."
        return "Gemini could not complete that response. Check the Google API key and model access."
    except Exception as error:
        logger.warning("Unexpected tutor failure (%s)", type(error).__name__)
        return "I could not complete that response. Please try again."


@st.dialog("🎓 SmartClass Study & Teach Hub", width="large")
def ai_chat_dialog(initial_prompt: str = None, audience: str = None):
    st.markdown("""
        <style>
            .smart-tutor-hero {
                position: relative; overflow: hidden; margin: .15rem 0 1rem;
                padding: 22px 24px; border: 1px solid #31545b;
                border-radius: 19px;
                background: linear-gradient(128deg,#203a43,#315b54 72%,#3c6658);
                box-shadow: 0 12px 27px rgba(32,58,67,.16);
            }
            .smart-tutor-hero:after {
                content: "✦"; position: absolute; top: -24px; right: 20px;
                color: rgba(216,239,155,.16); font-size: 8rem; line-height: 1;
            }
            .smart-tutor-hero .eyebrow {
                color: #d8ef9b; font-size: .68rem; font-weight: 700;
                letter-spacing: .14em; text-transform: uppercase;
            }
            .smart-tutor-hero h2 {
                position: relative; z-index: 1; margin: 7px 0 5px;
                color: #fffefa; font-size: clamp(1.35rem,2.6vw,1.75rem);
                line-height: 1.2;
            }
            .smart-tutor-hero p {
                position: relative; z-index: 1; margin: 0;
                color: #e1ebe3; line-height: 1.55;
            }
            .stDialog [data-testid="stChatMessage"] {
                border: 1px solid #e2e8df; border-radius: 16px;
                background: #fffefa;
            }
            .stDialog [data-testid="stChatInput"] textarea {
                border-color: #9aaf9c; border-radius: 14px;
            }
            .hub-path-copy {
                margin: .2rem 0 .7rem;
                color: #536663;
                font-size: .9rem;
            }
            .hub-prompt-caption {
                margin: .8rem 0 .25rem;
                color: #385844;
                font-size: .78rem;
                font-weight: 700;
                letter-spacing: .08em;
                text-transform: uppercase;
            }
            .stDialog [data-testid="stHorizontalBlock"] .stButton > button {
                min-height: 3.1rem;
                white-space: normal;
                line-height: 1.2;
            }
            @media (max-width: 640px) { .smart-tutor-hero { padding: 18px; } }
        </style>
        <section class="smart-tutor-hero">
          <span class="eyebrow">One hub · two ways to grow</span>
          <h2>Study a topic or plan a great lesson</h2>
          <p>Choose a student or teacher desk, then start with a focused idea or ask Abhishekh anything.</p>
        </section>
    """, unsafe_allow_html=True)

    login_role = audience or st.session_state.get("login_type") or st.session_state.get("user_role")
    default_mode = "Teacher Desk" if login_role == "teacher" else "Student Desk"
    mode = st.radio(
        "Choose your desk",
        ["Student Desk", "Teacher Desk"],
        index=1 if default_mode == "Teacher Desk" else 0,
        horizontal=True,
        key=f"smartclass_ai_desk_{default_mode.lower().replace(' ', '_')}",
    )

    if mode == "Student Desk":
        st.markdown('<p class="hub-path-copy">Understand a class topic, review notes, make a study plan, or practice with a quiz.</p>', unsafe_allow_html=True)
        prompt_actions = [
            ("Explain a topic", "Help me understand a topic. Ask me which topic and my class level, then explain it step by step with an example and a quick check question."),
            ("Make a study plan", "Help me make a realistic study plan. Ask what subject or exam I am preparing for and how much time I have."),
            ("Quiz me", "Quiz me on a topic I choose. Ask one question at a time, wait for my answer, then explain it simply."),
            ("Review my notes", "Help me review my uploaded course notes. Ask which subject or note I want to study, then summarize the key ideas and ask a practice question."),
        ]
        audience_prompt = "Act as a friendly student tutor. Explain ideas clearly, encourage questions, and check understanding without giving away quiz answers too early."
    else:
        st.markdown('<p class="hub-path-copy">Prepare lessons, shape class discussions, make quick checks for understanding, or simplify a topic.</p>', unsafe_allow_html=True)
        prompt_actions = [
            ("Plan a lesson", "Help me plan a lesson. Ask for the class level, topic, and lesson duration, then suggest objectives, activities, and a closing check."),
            ("Start a discussion", "Help me create an engaging class discussion. Ask for the subject, topic, and class level, then suggest an opening question and follow-up prompts."),
            ("Create a quick quiz", "Help me create a short quiz for my class. Ask for the topic and class level, then provide questions and a separate answer key."),
            ("Simplify a topic", "Help me explain a difficult topic to my students. Ask for the topic and class level, then give a clear explanation and an example."),
        ]
        audience_prompt = "Act as a practical teaching partner. Keep suggestions classroom-ready, age-appropriate, and easy to adapt."

    st.markdown('<div class="hub-prompt-caption">Start with a quick action</div>', unsafe_allow_html=True)
    prompt_columns = st.columns(4, gap="small")
    selected_prompt = None
    for column, (label, prompt) in zip(prompt_columns, prompt_actions):
        with column:
            if st.button(label, key=f"hub_{mode.lower().replace(' ', '_')}_{label.lower().replace(' ', '_')}", width="stretch"):
                selected_prompt = f"{audience_prompt}\n\n{prompt}"

    render_anam_avatar()

    if "snapclass_ai_messages" not in st.session_state:
        st.session_state.snapclass_ai_messages = [
            {
                "role": "assistant",
                "content": "Hi! 👋 I'm your SmartClass AI Tutor. How can I assist you with your studies or attendance today?",
            }
        ]

    pending_prompt = selected_prompt or initial_prompt
    if pending_prompt and (
        "last_initial_prompt" not in st.session_state
        or st.session_state.last_initial_prompt != pending_prompt
    ):
        st.session_state.last_initial_prompt = pending_prompt
        st.session_state.snapclass_ai_messages.append({"role": "user", "content": pending_prompt})
        with st.spinner("Abhishekh is thinking..."):
            reply = _request_ai_response(pending_prompt)
            if reply is not None:
                st.session_state.snapclass_ai_messages.append({"role": "assistant", "content": reply})

    chat_container = st.container(height=380)
    with chat_container:
        for index, msg in enumerate(st.session_state.snapclass_ai_messages):
            with st.chat_message(msg["role"]):
                st.markdown(sanitize_mermaid_blocks(msg["content"]))
                if msg["role"] == "assistant":
                    render_tts_player(msg["content"], f"ai_chat_{index}")

    user_input = st.chat_input("Type your question here...")
    if user_input:
        st.session_state.snapclass_ai_messages.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(sanitize_mermaid_blocks(user_input))
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = _request_ai_response(user_input)
                if reply is not None:
                    reply_index = len(st.session_state.snapclass_ai_messages)
                    st.markdown(sanitize_mermaid_blocks(reply))
                    render_tts_player(reply, f"ai_chat_{reply_index}")
        if reply is not None:
            st.session_state.snapclass_ai_messages.append({"role": "assistant", "content": reply})
