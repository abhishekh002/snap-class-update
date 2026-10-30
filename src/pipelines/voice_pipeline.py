import io

import numpy as np
import streamlit as st


def _load_voice_dependencies():
    try:
        import librosa
        from resemblyzer import VoiceEncoder, preprocess_wav
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Voice features require librosa and resemblyzer. "
            "Install them with `python -m pip install librosa resemblyzer`."
        ) from error
    return librosa, VoiceEncoder, preprocess_wav


@st.cache_resource
def load_voice_encoder():
    _, VoiceEncoder, _ = _load_voice_dependencies()
    return VoiceEncoder()


def get_voice_embedding(audio_bytes):
    if not audio_bytes:
        raise ValueError("Audio data must not be empty.")

    try:
        librosa, _, preprocess_wav = _load_voice_dependencies()
        audio, sample_rate = librosa.load(
            io.BytesIO(audio_bytes),
            sr=16000,
            mono=True,
        )
        wav = preprocess_wav(audio, source_sr=sample_rate)
        embedding = load_voice_encoder().embed_utterance(wav)
        return np.asarray(embedding, dtype=np.float32).tolist()
    except RuntimeError as error:
        st.error(str(error))
        return None


def identify_speaker(new_embedding, candidates_dict, threshold=0.65):
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    new_embedding = np.asarray(new_embedding, dtype=np.float32)
    if new_embedding.ndim != 1 or not np.isfinite(new_embedding).all():
        raise ValueError("The voice embedding must be a finite one-dimensional vector.")

    best_sid = None
    best_score = -1.0

    for sid, stored_embedding in candidates_dict.items():
        if stored_embedding is None:
            continue

        stored_embedding = np.asarray(stored_embedding, dtype=np.float32)
        if (
            stored_embedding.shape != new_embedding.shape
            or not np.isfinite(stored_embedding).all()
        ):
            continue

        similarity = float(np.dot(new_embedding, stored_embedding))
        if similarity > best_score:
            best_score = similarity
            best_sid = sid

    if best_sid is not None and best_score >= threshold:
        return best_sid, best_score
    return None, max(best_score, 0.0)


def process_bulk_audio(audio_bytes, candidates_dict, threshold=0.65):
    try:
        if not audio_bytes:
            raise ValueError("Audio data must not be empty.")

        librosa, _, preprocess_wav = _load_voice_dependencies()
        audio, sample_rate = librosa.load(
            io.BytesIO(audio_bytes),
            sr=16000,
            mono=True,
        )
        segments = librosa.effects.split(audio, top_db=30)

        identify_results = {}
        encoder = load_voice_encoder()

        for start, end in segments:
            if end - start < sample_rate * 0.5:
                continue

            wav = preprocess_wav(audio[start:end])
            embedding = encoder.embed_utterance(wav)
            student_id, score = identify_speaker(
                embedding,
                candidates_dict,
                threshold,
            )

            if student_id is not None and (
                student_id not in identify_results
                or score > identify_results[student_id]
            ):
                identify_results[student_id] = score

        return identify_results
    except Exception as error:
        raise RuntimeError(f"Bulk audio processing failed: {error}") from error
