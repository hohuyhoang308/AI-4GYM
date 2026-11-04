# Môi trường của lần đánh giá local

Ghi nhận ngày 04/11/2026 trên Windows, GPU **NVIDIA GeForce GTX 1650 4 GB**. Các câu đã có trong `evaluation_results.jsonl` được tạo bằng các model và mã xử lý dưới đây. Việc ghi hash giúp nhận biết khi người khác thay model hoặc thay luồng chatbot trước khi chạy lại.

| Thành phần | Phiên bản / định danh |
| --- | --- |
| Python | 3.14.7 |
| Node.js / npm | 23.11.1 / 10.9.2 |
| Ollama | 0.40.13 |
| FastAPI / LangChain | 0.162.0 / 1.4.7 |
| langchain-chroma / langchain-ollama | 1.1.0 / 1.1.0 |
| ChromaDB / openpyxl | 1.5.9 / 3.1.5 |
| SQLAlchemy / PyMySQL | 2.1.6 / 1.2.3 |
| Model trả lời và chấm | `qwen3:4b-instruct` — digest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0` |
| Model embedding | `qwen3-embedding:0.6b` — digest `ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d` |
| Excel gốc SHA-256 | `83251e1948d686a13019d71b0750f566914533240752ef5f7b3327036f3a5313` |

Git blob của các file quyết định hành vi đánh giá:

| File | Git blob |
| --- | --- |
| `BE/app/services/chat.py` | `1a58f541e3d86893dec4c8a8cf2803dfe7796f5a` |
| `BE/app/scripts/evaluate_chatbot.py` | `73ac8b582be5741ef2219c8f601858992650cc3d` |
| `BE/app/services/scope.py` | `62c6a87e7e2cda24fba4b943e69a27d859765bb2` |
| `BE/app/services/index.py` | `bf34d4bad098637388c29b3e1c67233b5c223a83` |
| `BE/app/services/plans.py` | `f08a1a0ddd878b2916ed99c78452185e6c8dcf10` |

`split_manifest.json` lưu seed 42 và hash Excel gốc. Mỗi kết quả trong JSONL lưu hash tập test, tên model và hash nguồn. **Tên model chưa thay thế được digest** nếu Ollama tải lại một bản model khác cùng tên; khi tái chạy, kiểm tra digest bằng `ollama list` hoặc API `/api/tags`. Báo cáo này mô tả môi trường của lần chạy, không cam kết kết quả giống từng chữ vì phần sinh văn bản có thể thay đổi theo môi trường và phiên bản runtime.
