import streamlit as st
from src.ai.agent import ask_snapclass_ai
from src.components.tts_player import render_tts_player


def _request_ai_response(message: str):
    try:
        return ask_snapclass_ai(message)
    except RuntimeError as error:
        st.error(str(error))
        return None


@st.dialog("🤖 SmartClass AI Tutor & Assistant", width="large")
def ai_chat_dialog(initial_prompt: str = None):
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
            @media (max-width: 640px) { .smart-tutor-hero { padding: 18px; } }
        </style>
        <section class="smart-tutor-hero">
          <span class="eyebrow">Your learning companion</span>
          <h2>Learn at your pace</h2>
          <p>Ask about class topics, course notes, attendance, or study plans.</p>
        </section>
    """, unsafe_allow_html=True)

    if "snapclass_ai_messages" not in st.session_state:
        st.session_state.snapclass_ai_messages = [
            {
                "role": "assistant",
                "content": "Hi! 👋 I'm your SmartClass AI Tutor. How can I assist you with your studies or attendance today?",
            }
        ]

    # If an initial prompt was passed (e.g. from a specific note)
    if initial_prompt and (
        "last_initial_prompt" not in st.session_state
        or st.session_state.last_initial_prompt != initial_prompt
    ):
        st.session_state.last_initial_prompt = initial_prompt
        st.session_state.snapclass_ai_messages.append({"role": "user", "content": initial_prompt})
        with st.spinner("AI Tutor is thinking..."):
            reply = _request_ai_response(initial_prompt)
            if reply is not None:
                st.session_state.snapclass_ai_messages.append({"role": "assistant", "content": reply})

    # Render chat container
    chat_container = st.container(height=380)
    with chat_container:
        for index, msg in enumerate(st.session_state.snapclass_ai_messages):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    render_tts_player(msg["content"], f"ai_chat_{index}")

    # Chat input
    user_input = st.chat_input("Type your question here...")
    if user_input:
        st.session_state.snapclass_ai_messages.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = _request_ai_response(user_input)
                if reply is not None:
                    reply_index = len(st.session_state.snapclass_ai_messages)
                    st.markdown(reply)
                    render_tts_player(reply, f"ai_chat_{reply_index}")
        if reply is not None:
            st.session_state.snapclass_ai_messages.append({"role": "assistant", "content": reply})
