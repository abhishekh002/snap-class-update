# SmartClass AI architecture

![SmartClass AI architecture diagram](src/assets/smartclass-architecture.svg)

## Overview

SmartClass AI is a Streamlit application with Python application logic. Students and teachers use separate portals for face-based attendance, classes, course notes, and assessments. Supabase stores profiles, classroom records, and private course files.

The AI Learning Studio sends text and extracted document content to the configured Gemini model. Janus handles image questions locally, while Ollama can provide optional local text chat. If Zep credentials are configured, relevant knowledge-graph snippets can be added as context to tutor answers.

## Main flows

1. A student or teacher opens the relevant Streamlit portal.
2. Face ID and classroom-image attendance use the local Python face pipeline; attendance records are stored in Supabase.
3. Teachers upload course materials and publish assessments. Students access course resources and submit assessment work through their dashboard.
4. The AI Learning Studio extracts supported document text before sending it with a question to Gemini. Image questions use the local Janus model. Optional Zep retrieval supplies relevant graph context, and optional Ollama supports local text chat.

The diagram reflects the current application. It does not include the earlier Anam avatar or FastAPI architecture.
