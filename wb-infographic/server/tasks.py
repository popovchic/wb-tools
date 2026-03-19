import asyncio
import sqlite3
import time
import uuid
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "tasks.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                input_path TEXT NOT NULL,
                output_path TEXT,
                error TEXT
            )
        """)
        conn.commit()


def create_task(task_type: str, input_path: str) -> str:
    task_id = str(uuid.uuid4())
    now = time.time()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO tasks (id, type, status, created_at, updated_at, input_path) VALUES (?, ?, 'pending', ?, ?, ?)",
            (task_id, task_type, now, now, input_path),
        )
        conn.commit()
    return task_id


def get_next_task() -> dict | None:
    """Возвращает следующую pending-задачу и переводит её в processing."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        now = time.time()
        conn.execute(
            "UPDATE tasks SET status = 'processing', updated_at = ? WHERE id = ?",
            (now, row["id"]),
        )
        conn.commit()
        return dict(row)


def complete_task(task_id: str, output_path: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE tasks SET status = 'done', output_path = ?, updated_at = ? WHERE id = ?",
            (output_path, time.time(), task_id),
        )
        conn.commit()


def fail_task(task_id: str, error: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE tasks SET status = 'error', error = ?, updated_at = ? WHERE id = ?",
            (error, time.time(), task_id),
        )
        conn.commit()


def get_task(task_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row else None


async def wait_for_task(task_id: str, timeout: float = 30.0) -> str | None:
    """Поллит SQLite каждые 0.5 сек. Возвращает output_path или None при ошибке/таймауте."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        task = get_task(task_id)
        if task is None:
            return None
        if task["status"] == "done":
            return task["output_path"]
        if task["status"] == "error":
            return None
        await asyncio.sleep(0.5)
    return None
