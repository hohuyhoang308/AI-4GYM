import argparse

from app.services.index import build_index
from app.services.knowledge import export_qa_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Chuẩn hóa Excel và lập chỉ mục RAG local")
    parser.add_argument("--export-only", action="store_true", help="Chỉ tạo data/processed/qa.json, chưa cần Ollama")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    if args.export_only:
        print(f"Exported {len(export_qa_json())} QA pairs to data/processed/qa.json")
        return
    print(f"Indexed {build_index(args.batch_size)} documents")


if __name__ == "__main__":
    main()
