#!/usr/bin/env python3
"""Windows Worker — поллит VPS, забирает задачи rembg и render, возвращает результат."""

import asyncio
import io
import logging
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env")

VPS_URL = os.getenv("VPS_URL", "http://localhost:8000").rstrip("/")
WORKER_TOKEN = os.getenv("WORKER_TOKEN", "")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

HEADERS = {"X-Worker-Token": WORKER_TOKEN}


def process_rembg(image_bytes: bytes) -> bytes:
    from rembg import remove
    return remove(image_bytes)


async def render_html_to_png(html_bytes: bytes) -> bytes:
    """Принимает HTML как bytes, возвращает PNG как bytes через Playwright."""
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 900, "height": 1200})
        html_str = html_bytes.decode("utf-8")
        await page.set_content(html_str, wait_until="networkidle")
        png = await page.screenshot(type="png", full_page=False)
        await browser.close()
        return png


def run() -> None:
    log.info("Worker started. VPS: %s", VPS_URL)
    while True:
        try:
            resp = requests.get(f"{VPS_URL}/api/tasks/next", headers=HEADERS, timeout=10)
            if resp.status_code == 204:
                time.sleep(POLL_INTERVAL)
                continue
            resp.raise_for_status()
            task = resp.json()
            task_id = task["id"]
            task_type = task["type"]
            log.info("Got task %s type=%s", task_id, task_type)

            # Скачать входной файл
            dl = requests.get(f"{VPS_URL}/api/tasks/{task_id}/input", headers=HEADERS, timeout=30)
            dl.raise_for_status()
            input_bytes = dl.content

            try:
                if task_type == "rembg":
                    result_bytes = process_rembg(input_bytes)
                    filename = "result.png"
                    mime = "image/png"

                elif task_type == "render":
                    result_bytes = asyncio.run(render_html_to_png(input_bytes))
                    filename = "result.png"
                    mime = "image/png"

                else:
                    raise ValueError(f"Unknown task type: {task_type}")

                requests.post(
                    f"{VPS_URL}/api/tasks/{task_id}/result",
                    headers=HEADERS,
                    files={"file": (filename, io.BytesIO(result_bytes), mime)},
                    timeout=30,
                ).raise_for_status()
                log.info("Task %s done", task_id)

            except Exception as exc:
                log.error("Task %s failed: %s", task_id, exc)
                requests.post(
                    f"{VPS_URL}/api/tasks/{task_id}/error",
                    headers=HEADERS,
                    params={"error": str(exc)},
                    timeout=10,
                )

        except requests.RequestException as exc:
            log.error("Network error: %s", exc)
            time.sleep(POLL_INTERVAL)
            continue

        time.sleep(0.5)


if __name__ == "__main__":
    run()
