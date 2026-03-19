import base64
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def _image_to_data_uri(image_path: str) -> str:
    """Конвертирует изображение в data URI для встраивания в HTML."""
    path = Path(image_path)
    ext = path.suffix.lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(ext, "image/png")
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode()
    return f"data:{mime};base64,{b64}"


def render_html_template(
    template_json: dict,
    product_image_path: str,
    user_texts: dict,
) -> str:
    """
    Генерирует HTML-строку с встроенным фото товара (base64 data URI).

    user_texts = {
        "title": "...",
        "bullets": ["...", "...", "..."],
        "badge": "...",   # опционально
        "footer": "...",  # опционально
    }

    Возвращает HTML строку (самодостаточный файл без внешних зависимостей по изображениям).
    """
    product_image_src = _image_to_data_uri(product_image_path)

    tmpl = jinja_env.get_template("infographic.html")
    html = tmpl.render(
        layout=template_json["layout"],
        title=template_json["title"],
        bullets=template_json.get("bullets", []),
        bullets_position=template_json.get("bullets_position", "bottom"),
        badge=template_json.get("badge"),
        footer=template_json.get("footer"),
        product_image_src=product_image_src,
        texts=user_texts,
    )
    return html
