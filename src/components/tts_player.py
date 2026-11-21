import hashlib
import json

import streamlit.components.v1 as components


MAX_SPEECH_CHUNK_CHARS = 220


def _split_speech_text(text: str) -> list[str]:
    chunks = []
    current = ""

    for token in text.split():
        while len(token) > MAX_SPEECH_CHUNK_CHARS:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(token[:MAX_SPEECH_CHUNK_CHARS])
            token = token[MAX_SPEECH_CHUNK_CHARS:]

        candidate = f"{current} {token}".strip()
        if len(candidate) > MAX_SPEECH_CHUNK_CHARS:
            chunks.append(current)
            current = token
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks


def render_tts_player(text: str, key: str) -> None:
    button_id = "speech_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    safe_chunks = (
        json.dumps(_split_speech_text(text), ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    components.html(
        f"""
        <style>
        body {{ margin: 0; font-family: sans-serif; }}
        button {{
            min-height: 40px;
            padding: 0 16px;
            border: 0;
            border-radius: 8px;
            background: #2563eb;
            color: white;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
        }}
        button:hover {{ background: #1d4ed8; }}
        button:focus-visible {{ outline: 3px solid #93c5fd; outline-offset: 2px; }}
        </style>
        <button id="{button_id}" type="button" aria-pressed="false">▶ Play</button>
        <span id="{button_id}_status" aria-live="polite"></span>
        <script>
        const speechChunks = {safe_chunks};
        const button = document.getElementById("{button_id}");
        const status = document.getElementById("{button_id}_status");
        let isPlaying = false;
        let chunkIndex = 0;
        const resetButton = () => {{
            isPlaying = false;
            button.setAttribute("aria-pressed", "false");
            button.textContent = "▶ Play";
        }};
        const speakNextChunk = () => {{
            if (!isPlaying) return;
            if (chunkIndex >= speechChunks.length) {{
                resetButton();
                status.textContent = "Finished.";
                return;
            }}
            const utterance = new SpeechSynthesisUtterance(speechChunks[chunkIndex++]);
            utterance.rate = 1.0;
            utterance.onstart = () => {{ status.textContent = "Speaking..."; }};
            utterance.onend = speakNextChunk;
            utterance.onerror = (event) => {{
                resetButton();
                status.textContent = event.error === "canceled" || event.error === "interrupted"
                    ? "Stopped."
                    : "Speech error: " + event.error;
            }};
            window.speechSynthesis.speak(utterance);
        }};
        button.addEventListener("click", () => {{
            if (!("speechSynthesis" in window)) {{
                status.textContent = "Speech is unavailable in this browser.";
                return;
            }}
            if (isPlaying) {{
                window.speechSynthesis.cancel();
                resetButton();
                status.textContent = "Stopped.";
                return;
            }}
            window.speechSynthesis.cancel();
            chunkIndex = 0;
            isPlaying = true;
            button.setAttribute("aria-pressed", "true");
            button.textContent = "⏹ Stop";
            status.textContent = "Starting speech...";
            speakNextChunk();
        }});
        </script>
        """,
        height=54,
    )
