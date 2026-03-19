import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles

from .config import config
from .render_api import router as render_router
from .template_api import router as template_router
from .tasks import (
    complete_task,
    create_task,
    fail_task,
    get_next_task,
    get_task,
    init_db,
)

app = FastAPI(title="WB Infographic Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

worker_token_header = APIKeyHeader(name="X-Worker-Token", auto_error=False)


app.include_router(template_router)
app.include_router(render_router)


@app.on_event("startup")
async def startup() -> None:
    init_db()


def verify_worker_token(token: str | None = Depends(worker_token_header)) -> None:
    if not config.worker_token:
        raise HTTPException(status_code=500, detail="WORKER_TOKEN not configured")
    if token != config.worker_token:
        raise HTTPException(status_code=401, detail="Invalid worker token")


# ---------------------------------------------------------------------------
# Worker API endpoints
# ---------------------------------------------------------------------------

@app.get("/api/tasks/next", dependencies=[Depends(verify_worker_token)])
async def next_task() -> Response:
    task = get_next_task()
    if task is None:
        return Response(status_code=204)
    return {"id": task["id"], "type": task["type"]}


@app.get("/api/tasks/{task_id}/input", dependencies=[Depends(verify_worker_token)])
async def get_input(task_id: str) -> Response:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    input_path = Path(task["input_path"])
    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Input file not found")
    return Response(content=input_path.read_bytes(), media_type="application/octet-stream")


@app.post("/api/tasks/{task_id}/result", dependencies=[Depends(verify_worker_token)])
async def upload_result(task_id: str, file: UploadFile = File(...)) -> dict:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    output_path = config.results_dir / f"{task_id}.png"
    output_path.write_bytes(await file.read())
    complete_task(task_id, str(output_path))
    return {"status": "done"}


@app.post("/api/tasks/{task_id}/error", dependencies=[Depends(verify_worker_token)])
async def report_error(task_id: str, error: str) -> dict:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    fail_task(task_id, error)
    return {"status": "error"}


# ---------------------------------------------------------------------------
# Test endpoints (этап 1)
# ---------------------------------------------------------------------------

@app.post("/api/test/rembg")
async def test_create_rembg(file: UploadFile = File(...)) -> dict:
    """Создаёт тестовую задачу rembg."""
    upload_path = config.uploads_dir / f"{uuid.uuid4()}{Path(file.filename or 'file').suffix}"
    upload_path.write_bytes(await file.read())
    task_id = create_task("rembg", str(upload_path))
    return {"task_id": task_id}


@app.get("/api/test/rembg/{task_id}")
async def test_get_rembg(task_id: str) -> Response:
    """Скачивает результат rembg задачи."""
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] == "pending" or task["status"] == "processing":
        return Response(content=task["status"], status_code=202)
    if task["status"] == "error":
        raise HTTPException(status_code=500, detail=task["error"])
    output_path = Path(task["output_path"])
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found")
    return Response(content=output_path.read_bytes(), media_type="image/png")


# ---------------------------------------------------------------------------
# Static files (подключим позже, когда будет фронтенд)
# ---------------------------------------------------------------------------

static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
