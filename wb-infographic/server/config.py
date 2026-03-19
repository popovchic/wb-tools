import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class Config:
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
    worker_token: str = os.getenv("WORKER_TOKEN", "")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    uploads_dir: Path = Path(__file__).parent.parent / "data" / "uploads"
    results_dir: Path = Path(__file__).parent.parent / "data" / "results"

    def __post_init__(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)


config = Config()
config.uploads_dir.mkdir(parents=True, exist_ok=True)
config.results_dir.mkdir(parents=True, exist_ok=True)
