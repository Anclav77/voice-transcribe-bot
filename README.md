# Voice Transcribe Bot

Telegram-бот: принимает голосовые сообщения, распознаёт речь локально через
Whisper (faster-whisper, модель `base`, int8), затем отправляет текст в
DeepSeek для расстановки пунктуации и чистки от слов-паразитов.

## Требования

- Docker + Docker Compose (продовый вариант)
- либо Python 3.10+ и ffmpeg (для локального запуска без Docker)
- Токен Telegram-бота (получить у [@BotFather](https://t.me/BotFather))
- API-ключ DeepSeek (https://platform.deepseek.com)

## Деплой на сервере (Docker)

```bash
git clone <ssh-url-репозитория> voice-transcribe-bot
cd voice-transcribe-bot
cp .env.example .env
nano .env   # впишите TELEGRAM_BOT_TOKEN и DEEPSEEK_API_KEY
docker compose up -d --build
docker compose logs -f
```

Секреты (`.env`) не попадают в git — правьте их прямо на сервере.

Контейнер ограничен по памяти (`mem_limit: 1200m` в `docker-compose.yml`),
чтобы модель Whisper не съела память у других процессов на сервере. Веса
модели кэшируются в docker-volume `whisper-cache` — при пересоздании
контейнера повторно не скачиваются.

Полезные команды:

```bash
docker compose restart          # перезапуск после правки .env
docker compose pull && docker compose up -d --build   # обновить код
docker compose down             # остановить и удалить контейнер
```

## Локальный запуск без Docker (для разработки)

```bash
sudo apt install -y ffmpeg python3-venv   # Linux
# или: winget install ffmpeg               # Windows

python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # впишите токены
python bot.py
```

При первом запуске faster-whisper скачает веса модели (~150 МБ для `base`)
в кэш (`~/.cache/huggingface`). Дальнейшие запуски используют кэш.

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

На проде (VPS ~2 ГБ RAM, делится с другими ботами и БД) модель `base` —
безопасный выбор. `small` даёт качество получше, но требует ~2 ГБ и
рискует упереться в память вместе с соседними процессами — переключайте
только если на сервере есть запас (проверьте `free -h` и `docker stats`
после переключения). `medium`/`large` на этом сервере не запустятся.

## Как это работает

1. Пользователь присылает голосовое сообщение в Telegram.
2. Бот скачивает файл (`.oga`) во временную папку.
3. `faster-whisper` распознаёт речь локально (без внешних API).
4. Сырой текст уходит в DeepSeek с промптом «расставь пунктуацию, убери
   слова-паразиты, не меняй смысл».
5. Готовый текст отправляется пользователю.

Если DeepSeek недоступен или вернул ошибку — бот отправит сырую
расшифровку без обработки, чтобы не терять результат.
