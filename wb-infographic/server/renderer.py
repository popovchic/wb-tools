import base64
import io
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


def render_infographic(
    template_json: dict,
    product_image_path: str,
    user_texts: dict,
) -> bytes:
    """
    Рендерит инфографику через weasyprint.

    user_texts = {
        "title": "...",
        "bullets": ["...", "...", "..."],
        "badge": "...",   # опционально
        "footer": "...",  # опционально
    }

    Возвращает PNG bytes.
    """
    # Встраиваем фото товара как data URI чтобы weasyprint не делал HTTP запросы
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

    from weasyprint import CSS, HTML

    png_bytes = (
        HTML(string=html)
        .write_png(
            stylesheets=[
                CSS(string="@page { size: 900px 1200px; margin: 0; }")
            ]
        )
    )
    return png_bytes
