import json
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from .config import config
from .renderer import render_html_template
from .tasks import create_render_task, create_task, wait_for_task

router = APIRouter(prefix="/api/infographic", tags=["infographic"])


@router.post("/create")
async def create_infographic(
    template_json: str = Form(...),
    product_image: UploadFile = File(...),
    remove_bg: str = Form(default="false"),
    title: str = Form(default=""),
    bullet_1: str = Form(default=""),
    bullet_2: str = Form(default=""),
    bullet_3: str = Form(default=""),
    bullet_4: str = Form(default=""),
    bullet_5: str = Form(default=""),
    bullet_6: str = Form(default=""),
    badge: str = Form(default=""),
    footer: str = Form(default=""),
) -> Response:
    # Парсим шаблон
    try:
        tmpl = json.loads(template_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid template_json")

    # Сохраняем фото товара
    ext = Path(product_image.filename or "photo.jpg").suffix or ".jpg"
    upload_path = config.uploads_dir / f"{uuid.uuid4()}{ext}"
    upload_path.write_bytes(await product_image.read())
    image_path = str(upload_path)

    # Удаление фона через worker если запрошено
    if remove_bg.lower() == "true":
        task_id = create_task("rembg", image_path)
        result_path = await wait_for_task(task_id, timeout=30)
        if result_path is None:
            raise HTTPException(
                status_code=503,
                detail="Сервис удаления фона временно недоступен. Загрузите фото с прозрачным фоном или снимите галочку.",
            )
        image_path = result_path

    # Собираем тексты
    bullets = [b for b in [bullet_1, bullet_2, bullet_3, bullet_4, bullet_5, bullet_6] if b.strip()]
    user_texts = {
        "title": title,
        "bullets": bullets,
        "badge": badge,
        "footer": footer,
    }

    # Генерируем HTML (фото встроено как base64)
    html_content = render_html_template(tmpl, image_path, user_texts)

    # Отправляем на рендер worker'у
    render_task_id = create_render_task(html_content)
    render_result = await wait_for_task(render_task_id, timeout=30)
    if render_result is None:
        raise HTTPException(status_code=503, detail="Render error: worker timeout or failure")

    png_bytes = Path(render_result).read_bytes()
    return Response(content=png_bytes, media_type="image/png")
