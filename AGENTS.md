# Anam avatar integration rules

- Mint Anam session tokens on the server and send only the short-lived token to the browser.
- Keep `ANAM_API_KEY` out of client code, source control, logs, and chat. Store it only in server-side environment or Streamlit secrets.
- Keep custom LLM provider credentials in Anam's secure LLM registration, never in source code or the browser.
- Bundle the official Anam JavaScript SDK and verify its current published version from npm before updating it.
- Keep spoken avatar responses concise and conversational.
- If an API credential is pasted into chat, do not use it; tell the user to rotate it and store its replacement locally.
