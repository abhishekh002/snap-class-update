"""Optional local Janus image-question answering for SnapClass AI."""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
import os
from pathlib import Path
import sys


DEFAULT_MODEL = "deepseek-ai/Janus-Pro-1B"


@lru_cache(maxsize=2)
def _load_janus(model_name: str):
    """Load Janus once per model in the current app process."""
    # Resolve the checked-out Janus source even if this interpreter has not
    # registered the editable install in site-packages.
    janus_checkout = Path(__file__).resolve().parents[2] / "Janus"
    if (janus_checkout / "janus" / "models").is_dir():
        checkout_path = str(janus_checkout)
        if checkout_path not in sys.path:
            sys.path.insert(0, checkout_path)

    try:
        import streamlit as st
        import torch
        from transformers import AutoModelForCausalLM
        from janus.models import MultiModalityCausalLM, VLChatProcessor
    except ImportError as error:
        missing_module = getattr(error, "name", None) or "a required dependency"
        raise RuntimeError(
            f"Janus could not import {missing_module} in this Streamlit environment. "
            "Install its dependencies in the same Python environment with "
            "`python -m pip install -r requirements-janus.txt`, then restart SnapClass."
        ) from error

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    else:
        # CPU kernels often do not support float16; use float32 for reliable inference.
        dtype = torch.float32
    with st.spinner(f"Loading {model_name} for image questions (first load downloads the model)..."):
        processor = VLChatProcessor.from_pretrained(model_name)
        model: MultiModalityCausalLM = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
        )
        model = model.to(device=device, dtype=dtype).eval()
    return model, processor, device, dtype


def ask_janus_about_image(
    image_bytes: bytes,
    question: str,
    model_name: str | None = None,
) -> str:
    """Answer a question about an uploaded image using the local Janus model."""
    from PIL import Image
    import torch

    model_name = model_name or os.environ.get("JANUS_MODEL", DEFAULT_MODEL)
    model, processor, device, dtype = _load_janus(model_name)
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    # Keep unusually large uploads from making CPU inference slower than needed.
    image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    conversation = [
        {
            "role": "<|User|>",
            "content": f"<image_placeholder>\n{question.strip()}",
            "images": [image],
        },
        {"role": "<|Assistant|>", "content": ""},
    ]
    inputs = processor(
        conversations=conversation,
        images=[image],
        force_batchify=True,
    ).to(device, dtype=dtype)

    with torch.inference_mode():
        embeddings = model.prepare_inputs_embeds(**inputs)
        output = model.language_model.generate(
            inputs_embeds=embeddings,
            attention_mask=inputs.attention_mask,
            pad_token_id=processor.tokenizer.eos_token_id,
            bos_token_id=processor.tokenizer.bos_token_id,
            eos_token_id=processor.tokenizer.eos_token_id,
            max_new_tokens=128,
            do_sample=False,
            use_cache=True,
        )
    answer = processor.tokenizer.decode(
        output[0].detach().cpu().tolist(), skip_special_tokens=True
    ).strip()
    return answer or "I couldn't read enough from that image to answer. Try a clearer photo."
