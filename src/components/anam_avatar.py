import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st
import streamlit.components.v1 as components

from src.ai.agent import SMARTCLASS_SYSTEM_PROMPT

DEFAULT_AVATAR_ID = "e28617e7-f8ac-4e5d-91fa-061402151a97"
DEFAULT_AVATAR_MODEL = "cara-4.1-express"
SESSION_TOKEN_TTL_SECONDS = 55 * 60


def _setting(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    value = value or os.environ.get(name)
    return str(value or default).strip()


def _session_token() -> str:
    api_key = _setting("ANAM_API_KEY")
    if not api_key:
        raise RuntimeError("Set ANAM_API_KEY in your local .env or Streamlit secrets.")

    voice_id = _setting("ANAM_VOICE_ID")
    llm_id = _setting("ANAM_LLM_ID")
    avatar_id = _setting("ANAM_AVATAR_ID", DEFAULT_AVATAR_ID)
    avatar_model = _setting("ANAM_AVATAR_MODEL", DEFAULT_AVATAR_MODEL)
    missing = [name for name, value in (("ANAM_VOICE_ID", voice_id), ("ANAM_LLM_ID", llm_id)) if not value]
    if missing:
        raise RuntimeError("Set " + " and ".join(missing) + " in your local .env or Streamlit secrets.")

    cached = st.session_state.get("anam_session_token")
    if cached and cached.get("expires_at", 0) > time.time():
        return cached["token"]

    base_url = _setting("ANAM_API_BASE", "https://api.anam.ai").rstrip("/")
    payload = {
        "personaConfig": {
            "name": "Abhishekh",
            "avatarId": avatar_id,
            "avatarModel": avatar_model,
            "voiceId": voice_id,
            "llmId": llm_id,
            "systemPrompt": SMARTCLASS_SYSTEM_PROMPT
            + " Keep spoken responses concise and conversational.",
        }
    }
    request = Request(
        f"{base_url}/v1/auth/session-token",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"Anam could not create a session (HTTP {error.code}). Check your Anam settings.") from None
    except (URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError("Anam could not be reached. Check your connection and Anam settings.") from None

    token = result.get("sessionToken") if isinstance(result, dict) else None
    if not isinstance(token, str) or not token:
        raise RuntimeError("Anam returned an invalid session token. Check your Anam persona settings.")

    st.session_state["anam_session_token"] = {
        "token": token,
        "expires_at": time.time() + SESSION_TOKEN_TTL_SECONDS,
    }
    return token


def _avatar_html(session_token: str) -> str:
    bundle_path = Path(__file__).resolve().parents[1] / "assets" / "anam-sdk-bundle.js"
    if not bundle_path.is_file():
        raise RuntimeError("The Anam browser bundle is missing. Run npm install and npm run build in frontend/anam_ui.")

    bundle = bundle_path.read_text(encoding="utf-8").replace("</script", "<\\/script")
    token_literal = json.dumps(session_token).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    page = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; color: #203a43; font: 14px/1.45 system-ui, sans-serif; }
    .wrap { display: grid; gap: 10px; }
    video { display: block; width: 100%; max-height: 390px; aspect-ratio: 16/9; object-fit: cover;
      background: #162b30; border-radius: 16px; }
    .controls { display: flex; align-items: center; gap: 10px; }
    button { border: 0; border-radius: 10px; padding: 10px 15px; color: white;
      background: #176b5d; font: inherit; font-weight: 650; cursor: pointer; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    #stop { background: #596b6a; }
    #status { color: #536663; }
  </style>
</head>
<body>
  <div class="wrap">
    <video id="anam-video" autoplay playsinline aria-label="Abhishekh AI avatar"></video>
    <div class="controls">
      <button id="start" type="button">Start voice chat</button>
      <button id="stop" type="button" disabled>End chat</button>
      <span id="status" role="status" aria-live="polite">Ready when you are.</span>
    </div>
  </div>
  <script>/* ANAM_SDK_BUNDLE */
    const sessionToken = /* SESSION_TOKEN */;
    const startButton = document.getElementById("start");
    const stopButton = document.getElementById("stop");
    const status = document.getElementById("status");
    let client;

    async function stopAvatar() {
      stopButton.disabled = true;
      try {
        if (client && client.isStreaming()) await client.stopStreaming();
      } catch (_) {
        status.textContent = "Chat ended.";
      } finally {
        client = undefined;
        startButton.disabled = false;
      }
    }

    startButton.addEventListener("click", async () => {
      startButton.disabled = true;
      status.textContent = "Connecting. Allow microphone access if prompted.";
      try {
        client = window.createAnamClient(sessionToken);
        await client.streamToVideoElement("anam-video");
        stopButton.disabled = false;
        status.textContent = "Connected. Speak naturally to Abhishekh.";
      } catch (_) {
        await stopAvatar();
        status.textContent = "Could not connect. Check microphone permission and Anam setup.";
      }
    });

    stopButton.addEventListener("click", stopAvatar);
    window.addEventListener("pagehide", () => { void stopAvatar(); });
  </script>
</body>
</html>"""
    return page.replace("/* ANAM_SDK_BUNDLE */", bundle).replace("/* SESSION_TOKEN */", token_literal)


def render_anam_avatar() -> None:
    with st.expander("🎙️ Talk with Abhishekh", expanded=False):
        try:
            session_token = _session_token()
            components.html(_avatar_html(session_token), height=470, scrolling=False)
        except RuntimeError as error:
            st.info(str(error))
