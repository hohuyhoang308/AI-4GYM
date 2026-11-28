# AI-4GYM

**Trợ lý tập luyện Gym bằng tiếng Việt, vận hành với mô hình AI tại máy cục bộ.**

AI-4GYM hỗ trợ người mới tìm hiểu bài tập, kỹ thuật thực hiện và xây dựng lịch tập. Hệ thống sử dụng Retrieval-Augmented Generation (RAG) để truy xuất tài liệu trước khi tạo phản hồi; tài khoản và lịch sử hội thoại được lưu trong MySQL.

## Chức năng

- Hỏi đáp về Gym/Fitness, kèm nguồn tài liệu được truy xuất.
- Duy trì ngữ cảnh hội thoại, mặc định sử dụng ba lượt hỏi–đáp gần nhất.
- Gợi ý bài tập và lịch tập từ 1 đến 6 buổi mỗi tuần theo dụng cụ, nhóm cơ và mục tiêu.
- Đăng ký, đăng nhập, xem lại, đổi tên và xoá hội thoại.
- Chat ở chế độ khách; cuộc trò chuyện không được lưu vào MySQL và mất khi tải lại trang.

## Công nghệ

| Thành phần | Công nghệ |
| --- | --- |
| Giao diện | React, TypeScript, Vite |
| Backend | Python, FastAPI, SQLAlchemy |
| Truy xuất tài liệu | LangChain, Chroma |
| Mô hình hội thoại | Ollama · `qwen3:4b-instruct` |
| Mô hình embedding | Ollama · `qwen3-embedding:0.6b` |
| Lưu trữ tài khoản và hội thoại | MySQL |

## Cấu trúc dự án

```text
AI-4GYM/
├── BE/
│   ├── app/
│   │   ├── api/          # API xác thực, hội thoại, chatbot và danh mục
│   │   ├── core/         # Cấu hình ứng dụng
│   │   ├── db/           # Mô hình và kết nối cơ sở dữ liệu
│   │   ├── services/     # RAG, xử lý hội thoại và lập lịch tập
│   │   └── scripts/      # Khởi tạo, xử lý dữ liệu và đánh giá
│   ├── data/             # Dữ liệu gốc, train/test và bài tập biên soạn
│   ├── tests/            # Kiểm thử chức năng, tích hợp và hồi quy
│   ├── .env.example
│   ├── requirements.txt
│   └── requirements-lock.txt
├── FE/
│   ├── src/              # Giao diện và HTTP client
│   ├── public/           # Tài nguyên tĩnh
│   └── package.json
├── reports/              # Báo cáo PDF, Excel, kết quả đánh giá
│   ├── results/          # Log kiểm thử và rà soát (minh chứng)
│   └── evidence/         # Ảnh giao diện, sơ đồ, môi trường
└── README.md
```

## Cài đặt

### Yêu cầu môi trường

- Python **3.11 trở lên** (đã kiểm thử đầy đủ trên Windows 11 + Python 3.14.7; bộ kiểm thử offline cũng chạy được trên Linux).
- Node.js **20.19+ thuộc nhánh 20**, hoặc **22.12 trở lên**, cùng npm.
- MySQL 8 đang hoạt động; có thể sử dụng MySQL trong ServBay.
- Ollama với hai mô hình được liệt kê bên dưới.

### Yêu cầu phần cứng (khuyến nghị)

| Thành phần | Tối thiểu | Khuyến nghị |
| --- | --- | --- |
| RAM | 8 GB | 16 GB |
| GPU | Không bắt buộc (chạy được bằng CPU) | GPU có ≥ 4 GB VRAM để giảm thời gian trả lời |
| Ổ đĩa trống | ~5 GB (hai mô hình ~3 GB, môi trường Python/Node, chỉ mục Chroma) | ≥ 10 GB |

Thời gian chờ dự kiến: trên máy thử không dùng GPU, mỗi câu hỏi qua RAG mất **trung bình khoảng 85 giây** (48–124 giây; xem [báo cáo kiểm thử](reports/Bao_cao_kiem_thu_AI_4GYM.pdf), mục 2.4). Lịch tập theo quy tắc và câu bị từ chối trả về gần như tức thì. Giao diện hiển thị số giây đã chờ và chỉ báo lỗi sau 5 phút.

