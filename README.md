# AI-4GYM

Chatbot Gym tiếng Việt dùng **FastAPI, React/TypeScript, LangChain, Chroma và Ollama**. Hỗ trợ tra cứu kỹ thuật, gợi ý bài tập, lịch tập 1–6 buổi/tuần và hội thoại nhiều lượt. Tài khoản lưu lịch sử trong MySQL; khách chat không cần đăng nhập. Các mô hình AI chạy local.

## Bản nộp

Mã nguồn, dữ liệu và kiểm thử nằm trong `BE/`, `FE/`; báo cáo hoàn chỉnh nằm trong `reports/`.

| Tệp | Nội dung |
| --- | --- |
| [Tiểu luận PDF](reports/Tieu_luan_AI_4GYM_CT07PM.pdf) | Cơ sở lý thuyết, thiết kế, triển khai và đánh giá. |
| [Báo cáo kiểm thử PDF](reports/Bao_cao_kiem_thu_AI_4GYM.pdf) | Kết quả phần mềm, hồi quy và đánh giá chatbot. |
| [Bộ kiểm thử Excel](reports/Bo_kiem_thu_AI_4GYM.xlsx) | Ca phần mềm, trình duyệt, hồi quy, đánh giá AI và sheet `20 Ca Kiem Thu Mo Rong` đã gộp. |
| [Báo cáo train/test Excel](reports/AI-4GYM_train_test_report.xlsx) | 772 câu train, 193 câu test, phản hồi và điểm đánh giá. |

```text
AI-4GYM/
├── BE/
│   ├── app/                  # API, MySQL, RAG và xử lý dữ liệu
│   ├── data/                 # Excel gốc, train/test và bài tập biên soạn
│   ├── tests/                # Unit, HTTP, hồi quy và 20 ca mở rộng
│   ├── .env.example
│   └── requirements.txt
├── FE/                       # React/TypeScript, Vite
├── reports/                  # 2 PDF, 2 Excel và kết quả đánh giá train/test
└── README.md
```

## Cài đặt

Cần **Python 3.11+**, **Node.js 20.19+ hoặc 22.12+**, **MySQL** và **Ollama**. Các lệnh dưới đây dùng PowerShell, bắt đầu tại thư mục chứa `BE` và `FE`.

Bật MySQL (có thể dùng ServBay), mở Ollama và tải model:

```powershell
ollama pull qwen3:4b-instruct
ollama pull qwen3-embedding:0.6b
```

Tạo môi trường backend:

```powershell
Set-Location BE
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
```

Sửa thông tin MySQL trong `BE/.env`, đặc biệt `DATABASE_PASSWORD=change_me` thành mật khẩu thật. Tài khoản MySQL cần quyền tạo database và bảng. Cấu hình mặc định dùng MySQL tại `127.0.0.1:3306`, Ollama tại `127.0.0.1:11434`. Mẫu `.env.example` liệt kê đầy đủ tùy chọn.

Khởi tạo database và chỉ mục RAG, vẫn tại `BE/`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.init_db
.\.venv\Scripts\python.exe -m app.scripts.ingest
```

Cài frontend:

```powershell
Set-Location ..\FE
npm ci
```

## Chạy ứng dụng

Bật MySQL và Ollama. Mở hai cửa sổ PowerShell tại gốc dự án.

Backend:

```powershell
Set-Location BE
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
Set-Location FE
npm run dev
```

Mở **http://127.0.0.1:5173**. API: http://127.0.0.1:8000/docs; trạng thái: http://127.0.0.1:8000/health.

Để chạy giao diện qua backend, build tại `FE/` bằng `npm run build`, sau đó mở http://127.0.0.1:8000. Mỗi lần sửa frontend cần build lại. Không cần cài thư viện hoặc tạo lại chỉ mục mỗi lần khởi động.

## Dữ liệu và đánh giá

Excel gốc có **965 cặp hỏi đáp**, chia cố định thành **772 train/corpus (80%)** và **193 test (20%)**. Chroma chỉ lập chỉ mục train và **11 bài tập** biên soạn, tổng **783 tài liệu**. Đây là corpus truy xuất RAG; không fine-tune model. Câu hỏi trùng sau chuẩn hóa không nằm ở cả hai tập.

`reports/evaluation_results.jsonl` lưu 193 phản hồi và metadata để các lệnh đánh giá, xuất Excel và kiểm toán hoạt động. Hồ sơ bàn giao có điểm **132/56/5** theo mức **2/1/0**, gồm 154 dòng judge v2 và 39 dòng v3; nhãn tay 187 đạt/6 không đạt. Đây là kết quả đã lưu, chưa được chuyên gia độc lập xác minh. Các kết quả chức năng, trình duyệt và nhận xét AI được trình bày trong PDF/Excel.

Khi thay dữ liệu, sửa Excel gốc hoặc `BE/data/curated/exercises.json`, chạy lại `ingest` và khởi động lại backend. JSON trong `data/processed/` được sinh từ Excel. `ingest --export-only` chỉ xuất JSON, không cần model.

## Kiểm tra

Xác nhận ngày **28/11/2026**: **72 test chạy đạt**, một nhóm tích hợp tài khoản bị bỏ qua do thiếu dịch vụ; build frontend và kiểm toán dữ liệu/Excel từ ZIP giải nén đạt. PDF và workbook đã gộp được kiểm tra nội dung, số trang và dữ liệu.

Tại `BE/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m app.scripts.audit_report
```

Tại `FE/`:

```powershell
npm run build
```

Các ca tích hợp cần MySQL, Ollama và chỉ mục đã khởi tạo. Ca tài khoản tự bỏ qua khi thiếu dịch vụ; ca RAG nhiều lượt vẫn cần Ollama. Xem kết quả thực tế của runner để phân biệt pass, skip và lỗi môi trường.

Để xuất lại Excel từ kết quả đã lưu, chạy `python -m app.scripts.export_report` bằng Python trong `.venv` tại `BE/`. `python -m app.scripts.evaluate_chatbot --ids qa-20,qa-132` giới hạn đánh giá theo ID; chạy không có `--ids` sẽ xử lý cả tập test và chấm lại các dòng judge cũ.
