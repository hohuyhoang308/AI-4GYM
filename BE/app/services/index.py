import hashlib
import json

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from app.core.config import settings
from app.services.dataset import export_qa_splits
from app.services.knowledge import build_documents, export_qa_json


def collection_name() -> str:
    model_hash = hashlib.sha256(settings.embed_model.encode()).hexdigest()[:8]
    return f"gym_knowledge_{model_hash}"


def vector_store() -> Chroma:
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(settings.chroma_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    return Chroma(
        client=client,
        collection_name=collection_name(),
        collection_metadata={"hnsw:space": "cosine"},
        embedding_function=OllamaEmbeddings(model=settings.embed_model, base_url=settings.ollama_base_url),
    )


def indexed_count() -> int:
    return vector_store()._collection.count()


def build_index(batch_size: int = 32) -> int:
    if batch_size < 1 or batch_size > 100:
        raise ValueError("batch_size phải từ 1 đến 100")
    all_rows = export_qa_json()
    split = export_qa_splits(all_rows)
    train_rows = json.loads(settings.train_json_path.read_text(encoding="utf-8"))
    documents = build_documents(train_rows)
    store = vector_store()
    expected_ids = {str(document.id) for document in documents}
    stored = store.get(include=["documents", "metadatas"])
    existing_documents = {
        doc_id: (content, metadata)
        for doc_id, content, metadata in zip(stored["ids"], stored["documents"], stored["metadatas"])
    }
    old_ids = set(existing_documents)
    stale_ids = list(old_ids - expected_ids)
    if stale_ids:
        store.delete(ids=stale_ids)
    changed_documents = [
        document for document in documents
        if existing_documents.get(str(document.id)) != (document.page_content, document.metadata)
    ]
    for start in range(0, len(changed_documents), batch_size):
        batch = changed_documents[start : start + batch_size]
        store.add_documents(batch, ids=[str(document.id) for document in batch])
        print(f"Updated {min(start + batch_size, len(changed_documents))}/{len(changed_documents)} documents", flush=True)
    print(f"Index synchronized: {len(documents)} documents; {len(changed_documents)} embedded, {len(stale_ids)} removed", flush=True)
    manifest = {"qa_rows": len(all_rows), "train_rows": split["train_rows"], "test_rows": split["test_rows"], "documents": len(documents), "embed_model": settings.embed_model}
    (settings.chroma_path / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(documents)
