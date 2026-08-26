import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    deepseek_api_key: str
    whisper_model_size: str
    whisper_device: str
    whisper_compute_type: str
    deepseek_model: str
    enable_deepseek_polish: bool


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


settings = Settings(
    telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
    deepseek_api_key=os.environ["DEEPSEEK_API_KEY"],
    whisper_model_size=os.getenv("WHISPER_MODEL_SIZE", "base"),
    whisper_device=os.getenv("WHISPER_DEVICE", "cpu"),
    whisper_compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
    deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    enable_deepseek_polish=_get_bool("ENABLE_DEEPSEEK_POLISH", True),
)
