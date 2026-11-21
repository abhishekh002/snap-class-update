import streamlit as st
from src.ai.agent import ask_snapclass_ai
from src.components.tts_player import render_tts_player


def _request_ai_response(message: str):
    try:
        return ask_snapclass_ai(message)
    except RuntimeError as error:
        st.error(str(error))
        return None


@st.dialog("🤖 SnapClass AI Tutor & Assistant", width="large")
def ai_chat_dialog(initial_prompt: str = None):
    st.caption("Ask questions about your subjects, understand course notes, or get study help!")

    if "snapclass_ai_messages" not in st.session_state:
        st.session_state.snapclass_ai_messages = [
            {
                "role": "assistant",
                "content": "Hi! 👋 I'm your SnapClass AI Tutor. How can I assist you with your studies or attendance today?",
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