Các lệnh dưới đây dùng **PowerShell trên Windows**, bắt đầu từ thư mục gốc dự án. Trên Linux/macOS, thay `.\.venv\Scripts\python.exe` bằng `.venv/bin/python` và `Copy-Item` bằng `cp`.

### 1. Chuẩn bị mô hình AI

Mở Ollama và tải mô hình:

```powershell
ollama pull qwen3:4b-instruct
ollama pull qwen3-embedding:0.6b
```

Ứng dụng kết nối Ollama tại `http://127.0.0.1:11434`. Quá trình tải mô hình cần Internet; khi trả lời, hệ thống sử dụng mô hình local và không yêu cầu khoá API AI.

### 2. Thiết lập backend

```powershell
Set-Location BE
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
```

`requirements-lock.txt` khóa đúng phiên bản mọi gói (sinh từ `requirements.txt`); nếu phiên bản Python của bạn chưa có bản dựng sẵn cho một gói trong đó, dùng `requirements.txt` thay thế.

Chỉnh `BE/.env` theo [tệp cấu hình mẫu](BE/.env.example). Điền đúng `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST` và `DATABASE_PORT` của MySQL trên máy. Giá trị `change_me` cần được thay bằng mật khẩu thực tế; tài khoản MySQL cần quyền tạo database và bảng.

Khi MySQL và Ollama đã hoạt động, chạy tại `BE/`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.init_db
.\.venv\Scripts\python.exe -m app.scripts.ingest
```

Hai lệnh tạo cơ sở dữ liệu và chỉ mục RAG. Chỉ cần thực hiện khi cài đặt lần đầu hoặc cập nhật dữ liệu. Với database đã tạo bằng phiên bản trước 28/11/2026, `init_db` (hoặc lần khởi động backend kế tiếp) tự nâng các cột thời gian lên `DATETIME(6)` để tin nhắn giữ đúng thứ tự; nên chạy lại `ingest` để cập nhật liên kết nguồn bài tập đã sửa.

### 3. Thiết lập frontend

```powershell
Set-Location ..\FE
npm ci
```

## Chạy ứng dụng

Bật MySQL và Ollama, sau đó mở hai cửa sổ PowerShell tại thư mục gốc dự án.

**Backend**

```powershell
Set-Location BE
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Frontend**

```powershell
Set-Location FE
npm run dev
```

