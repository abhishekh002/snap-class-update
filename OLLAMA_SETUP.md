# Local DeepSeek-R1 in SnapClass

SnapClass AI chat offers **Local DeepSeek-R1 (Ollama)** alongside Gemini. The local option sends chat history to the Ollama service running on the same machine as Streamlit. It shows a short thinking status while generating and displays only the final answer, not the model's private reasoning. In this mode, SnapClass does not send chat prompts to Google or Zep.

## Setup on Windows

Ollama and the `deepseek-r1:1.5b` model are installed locally on this computer. The model download is about 1.1 GB. If you need to set them up on another computer:

1. Install Ollama from [Ollama for Windows](https://ollama.com/download/windows). The official Windows standalone ZIP is also available from [Ollama releases](https://github.com/ollama/ollama/releases).
2. Pull a small DeepSeek-R1 model:

   ```powershell
   ollama pull deepseek-r1:1.5b
   ```

3. Start Ollama before launching SnapClass. If Ollama is installed under the normal user Programs folder, run:

   ```powershell
   .\scripts\start_local_ollama.ps1
   ```

4. Launch SnapClass in its project environment:

   ```powershell
   .\.venv\Scripts\streamlit.exe run app.py
   ```

5. Open **SnapClass AI Learning Studio → Chat with SnapClass AI** and choose **Local DeepSeek-R1 (Ollama)**.

The default model is `deepseek-r1:1.5b`. To use another model already pulled into Ollama, set `OLLAMA_MODEL`. To use a different Ollama server, set `OLLAMA_BASE_URL` (default: `http://localhost:11434`). The app uses Ollama's local `/api/chat` endpoint, so it does not need the separate Python `ollama` package.

This feature runs locally only when Ollama and Streamlit run on the same machine. If SnapClass is hosted remotely, `localhost` refers to that server, not your computer.