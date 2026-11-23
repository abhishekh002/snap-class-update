"""Optional Zep graph retrieval for the SmartClass study tutor."""

import logging
import os
from functools import lru_cache

import streamlit as st

logger = logging.getLogger(__name__)
MAX_QUERY_LENGTH = 256
MAX_CONTEXT_CHARS = 8000


def _setting(name: str) -> str:
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return str(value or os.environ.get(name) or "").strip()


@lru_cache(maxsize=1)
def _client():
    api_key = _setting("ZEP_API_KEY")
    if not api_key:
        return None
    try:
        from zep_cloud import Zep
    except ImportError:
        logger.warning("zep-cloud is not installed; continuing without graph context.")
        return None
    return Zep(api_key=api_key)


def search_study_context(query: str) -> str:
    """Return relevant public course reference chunks, or empty if Zep is unset."""
    user_id = _setting("ZEP_DOCS_USER_ID")
    client = _client()
    if not client or not user_id or not query.strip():
        return ""

    try:
        results = client.graph.search(
            user_id=user_id,
            query=query.strip()[:MAX_QUERY_LENGTH],
            scope="episodes",
            limit=5,
        )
    except Exception:
        logger.warning("Zep graph search failed; continuing without graph context.")
        return ""

    episodes = getattr(results, "episodes", None) or []
    snippets = []
    for episode in episodes:
        content = getattr(episode, "content", None) or getattr(episode, "data", None)
        if isinstance(content, str) and content.strip():
            snippets.append(content.strip())

    context = "\n\n---\n\n".join(snippets)
    return context[:MAX_CONTEXT_CHARS]