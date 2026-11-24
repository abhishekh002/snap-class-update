# Janus image questions in SnapClass

SnapClass AI chat can use DeepSeek Janus-Pro-1B to answer questions about an uploaded worksheet, textbook page, diagram, or classroom board photo. Text chat continues using the existing SnapClass providers.

## Install locally

Run these commands from the SnapClass project root in PowerShell. Use the exact `.venv` interpreter for installation and launch so `pip` and Streamlit cannot target different Python environments. If the `Janus` folder is missing, clone it first:

```powershell
git clone https://github.com/deepseek-ai/Janus.git
```

Then install the runtime dependencies into the app environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-janus.txt
```

The app imports the checked-out Janus source directly, so an editable package build is not required.

The Janus install file pins Transformers below version 5 because Janus currently requires the Transformers 4 API. Then restart Streamlit. The first image question downloads the `deepseek-ai/Janus-Pro-1B` model weights and loads them into memory. The model stays loaded for later questions while the app process is running. A CUDA GPU is recommended; CPU can run the model but may be slow. To use a different compatible Janus checkpoint, set `JANUS_MODEL` in the server environment (default: `deepseek-ai/Janus-Pro-1B`).

On this computer, use the newly created environment because the old `venv` points to a removed Python 3.11 installation:

```powershell
 .\.venv\Scripts\python.exe -m streamlit run app.py
```

This environment currently has CPU-only PyTorch. Janus inference will run on the CPU until a CUDA-enabled PyTorch build is installed. The model weights have not been downloaded yet; Janus downloads them the first time someone asks a question about an image.

## Use it

Open **SnapClass AI Learning Studio**, choose **Chat with SnapClass AI**, upload an image in **Ask about a picture**, and submit a question in the chat box. Janus analyzes the image on the SnapClass server and returns an answer in the chat.

The image is not uploaded to Google or Zep by this feature. Install Janus only on a server where you have enough memory and compute for the model. Follow the [Janus project license](https://github.com/deepseek-ai/Janus#license) for model use.
