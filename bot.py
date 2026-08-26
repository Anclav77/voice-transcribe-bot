import asyncio
import logging
import os
import tempfile

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import BufferedInputFile, Message

from config import settings
from deepseek_client import polish_text
from diarization import assign_speakers, diarize
from pdf_export import build_pdf
from transcriber import Transcriber, join_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 4096

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()
transcriber = Transcriber(
    model_size=settings.whisper_model_size,
    device=settings.whisper_device,
    compute_type=settings.whisper_compute_type,
)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Пришлите голосовое сообщение — я расшифрую его в текст.\n"
        "Распознавание речи работает локально (Whisper), а DeepSeek дополнительно "
        "расставляет пунктуацию и убирает слова-паразиты."
    )


@dp.message(F.voice | F.audio)
async def handle_voice(message: Message) -> None:
    file_id = message.voice.file_id if message.voice else message.audio.file_id
    status = await message.answer("Расшифровываю...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        local_path = os.path.join(tmp_dir, f"{file_id}.oga")
        tg_file = await bot.get_file(file_id)
        await bot.download_file(tg_file.file_path, destination=local_path)

        try:
            segments, duration = await asyncio.to_thread(transcriber.transcribe, local_path)
        except Exception:
            logger.exception("Ошибка распознавания речи")
            await status.edit_text("Не получилось распознать сообщение. Попробуйте ещё раз.")
            return

        raw_text = join_text(segments)
        if not raw_text.strip():
            await status.edit_text("Не удалось разобрать речь в сообщении.")
            return

        if duration >= settings.diarization_min_seconds:
            try:
                turns = await asyncio.to_thread(diarize, local_path)
                raw_text = assign_speakers(segments, turns)
            except Exception:
                logger.exception("Ошибка диаризации, отдаю текст без разделения по спикерам")

    final_text = raw_text
    if settings.enable_deepseek_polish:
        try:
            final_text = await polish_text(raw_text)
        except Exception:
            logger.exception("Ошибка DeepSeek, отдаю сырой текст без обработки")

    await status.edit_text(final_text[:TELEGRAM_MESSAGE_LIMIT])
    for start in range(TELEGRAM_MESSAGE_LIMIT, len(final_text), TELEGRAM_MESSAGE_LIMIT):
        await message.answer(final_text[start : start + TELEGRAM_MESSAGE_LIMIT])

    try:
        pdf_bytes = await asyncio.to_thread(build_pdf, final_text)
        await message.answer_document(
            BufferedInputFile(pdf_bytes, filename="transcript.pdf"),
            caption="Расшифровка в PDF",
        )
    except Exception:
        logger.exception("Ошибка генерации PDF")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
