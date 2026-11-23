# Connect Abhishekh to SnapClass

The AI Tutor can retrieve study reference chunks from a Zep user graph and answer with the existing Google ADK Gemini tutor. The Anam voice avatar uses your portrait, the Dana voice, and Anam-hosted Google Gemini 3.5 Flash Lite.

## Configure Zep reference search

1. Rotate the Zep credential that was pasted into chat in your Zep account, then put the replacement in the local `.env` as `ZEP_API_KEY`. Do not reuse the pasted value.
2. Set `ZEP_DOCS_USER_ID` to the same graph user ID used by your ingestion data.
3. Put prepared chunks in `data/chunked-docs.json` with `context`, `heading`, and `content` fields, then run `python scripts/ingest_to_graph.py`.
4. The text AI Tutor retrieves up to five relevant graph episodes for each question. If Zep is not configured or unavailable, the tutor falls back to its normal Gemini response.

## Anam voice avatar

1. Anam Lab contains the saved **Abhishekh** persona using your uploaded portrait, `cara-4.1-express`, Dana voice, and Google Gemini 3.5 Flash Lite.
2. The restricted `SnapClass local` Anam API key is stored as `ANAM_API_KEY` in the local `.env`. It can create session tokens and has no resource read/write permissions.
3. `ANAM_VOICE_ID` and `ANAM_LLM_ID` in `.env` are the selected Dana voice and hosted Gemini model IDs. A Google key is not needed for this hosted model. To use a custom Gemini registration later, enter its Google key directly in Anam Lab and replace `ANAM_LLM_ID` with the custom LLM ID.
4. Anam session tokens are minted server-side. The browser never receives the Anam API key or a Google API key.

The voice avatar currently uses Anam-hosted Gemini and does not perform Zep graph retrieval for each spoken turn. Zep grounding is connected to the text tutor; per-turn Zep grounding in voice requires a publicly reachable custom LLM endpoint.

## Run the application

From the project root:

```powershell
streamlit run app.py
```

Open the AI Tutor, expand **Talk with Abhishekh**, then press **Start voice chat**. Allow microphone access when the browser asks. Closing the tutor dialog ends the stream.