| Địa chỉ | Chức năng |
| --- | --- |
| [127.0.0.1:5173](http://127.0.0.1:5173) | Giao diện ứng dụng |
| [127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Tài liệu và thử nghiệm API |
| [127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Trạng thái mô hình, chỉ mục và MySQL |

Để phục vụ giao diện qua backend, chạy `npm run build` tại `FE/`, rồi truy cập [127.0.0.1:8000](http://127.0.0.1:8000) khi backend đang hoạt động. Cần build lại sau mỗi lần thay đổi frontend.

### Chuẩn bị trước khi demo

1. Bật MySQL và Ollama, chạy `ollama run qwen3:4b-instruct "xin chào"` một lần để nạp sẵn mô hình vào bộ nhớ (lần gọi đầu tiên chậm hơn đáng kể).
2. Mở [127.0.0.1:8000/health](http://127.0.0.1:8000/health), kiểm tra `status` là `ready` và `database_running` là `true`.
3. Hỏi thử một câu lịch tập (trả lời ngay) và một câu RAG (chờ 1–2 phút) trước khi trình bày.
4. Chuẩn bị sẵn video quay màn hình làm phương án dự phòng nếu máy demo chậm.

## Dữ liệu và đánh giá

Dữ liệu gốc tại [BE/data/raw/data.xlsx](BE/data/raw/data.xlsx) gồm **965 cặp hỏi–đáp**, được chia cố định như sau:

| Tập dữ liệu | Số lượng | Vai trò |
| --- | ---: | --- |
| Train/corpus | 772 câu · 80% | Xây dựng kho truy xuất RAG |
| Test | 193 câu · 20% | Đánh giá độc lập với kho truy xuất |

Chroma lập chỉ mục 772 câu train và 11 bài tập biên soạn, tổng cộng **783 tài liệu**. Tập test không được đưa vào chỉ mục; các câu hỏi trùng sau chuẩn hoá được giữ trong cùng một tập. Thuật ngữ “train” ở đây chỉ corpus RAG, không phải huấn luyện lại trọng số mô hình.

[reports/evaluation_results.jsonl](reports/evaluation_results.jsonl) lưu phản hồi và metadata của 193 câu đánh giá, phục vụ kiểm toán và xuất Excel. Điểm AI và nhãn duyệt tay trong báo cáo là kết quả của bộ đánh giá đã lưu, chưa được chuyên gia độc lập xác minh.

Khi cập nhật dữ liệu, chỉnh Excel gốc hoặc `BE/data/curated/exercises.json`, chạy lại `ingest` và khởi động lại backend. Các tệp trong `BE/data/processed/` được sinh từ Excel, luôn ghi với xuống dòng CRLF; hash kiểm toán được chuẩn hóa xuống dòng nên `ingest --export-only` và `audit_report` cho cùng kết quả trên Windows, Linux và macOS.

## Kiểm thử

Chạy tại `BE/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m app.scripts.audit_report
```

Lệnh sau chạy cùng bộ kiểm thử và lưu minh chứng (nền tảng, Python, commit, kết quả từng ca) vào `reports/results/software_test_results_<ngày>.json`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.run_tests
```

Kiểm tra TypeScript và bản build tại `FE/`:

```powershell
npm run build
```

Bộ kiểm thử hiện có **85 phương thức**. Ba ca cần dịch vụ thật sẽ **tự bỏ qua (skip)** khi thiếu MySQL/Ollama/chỉ mục RAG, không báo lỗi: tích hợp tài khoản (`test_auth_flow`), hội thoại nhiều lượt với model thật (`test_multiturn_flow`) và đối chiếu nội dung chỉ mục (`test_dataset_split`).

| Lần chạy | Môi trường | Kết quả | Minh chứng |
| --- | --- | --- | --- |
| 25/11/2026 | Windows 11, Python 3.14.7, MySQL + Ollama | 53/53 đạt (bộ kiểm thử lúc đó) | `reports/results/software_test_results.json` |
| 28/11/2026 | Linux, Python 3.10, không có MySQL/Ollama | 82 đạt, 0 lỗi, 3 bỏ qua | `reports/results/software_test_results_20261128.json` |

Build frontend và kiểm toán dữ liệu/Excel (`audit_report`) đạt ở cả hai lần. Trước khi nộp, nên chạy lại `run_tests` trên máy có MySQL và Ollama để cả 85 ca đều được thực thi.

## Báo cáo

| Tài liệu | Nội dung |
| --- | --- |
| [Tiểu luận](reports/Tieu_luan_AI_4GYM_CT07PM.pdf) | Cơ sở lý thuyết, thiết kế, triển khai và đánh giá hệ thống |
| [Báo cáo kiểm thử](reports/Bao_cao_kiem_thu_AI_4GYM.pdf) | Kết quả kiểm thử phần mềm, hồi quy và nhận xét về chatbot |
| [Bộ kiểm thử](reports/Bo_kiem_thu_AI_4GYM.xlsx) | Ma trận ca kiểm thử, kết quả và 20 ca mở rộng |
| [Báo cáo train/test](reports/AI-4GYM_train_test_report.xlsx) | Danh sách dữ liệu, phản hồi và điểm đánh giá theo từng câu |
| [reports/results/](reports/results) | Log kiểm thử phần mềm, hồi quy trước/sau sửa, trình duyệt và rà soát chatbot (được trích dẫn trong hai báo cáo PDF) |
| [reports/evidence/](reports/evidence) | Ảnh giao diện, sơ đồ kiến trúc, môi trường chạy thử |
