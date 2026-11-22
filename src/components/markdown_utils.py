import re


def sanitize_mermaid_blocks(text: str | None) -> str:
    """Display Mermaid fences as plain code so malformed diagrams cannot break a page."""
    content = str(text or "")
    return re.sub(
        r"(?im)^([ \t]*\x60{3})[ \t]*mermaid\b[^\r\n]*",
        r"\1text",
        content,
    )
