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
| `docs/` | Hướng dẫn cài đặt, tổ chức repository và biên bản rà soát báo cáo/docs. |
| `reports/` | Word/PDF/Excel hoàn chỉnh, danh mục hồ sơ. |
| `reports/results/` | Bằng chứng thực thi mới, log kiểm thử và nhận xét AI. |
| `reports/evidence/` | Ảnh giao diện, sơ đồ, biểu đồ, môi trường. |
| `reports/history/` | Hồ sơ kỹ thuật cũ, ghi rõ ngày và giới hạn. |
| `reports/tools/` | Công cụ tạo, hoàn thiện và đóng gói báo cáo. |
| `reports/releases/` | ZIP hồ sơ nộp đầy đủ, quản lý trên Git để tải trọn bộ. |

## Những gì không đưa lên Git

- `BE/.env`, `FE/.env.local`: cấu hình riêng; backend dùng `BE/.env.example` làm mẫu. Frontend hiện dùng địa chỉ API theo chế độ dev/build trong `FE/src/lib/api.ts`, chưa đọc `.env.local` để đổi backend.
- `BE/.venv/`, `FE/node_modules/`: thư viện cài trên từng máy.
- `BE/data/index/chroma/`: chỉ mục RAG tạo từ dữ liệu; không xóa lúc dọn vì đang dùng.
- `FE/dist/`: bản build để backend phục vụ web, có thể tạo lại.
- `__pycache__/`, `*.pyc`, `*.log`, `*.tsbuildinfo`, file khóa Office: cache/nhật ký local.
- `.local/`: nơi dành cho bản sao và ảnh xem thử local; không phải hiện vật bắt buộc có sẵn sau khi clone.

Không chuyển `BE/` hoặc `FE/` để giữ nguyên import Python, lệnh npm và cách backend tìm frontend. Hai tập dữ liệu nằm tại `BE/data/processed/train.json` và `test.json`. Hai hiện vật tại gốc `reports/` là `evaluation_results.jsonl` và `AI-4GYM_train_test_report.xlsx`; giữ vị trí vì audit/export/evaluate đang dùng chúng. Kết quả kiểm thử mới nằm riêng trong `reports/results/`, không trộn vào 193 bản ghi bàn giao.

## Chỉnh sửa và đóng gói tài liệu

Word/PDF hiện hành được chỉnh trực tiếp từ bản tiểu luận của nhóm; cập nhật mục lục và xuất PDF cùng lần lưu. `reports/tools/build_submission.py` là công cụ tạo lại toàn bộ Word/Excel theo cấu trúc riêng của script, nên không dùng để cập nhật bản Word đã chỉnh theo form trường. `finalize_word.ps1` cập nhật trường Word và PDF; cần Microsoft Word trên Windows. `package_submission.py` kiểm tra hiện vật, cập nhật manifest và ZIP, không chạy lại kiểm thử phần mềm.

Từ gốc dự án, khi đã có Python trong `BE/.venv` và thư viện báo cáo:

```powershell
.\BE\.venv\Scripts\python.exe -m pip install -r reports/requirements-report.txt
.\BE\.venv\Scripts\python.exe reports/tools/package_submission.py
```

Gói ZIP là hồ sơ báo cáo kèm bằng chứng và mã kiểm thử được tham chiếu, không phải toàn bộ ứng dụng có thể chạy sau khi giải nén. Mã nguồn đầy đủ lấy từ repository; môi trường và chỉ mục được tạo theo hướng dẫn cài đặt.

Tài liệu khởi chạy: [setup.md](setup.md). Hồ sơ nộp: [reports/README.md](../reports/README.md). Phạm vi và kết quả rà soát: [report-review.md](report-review.md).
