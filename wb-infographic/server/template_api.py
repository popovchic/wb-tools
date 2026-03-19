import base64
import json

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .config import config

router = APIRouter(prefix="/api/template", tags=["template"])

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

CREATE_PROMPT = """Ты — дизайнер инфографики для маркетплейсов. Проанализируй загруженное изображение инфографики товара и создай JSON-описание шаблона.

Определи:
1. Общую компоновку (layout): где фото товара, где текстовые блоки, где иконки
2. Цветовую схему: фон, цвет текста, акцентные цвета
3. Типографику: примерный размер заголовков, буллетов, подписей
4. Стиль: минималистичный/яркий/premium и т.д.

Пользователь просит: {instructions}

Верни строго JSON (без markdown):
{{
  "layout": {{
    "background_color": "#hex",
    "background_gradient": null,
    "product_image": {{
      "position": "left|right|center|top|bottom",
      "width_percent": 50,
      "offset_x_percent": 0,
      "offset_y_percent": 0
    }}
  }},
  "title": {{
    "text": "{{{{title}}}}",
    "position": "top-left|top-right|top-center",
    "font_size": 36,
    "font_weight": "bold",
    "color": "#hex",
    "max_width_percent": 80
  }},
  "bullets": [
    {{
      "icon": "emoji или null",
      "text": "{{{{bullet_1}}}}",
      "font_size": 20,
      "color": "#hex"
    }}
  ],
  "bullets_position": "left|right|bottom",
  "badge": null,
  "footer": null,
  "style_notes": "краткое описание стиля"
}}"""

MODIFY_PROMPT = """Ты — дизайнер инфографики для маркетплейсов. Вот текущий JSON-шаблон инфографики:
{template_json}

Пользователь просит внести изменения: {instructions}

Внеси изменения и верни обновлённый JSON. Сохрани все поля которые не упомянуты в инструкции. Верни строго JSON (без markdown)."""


async def call_openrouter(messages: list, model: str) -> str:
    if not config.openrouter_api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {config.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"OpenRouter error: {resp.text}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def parse_json_response(text: str) -> dict:
    """Парсит JSON из ответа модели, убирая возможные markdown-блоки."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"Invalid JSON from model: {e}")


@router.post("/create")
async def create_template(
    image: UploadFile = File(...),
    instructions: str = Form(default=""),
) -> dict:
    """Анализирует образец инфографики и создаёт JSON-шаблон."""
    image_bytes = await image.read()
    image_b64 = base64.b64encode(image_bytes).decode()
    media_type = image.content_type or "image/jpeg"

    prompt = CREATE_PROMPT.format(instructions=instructions or "без особых пожеланий")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{image_b64}"},
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]

    text = await call_openrouter(messages, config.openrouter_model)
    template = parse_json_response(text)
    return template


@router.post("/modify")
async def modify_template(
    template_json: str = Form(...),
    instructions: str = Form(...),
) -> dict:
    """Модифицирует существующий шаблон по текстовым инструкциям."""
    prompt = MODIFY_PROMPT.format(
        template_json=template_json,
        instructions=instructions,
    )

    messages = [{"role": "user", "content": prompt}]

    # DeepSeek V3 для текстовых правок (дешевле, vision не нужен)
    text = await call_openrouter(messages, "deepseek/deepseek-chat")
    template = parse_json_response(text)
    return template
