# Voice Transcribe Bot

Telegram-бот: принимает голосовые сообщения, распознаёт речь локально через
Whisper (faster-whisper, модель `base`, int8), отправляет текст в DeepSeek
для расстановки пунктуации и чистки от слов-паразитов, присылает
расшифровку текстом и PDF-файлом. Для сообщений длиннее
`DIARIZATION_MIN_SECONDS` (по умолчанию 180 сек) дополнительно разделяет
речь по спикерам (pyannote.audio).

## Требования

- Docker + Docker Compose (продовый вариант)
- либо Python 3.10+ и ffmpeg (для локального запуска без Docker)
- Токен Telegram-бота (получить у [@BotFather](https://t.me/BotFather))
- API-ключ DeepSeek (https://platform.deepseek.com)
- Токен HuggingFace для диаризации по спикерам (см. ниже)

### Токен HuggingFace (для разделения по спикерам)

1. Зарегистрируйтесь на [huggingface.co](https://huggingface.co)
2. Примите условия использования на страницах моделей (иначе диаризация не
   заработает — вернёт ошибку доступа):
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
3. Создайте токен: https://huggingface.co/settings/tokens (права read
   достаточно) и впишите его в `.env` как `HF_TOKEN`

Без `HF_TOKEN` бот продолжит работать как обычно — просто длинные
сообщения будут приходить без разделения по спикерам (ошибка
диаризации логируется и не ломает остальную обработку).

## Деплой на сервере (Docker)

```bash
git clone <ssh-url-репозитория> voice-transcribe-bot
cd voice-transcribe-bot
cp .env.example .env
nano .env   # впишите TELEGRAM_BOT_TOKEN, DEEPSEEK_API_KEY, HF_TOKEN
docker compose up -d --build
docker compose logs -f
```

Секреты (`.env`) не попадают в git — правьте их прямо на сервере.

Контейнер ограничен по памяти (`mem_limit: 1800m` в `docker-compose.yml`),
чтобы не отобрать память у других процессов на сервере. Веса моделей
(Whisper и pyannote) кэшируются в docker-volume `whisper-cache` — при
пересоздании контейнера повторно не скачиваются.

Полезные команды:

```bash
docker compose up -d            # пересоздать контейнер после правки .env
                                 # (docker compose restart НЕ перечитывает .env!)
git pull && docker compose up -d --build   # обновить код
docker compose down             # остановить и удалить контейнер
```

## Локальный запуск без Docker (для разработки)

```bash
sudo apt install -y ffmpeg python3-venv libsndfile1   # Linux
# или: winget install ffmpeg                            # Windows

python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # впишите токены
python bot.py
```

При первом запуске faster-whisper скачает веса модели (~150 МБ для
`base`) в кэш (`~/.cache/huggingface`). Модель диаризации (pyannote)
скачивается лениво — только при первом голосовом сообщении длиннее
порога. Дальнейшие запуски используют кэш.

## Настройки (.env)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | токен бота |
| `DEEPSEEK_API_KEY` | — | ключ DeepSeek API |
| `WHISPER_MODEL_SIZE` | `base` | `tiny`/`base`/`small`/`medium`/`large-v3` |
| `WHISPER_DEVICE` | `cpu` | `cpu` или `cuda`, если есть GPU |
| `WHISPER_COMPUTE_TYPE` | `int8` | квантование; `int8` обязателен на слабом CPU |
| `DEEPSEEK_MODEL` | `deepseek-chat` | модель DeepSeek |
| `ENABLE_DEEPSEEK_POLISH` | `true` | выключить, если нужна только сырая расшифровка |
| `DIARIZATION_MIN_SECONDS` | `180` | порог длительности для разделения по спикерам |
| `HF_TOKEN` | — | токен HuggingFace для pyannote (см. выше) |
| `PDF_FONT_PATH` | — | путь к TTF-шрифту с кириллицей, если авто-поиск не находит |

На проде (VPS ~2 ГБ RAM, делится с другими ботами и БД) модель `base` —
безопасный выбор. `small` даёт качество получше, но требует ~2 ГБ и
рискует упереться в память вместе с соседними процессами — переключайте
только если на сервере есть запас (проверьте `free -h` и `docker stats`
после переключения). `medium`/`large` на этом сервере не запустятся.

Диаризация (pyannote.audio + torch CPU) добавляет заметный вес: образ
становится больше, а после первого длинного сообщения модель остаётся в
памяти контейнера. Поэтому запускается только для сообщений длиннее
`DIARIZATION_MIN_SECONDS`, а не на каждое голосовое.

## Как это работает

1. Пользователь присылает голосовое сообщение в Telegram.
2. Бот скачивает файл (`.oga`) во временную папку.
3. `faster-whisper` распознаёт речь локально, с таймкодами по сегментам.
4. Если длительность ≥ `DIARIZATION_MIN_SECONDS` — `pyannote.audio`
   определяет, где говорит какой спикер, и сегменты размечаются как
   «Спикер 1: ...», «Спикер 2: ...».
5. Текст (с разметкой спикеров или без) уходит в DeepSeek — расставить
   пунктуацию и убрать слова-паразиты, сохраняя структуру реплик.
6. Готовый текст отправляется сообщением и дополнительно PDF-файлом.

Если DeepSeek, диаризация или генерация PDF дают сбой — бот не падает:
отправляет то, что успел получить на предыдущем шаге (например, сырую
расшифровку без пунктуации, или без PDF).
