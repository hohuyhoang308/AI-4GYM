from urllib.request import urlopen
import json

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import engine
from app.services.index import indexed_count
from app.services.knowledge import load_exercises


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    ollama_running = False
    try:
        with urlopen(settings.ollama_base_url + "/api/tags", timeout=2) as response:
            installed = {item["name"] for item in json.load(response)["models"]}
            ollama_running = True
    except Exception:
        installed = set()
    try:
        count = indexed_count()
    except Exception:
        count = 0
    try:
        split = json.loads(settings.split_manifest_path.read_text(encoding="utf-8"))
        expected_documents = split["train_rows"] + len(load_exercises())
    except (OSError, ValueError, KeyError):
        split = None
        expected_documents = 0
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_running = True
    except SQLAlchemyError:
        database_running = False
    return {
        "status": "ready" if expected_documents and count == expected_documents and settings.chat_model in installed and settings.embed_model in installed else "setup_required",
        "ollama_running": ollama_running,
        "chat_model_ready": settings.chat_model in installed,
        "embed_model_ready": settings.embed_model in installed,
        "indexed_documents": count,
        "expected_documents": expected_documents,
        "dataset_split": split,
        "database_running": database_running,
    }
