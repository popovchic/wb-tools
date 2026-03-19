#!/usr/bin/env python3
"""P40 Worker — поллит VPS, забирает задачи rembg, возвращает результат."""

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

            if task_type == "rembg":
                try:
                    result_bytes = process_rembg(input_bytes)
                    requests.post(
                        f"{VPS_URL}/api/tasks/{task_id}/result",
                        headers=HEADERS,
                        files={"file": ("result.png", io.BytesIO(result_bytes), "image/png")},
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
            else:
                log.warning("Unknown task type: %s", task_type)
                requests.post(
                    f"{VPS_URL}/api/tasks/{task_id}/error",
                    headers=HEADERS,
                    params={"error": f"Unknown task type: {task_type}"},
                    timeout=10,
                )

        except requests.RequestException as exc:
            log.error("Network error: %s", exc)
            time.sleep(POLL_INTERVAL)
            continue

        time.sleep(0.5)


if __name__ == "__main__":
    run()
