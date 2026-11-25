# Cấu trúc dự án

| Thư mục | Trách nhiệm |
| --- | --- |
| `BE/app/api/` | HTTP API: đăng nhập, chat, hội thoại, danh mục và health. |
| `BE/app/core/`, `BE/app/db/` | Cấu hình, kết nối MySQL và model dữ liệu. |
| `BE/app/services/` | RAG, dữ liệu, phạm vi câu hỏi, ngữ cảnh và mẫu lịch tập. |
| `BE/app/scripts/` | Khởi tạo DB, ingest, đánh giá, kiểm toán và xuất kết quả. |
| `BE/tests/` | Unit test, HTTP integration và hồi quy lỗi. |
| `BE/data/raw/` | Excel dữ liệu đầu vào. |
| `BE/data/processed/` | Corpus/test JSON và manifest phép chia. |
| `BE/data/curated/` | Bài tập biên soạn, các tình huống đánh giá. |
| `FE/src/` | Giao diện React/TypeScript, thành phần và HTTP client. |
| `docs/` | Tài liệu cài đặt và sơ đồ tổ chức repository. |
| `reports/` | Word/PDF/Excel hoàn chỉnh, danh mục hồ sơ. |
| `reports/results/` | Bằng chứng thực thi mới, log kiểm thử và nhận xét AI. |
| `reports/evidence/` | Ảnh giao diện, sơ đồ, biểu đồ, môi trường. |
| `reports/history/` | Hồ sơ kỹ thuật cũ, ghi rõ ngày và giới hạn. |
| `reports/tools/` | Công cụ tạo, hoàn thiện và đóng gói báo cáo. |
| `reports/releases/` | ZIP hồ sơ nộp đầy đủ, quản lý trên Git để tải trọn bộ. |

## Những gì không đưa lên Git

- `BE/.env`, `FE/.env.local`: cấu hình riêng; dùng `.env.example` làm mẫu.
- `BE/.venv/`, `FE/node_modules/`: thư viện cài trên từng máy.
- `BE/data/index/chroma/`: chỉ mục RAG tạo từ dữ liệu; không xóa lúc dọn vì đang dùng.
- `FE/dist/`: bản build để backend phục vụ web, có thể tạo lại.
- `__pycache__/`, `*.pyc`, `*.log`, `*.tsbuildinfo`, file khóa Office: cache/nhật ký local.
- `.local/`: bản sao Word gốc và ảnh xem thử tài liệu, không dùng làm mã nguồn.

Không chuyển `BE/` hoặc `FE/` để giữ nguyên import Python, lệnh npm và cách backend tìm frontend. Hai tệp train/test tại gốc `reports/` được giữ nguyên vị trí vì các lệnh audit/export/evaluate đang dùng chúng. Kết quả kiểm thử mới được tách riêng, không trộn vào 193 bản ghi đánh giá bàn giao.

Tài liệu khởi chạy: [setup.md](setup.md). Hồ sơ nộp: [reports/README.md](../reports/README.md).
