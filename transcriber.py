from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_size: str, device: str, compute_type: str) -> None:
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str) -> str:
        segments, _ = self._model.transcribe(audio_path, language="ru", vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments)
