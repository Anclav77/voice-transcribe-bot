from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_size: str, device: str, compute_type: str) -> None:
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str) -> tuple[list[tuple[float, float, str]], float]:
        segments, info = self._model.transcribe(audio_path, language="ru", vad_filter=True)
        result = [(s.start, s.end, s.text.strip()) for s in segments]
        return result, info.duration


def join_text(segments: list[tuple[float, float, str]]) -> str:
    return " ".join(text for _, _, text in segments)
