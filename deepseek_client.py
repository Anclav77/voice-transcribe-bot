from openai import AsyncOpenAI

from config import settings

_client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url="https://api.deepseek.com")

_SYSTEM_PROMPT = (
    "Ты редактируешь расшифровку голосового сообщения. Расставь знаки препинания, "
    "раздели текст на предложения и абзацы, убери слова-паразиты (\"эм\", \"ну\", \"короче\", "
    "повторы слов). Не меняй смысл, не добавляй ничего от себя и не сокращай содержание. "
    "Если текст размечен по репликам вида \"Спикер 1: ...\", \"Спикер 2: ...\" — сохрани эту "
    "структуру построчно, не объединяй и не переставляй реплики разных спикеров, обрабатывай "
    "текст только внутри реплики каждого спикера. "
    "Верни только готовый текст, без пояснений."
)


async def polish_text(raw_text: str) -> str:
    response = await _client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()
