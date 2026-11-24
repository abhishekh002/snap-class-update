"""Local DeepSeek-R1 chat via the Ollama HTTP API."""

from __future__ import annotations

import os
import re

import requests


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "deepseek-r1:1.5b"
LOCAL_SYSTEM_PROMPT = """You are SnapClass AI, a friendly study tutor and practical teaching partner.
Explain topics clearly, encourage questions, and use concise examples. Keep answers age-
appropriate and useful for learning. Do not reveal private internal reasoning; provide only
the explanation needed to teach the topic."""
_THINK_BLOCK = re.compile(r"<think>.*?</think>", flags=re.IGNORECASE | re.DOTALL)
_OPEN_THINK_BLOCK = re.compile(r"<think>.*$", flags=re.IGNORECASE | re.DOTALL)


def local_model_status() -> tuple[bool, str]:
    """Return whether the configured Ollama model is available locally."""
    base_url = os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=(1, 1))
        response.raise_for_status()
        installed = {item.get("name") for item in response.json().get("models", [])}
    except (requests.RequestException, ValueError, AttributeError):
        return False, "Ollama is not running on this computer."

    if model not in installed and f"{model.split(':')[0]}:latest" not in installed:
        return False, f"Ollama is running, but `{model}` is not installed."
    return True, ""


def _answer_text(content: str) -> str:
    """Remove DeepSeek's private reasoning tags and return only its answer."""
    answer = _THINK_BLOCK.sub("", content)
    answer = _OPEN_THINK_BLOCK.sub("", answer)
    return answer.replace("</think>", "").strip()


def ask_local_deepseek(messages: list[dict[str, str]]) -> str:
    """Ask the local Ollama model using the current chat history."""
    base_url = os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()
    if not messages:
        raise RuntimeError("Enter a question for DeepSeek-R1 first.")

    payload_messages = [{"role": "system", "content": LOCAL_SYSTEM_PROMPT}]
    payload_messages.extend(
        {
            "role": item["role"],
            "content": str(item.get("content", ""))[-6000:],
        }
        for item in messages[-12:]
        if item.get("role") in {"user", "assistant"}
    )

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": payload_messages,
                "stream": False,
                "keep_alive": "10m",
            },
            timeout=(5, 600),
        )
    except requests.ConnectionError as error:
        raise RuntimeError(
            "Could not connect to Ollama. Install and start Ollama on this computer, "
            f"then pull the model with `ollama pull {model}`."
        ) from error
    except requests.Timeout as error:
        raise RuntimeError("Ollama took too long to respond. Try again or use a smaller model.") from error

    if response.status_code == 404:
        raise RuntimeError(f"Ollama could not find `{model}`. Pull it with `ollama pull {model}`.")
    if not response.ok:
        raise RuntimeError(f"Ollama returned HTTP {response.status_code}. Check that its local service is running.")

    try:
        result = response.json()
        raw_answer = result.get("message", {}).get("content", "")
    except (ValueError, AttributeError) as error:
        raise RuntimeError("Ollama returned an unreadable response.") from error

    answer = _answer_text(str(raw_answer))
    if not answer:
        raise RuntimeError("DeepSeek-R1 did not return a final answer. Please try again.")
    return answer
