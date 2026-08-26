import os
import threading

from pyannote.audio import Pipeline

_lock = threading.Lock()
_pipeline: Pipeline | None = None


def _get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        with _lock:
            if _pipeline is None:
                token = os.environ.get("HF_TOKEN")
                if not token:
                    raise RuntimeError("HF_TOKEN не задан в .env — диаризация недоступна")
                _pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1", use_auth_token=token
                )
    return _pipeline


def diarize(audio_path: str) -> list[tuple[float, float, str]]:
    annotation = _get_pipeline()(audio_path)
    return [
        (segment.start, segment.end, speaker)
        for segment, _, speaker in annotation.itertracks(yield_label=True)
    ]


def _best_speaker(start: float, end: float, turns: list[tuple[float, float, str]]) -> str:
    best_overlap = 0.0
    best_speaker = "SPEAKER_00"
    for t_start, t_end, speaker in turns:
        overlap = min(end, t_end) - max(start, t_start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = speaker
    return best_speaker


def _label_for(speaker: str, order: list[str]) -> str:
    if speaker not in order:
        order.append(speaker)
    return f"Спикер {order.index(speaker) + 1}"


def assign_speakers(
    segments: list[tuple[float, float, str]], turns: list[tuple[float, float, str]]
) -> str:
    order: list[str] = []
    blocks: list[tuple[str, list[str]]] = []

    for start, end, text in segments:
        speaker = _best_speaker(start, end, turns)
        label = _label_for(speaker, order)
        if blocks and blocks[-1][0] == label:
            blocks[-1][1].append(text)
        else:
            blocks.append((label, [text]))

    return "\n\n".join(f"{label}: {' '.join(words)}" for label, words in blocks)
