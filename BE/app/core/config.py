from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import os

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    chat_model: str = os.getenv("CHAT_MODEL", "qwen3:4b-instruct")
    embed_model: str = os.getenv("EMBED_MODEL", "qwen3-embedding:0.6b")
    chat_context_turns: int = int(os.getenv("CHAT_CONTEXT_TURNS", "3"))
    database_host: str = os.getenv("DATABASE_HOST", "127.0.0.1")
    database_port: int = int(os.getenv("DATABASE_PORT", "3306"))
    database_name: str = os.getenv("DATABASE_NAME", "ai_4gym")
    database_user: str = os.getenv("DATABASE_USER", "root")
    database_password: str = os.getenv("DATABASE_PASSWORD", "")
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "false").strip().lower() == "true"
    excel_path: Path = ROOT / "data" / "raw" / "data.xlsx"
    qa_json_path: Path = ROOT / "data" / "processed" / "qa.json"
    train_json_path: Path = ROOT / "data" / "processed" / "train.json"
    test_json_path: Path = ROOT / "data" / "processed" / "test.json"
    split_manifest_path: Path = ROOT / "data" / "processed" / "split_manifest.json"
    exercise_path: Path = ROOT / "data" / "curated" / "exercises.json"
    chroma_path: Path = ROOT / "data" / "index" / "chroma"

    def __post_init__(self) -> None:
        parsed = urlparse(self.ollama_base_url)
        if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("OLLAMA_BASE_URL phải trỏ tới Ollama trên máy local qua HTTP")
        if self.chat_model.endswith(":cloud") or self.embed_model.endswith(":cloud"):
            raise ValueError("Không hỗ trợ model Ollama cloud")
        if not 1 <= self.chat_context_turns <= 10:
            raise ValueError("CHAT_CONTEXT_TURNS phải nằm trong khoảng 1 đến 10")


settings = Settings()
