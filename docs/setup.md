# Cài đặt và chạy AI-4GYM từ A đến Z (Windows)

Hướng dẫn này dành cho máy Windows dùng PowerShell, ServBay/MySQL và Ollama local. Không cần khóa API AI. Làm lần lượt từ bước 1 đến bước 8; những lần sau chỉ cần xem bước 9. Số liệu được đối chiếu với dữ liệu và mã nguồn ngày 25/11/2026.

## 1. Cài phần mềm cần thiết

| Phần mềm | Dùng để làm gì | Cách kiểm tra |
| --- | --- | --- |
| [Python](https://www.python.org/downloads/windows/) 3.11 trở lên | Chạy backend FastAPI và LangChain | `python --version` |
| [Node.js](https://nodejs.org/en/download) nhánh 20 từ 20.19, hoặc phiên bản từ 22.12 trở lên, và npm | Chạy, build frontend React | `node --version`, `npm --version` |
| [Ollama](https://ollama.com/download/windows) | Chạy model chat và embedding trên máy | `ollama --version` |
| ServBay hoặc MySQL local đang chạy | Lưu tài khoản và lịch sử chat | `Test-NetConnection 127.0.0.1 -Port 3306` |
| Git (tùy chọn) | Tải/cập nhật mã nguồn | `git --version` |

Sau khi cài Python, Node.js hoặc Ollama, mở **cửa sổ PowerShell mới** để cập nhật `PATH`. Khi cài Python, chọn tùy chọn thêm Python vào `PATH` nếu trình cài đặt có hỏi. Môi trường đã lưu trong [environment.json](../reports/evidence/environment.json) ghi Python 3.14.7; yêu cầu Node.js ở bảng trên khớp trường `engines` của các gói Vite trong `FE/package-lock.json`.

## 2. Mở dự án

Với thư mục của bản đang làm việc:

```powershell
Set-Location 'D:\AI-4GYM-main\AI-4GYM-main'
```

Nếu tải từ GitHub trên máy khác:

```powershell
git clone https://github.com/hohuyhoang308/AI-4GYM.git
Set-Location AI-4GYM
```

Kiểm tra có hai thư mục `BE` và `FE`:

```powershell
Get-ChildItem -Name
```

> Nếu đặt dự án ở vị trí khác, thay đường dẫn trên bằng thư mục chứa `BE`, `FE`, `docs` và `reports`. Các lệnh tiếp theo chạy từ thư mục đó, trừ khi có dòng `Set-Location` khác.

## 3. Bật MySQL trong ServBay

1. Mở ServBay và khởi động dịch vụ **MySQL**; cũng có thể dùng MySQL local đã cài riêng.
2. Kiểm tra MySQL nghe cổng `3306`:

```powershell
Test-NetConnection 127.0.0.1 -Port 3306
```

`TcpTestSucceeded` cần là `True`. Dùng đúng tài khoản, mật khẩu và cổng của MySQL trên máy bạn để điền vào `BE/.env` ở bước 5. Tài khoản này cần quyền tạo database và bảng. **Không cần tạo database bằng tay**: lệnh `init_db` sẽ tạo `ai_4gym` và các bảng.

## 4. Bật Ollama và tải model local

Mở ứng dụng Ollama cho Windows. Nếu Ollama chưa chạy dưới nền, mở cửa sổ PowerShell riêng và chạy `ollama serve`. Sau đó tải hai model:

```powershell
ollama pull qwen3:4b-instruct
ollama pull qwen3-embedding:0.6b
ollama list
```

`qwen3:4b-instruct` dùng để trả lời; `qwen3-embedding:0.6b` dùng để lập chỉ mục và tìm tài liệu. Lần đầu `pull` phải có Internet và có thể mất vài phút. Khi dùng chatbot, cả hai model chạy qua Ollama tại `127.0.0.1:11434`, không gọi API AI bên ngoài. Tránh chọn biến thể model có hậu tố `:cloud`.

Kiểm tra Ollama đang hoạt động:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

## 5. Tạo môi trường Python và cấu hình backend

Từ thư mục gốc:

```powershell
Set-Location BE
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
notepad .env
```

Trong file `.env`, thay `DATABASE_PASSWORD=change_me` bằng mật khẩu MySQL thật; sửa `DATABASE_USER`, host và port nếu cần. Ví dụ cấu hình local theo tệp mẫu:

```dotenv
OLLAMA_BASE_URL=http://127.0.0.1:11434
CHAT_MODEL=qwen3:4b-instruct
EMBED_MODEL=qwen3-embedding:0.6b
CHAT_CONTEXT_TURNS=3
DATABASE_HOST=127.0.0.1
DATABASE_PORT=3306
DATABASE_NAME=ai_4gym
DATABASE_USER=root
DATABASE_PASSWORD=change_me
COOKIE_SECURE=false
```

`change_me` là giá trị cần thay, không phải mật khẩu mặc định của MySQL. `COOKIE_SECURE=false` dùng khi chạy HTTP ở `127.0.0.1`; nếu phục vụ qua HTTPS, đổi thành `true`. File `.env` và thư mục `.venv` được Git bỏ qua. Ollama chỉ được cấu hình bằng HTTP tới `localhost`, `127.0.0.1` hoặc `::1`; ứng dụng từ chối model có hậu tố `:cloud`.

## 6. Tạo database và chỉ mục RAG

Vẫn trong `BE/`, khi MySQL và Ollama đều đã chạy:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.init_db
.\.venv\Scripts\python.exe -m app.scripts.ingest
```

`init_db` tạo database `ai_4gym` và năm bảng chính: `users`, `login_sessions`, `conversations`, `chat_messages`, `chat_request_records`. Bảng cuối hỗ trợ tránh lưu lặp khi gửi lại `request_id`. `ingest` đọc `data/raw/data.xlsx`, chuyển **965 cặp hỏi đáp** sang `data/processed/qa.json`, rồi chia thành `train.json` (**772 câu, 80%**) và `test.json` (**193 câu, 20%**). Chroma chỉ lập chỉ mục 772 câu train và **11 bài tập** trong `data/curated/exercises.json`, tổng cộng **783 tài liệu**. Tập test không nằm trong chỉ mục. Lần đầu có thể mất vài phút vì phải tạo embedding local.

Nếu chỉ muốn xem JSON mà chưa tải model, dùng:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.ingest --export-only
```

Lệnh `--export-only` cũng tạo lại `train.json`, `test.json` và `split_manifest.json` mà chưa cần Ollama. Cách chia cố định bằng seed `42` và giữ các câu hỏi trùng sau chuẩn hóa trong cùng một tập, giúp chạy lại ra cùng kết quả. Sau khi sửa Excel hoặc `exercises.json`, chạy lại `ingest` đầy đủ rồi khởi động lại backend để cập nhật dữ liệu truy xuất. **Không chỉnh các file JSON rồi chạy `ingest`** vì lệnh này sẽ tạo lại chúng từ Excel.

### Xuất báo cáo train/test ra Excel

Sau khi `ingest` đầy đủ đã tạo chỉ mục Chroma, vẫn trong `BE/`, chạy:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.export_report
```

File được tạo tại `../reports/AI-4GYM_train_test_report.xlsx`. Báo cáo gồm 4 sheet: `Tong quan` (số liệu 80/20, kết quả đánh giá, kiểm tra dữ liệu), `Train 80` (772 câu), `Test 20` (193 câu) và `Danh gia Test` (câu trả lời chatbot và điểm trên từng câu). Để **chạy chatbot thật trên toàn bộ 193 câu test và chấm tự động bằng Qwen local**, dùng:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.evaluate_chatbot
```

Mỗi câu test được hỏi như một phiên chat mới, không lấy lịch sử từ câu trước. Script ghi từng kết quả vào `../reports/evaluation_results.jsonl`; nếu dừng, chạy lại để hoàn thành câu chưa chấm theo phiên bản judge hiện tại. **Hiện cả 193 câu đã có điểm; chạy lại toàn bộ sẽ chấm lại các dòng judge v2 bằng v3, làm thay đổi thống kê.** Dùng `--ids qa-20,qa-132` để giới hạn câu cần xem. Khi hoàn tất, Excel được cập nhật. Điểm AI: `2` = đạt đủ ý chính, `1` = đúng một phần, `0` = sai hoặc từ chối. Cột `Duyệt tay (1/0)` ở sheet `Danh gia Test` dành cho người kiểm tra độc lập; nhập `1` hoặc `0`, tỷ lệ duyệt tay sẽ tự tính ở `Tong quan` khi mở bằng Excel. Token F1 và ROUGE-L F1 là chỉ số trùng từ, không phải tỷ lệ đúng. Điểm AI do chính model Qwen chấm nên cần xem lại trước khi dùng làm kết luận học thuật. Nếu thay dữ liệu test hoặc model, lưu trữ kết quả cũ rồi đánh giá lại từ đầu để tránh trộn kết quả.

## 7. Chạy backend

Trong cửa sổ PowerShell đang ở `BE/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Giữ cửa sổ này mở. Kiểm tra:

- [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health): khi sẵn sàng, `status` là `ready`, `database_running` là `true`, `indexed_documents` và `expected_documents` đều là `783`; `dataset_split` hiển thị số câu và tỷ lệ. Kiểm tra riêng `database_running`: trường `status` chỉ xét model/chỉ mục, nên vẫn có thể là `ready` khi MySQL chưa hoạt động.
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs): tài liệu và giao diện thử API.

## 8. Cài và chạy frontend

Mở **PowerShell thứ hai** tại thư mục gốc `AI-4GYM`:

```powershell
Set-Location FE
npm ci
npm run dev
```

Mở [http://127.0.0.1:5173](http://127.0.0.1:5173). Vite tự chuyển `/api` sang backend cổng 8000. Thử hỏi “Gợi ý lịch tập 3 buổi/tuần” khi chưa đăng nhập. F5 sẽ xóa cuộc chat khách. Sau đó đăng ký tài khoản, gửi câu hỏi và F5: hội thoại phải xuất hiện lại từ MySQL.

### Ngữ cảnh hội thoại

Mỗi câu hỏi mới lấy tối đa **3 lượt hỏi–đáp trước đó** (6 tin nhắn) trong cùng cuộc trò chuyện. LangChain gửi các tin này theo đúng vai trò người dùng/trợ lý cho model. Với câu hỏi nối tiếp, backend dùng các lượt gần đây để truy xuất RAG; nếu người dùng nói “bài đầu tiên” hoặc “bài đó”, backend xác định bài tập được nhắc tới trước khi tìm tài liệu. Lịch sử cũ vẫn hiển thị đầy đủ cho tài khoản, nhưng model chỉ nhận 3 lượt gần nhất để giữ ngữ cảnh gọn.

Khách giữ ngữ cảnh tạm trong RAM của backend bằng `session_id`, tối đa khoảng 1 giờ không hoạt động; F5 làm trang quên `session_id` nên bắt đầu cuộc chat mới. Tài khoản lấy 3 lượt gần nhất từ MySQL, kể cả sau khi khởi động lại backend. Có thể đổi số lượt bằng `CHAT_CONTEXT_TURNS` trong `BE/.env` (1–10), sau đó khởi động lại backend.

## 9. Những lần chạy tiếp theo

Mỗi lần sử dụng đầy đủ tài khoản và chat, bật **MySQL trong ServBay** và **Ollama** trước. Sau đó mở hai PowerShell:

```powershell
# Cửa sổ 1, tại AI-4GYM/BE
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

```powershell
# Cửa sổ 2, tại AI-4GYM/FE
npm run dev
```

Không cần chạy lại `pip install`, `npm install`, `ollama pull` hoặc `ingest` mỗi lần, trừ khi đổi dependency, model hoặc dữ liệu.

### Chạy bằng một cổng (bản build)

Tại `FE/`, chạy `npm run build`. Sau đó chỉ cần backend đang chạy; mở [http://127.0.0.1:8000](http://127.0.0.1:8000). Backend sẽ phục vụ các file trong `FE/dist`. Sau mỗi lần sửa frontend, build lại để thấy thay đổi tại cổng 8000. Khi phát triển, dùng Vite ở cổng 5173 sẽ tiện hơn.

## 10. Kiểm tra và xử lý lỗi thường gặp

### Số liệu train/test để báo cáo

Từ 965 cặp hỏi đáp: **772 câu (80%)** dùng làm corpus RAG, **193 câu (20%)** được giữ riêng để đánh giá. Có **11 bài tập** bổ sung ngoài phép chia, được đưa vào chỉ mục. Đây không phải huấn luyện lại trọng số Ollama/Qwen. Hồ sơ bàn giao hiện đủ **193/193 điểm**, phân bố **132/56/5** theo mức **2/1/0**, gồm 154 dòng judge v2 và 39 dòng v3. Excel có **187 nhãn tay đạt/6 không đạt**, chưa có xác minh chuyên gia độc lập. Xem [hồ sơ nộp](../reports/HO_SO_NOP.md) để phân biệt bộ 193 câu cũ với các tình huống hỏi mới sau sửa lỗi.

Tại `BE/`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.audit_report
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Lệnh `audit_report` kiểm tra Excel gốc, JSON, train/test và báo cáo mà không cần MySQL/Ollama, nhưng vẫn cần cài dependency backend. `evaluation_complete: true` nghĩa là đủ điểm cho tập test; `report_synced: false` nghĩa là số kết quả Excel chưa đồng bộ JSONL. Ca tài khoản trong `test_auth_flow.py` tự bỏ qua nếu thiếu dịch vụ. Một số ca khác, như `test_multiturn_flow.py`, tạo `ChatService` thật nên vẫn cần Ollama và chỉ mục; không coi một lần chạy thiếu dịch vụ hoặc có skip là toàn bộ kiểm thử đã đạt.

Tại `FE/`:

```powershell
npm run build
```

| Triệu chứng | Cách xử lý |
| --- | --- |
| `python` không nhận | Mở PowerShell mới; thử `py -m venv .venv`; kiểm tra Python đã được thêm vào `PATH`. |
| Không chạy được `Activate.ps1` | Không cần kích hoạt venv; dùng trực tiếp `.\.venv\Scripts\python.exe` như hướng dẫn. |
| `Access denied for user 'root'` | Kiểm tra `DATABASE_USER`/`DATABASE_PASSWORD` trong `BE/.env` và mật khẩu MySQL thực tế. |
| Không kết nối được MySQL | Bật MySQL; kiểm tra cổng bằng `Test-NetConnection 127.0.0.1 -Port 3306`; sửa `DATABASE_PORT` nếu dùng cổng khác. |
| `/health` báo thiếu Ollama/model | Mở Ollama, chạy `ollama list`, tải model thiếu bằng `ollama pull ...`. |
| `/health` có `indexed_documents: 0` | Chạy lại `python -m app.scripts.ingest` từ `BE/`. |
| Frontend báo không kết nối | Kiểm tra backend ở cổng 8000, frontend ở 5173; xem `/health`. |
| Cổng 8000 hoặc 5173 đã được dùng | Dừng tiến trình cũ đang dùng cổng; Vite đang cấu hình cổng 5173 cố định. |
| Model trả lời chậm | Ollama có thể đang chạy bằng CPU hoặc model chưa nạp xong; đợi câu hỏi đầu tiên. |

## 11. Dữ liệu local và phạm vi

- `BE/.env`, `BE/.venv`, `BE/data/index/chroma`, `FE/node_modules` và `FE/dist` không được đưa lên Git.
- Mật khẩu tài khoản được băm; cookie phiên đăng nhập đặt cờ `HttpOnly`, và lịch sử tài khoản nằm trong MySQL local.
- Khách không ghi lịch sử vào MySQL; hội thoại khách trong trình duyệt mất khi tải lại trang. Backend có thể giữ ngữ cảnh khách tạm trong RAM khi phiên chat đang mở.
- Kho Excel hiện có cột `Source`; nguồn được giữ trong JSON và metadata truy xuất. Liên kết giúp truy vết, chưa chứng minh nội dung đã được chuyên gia thẩm định. Chatbot không thay thế tư vấn chuyên môn khi có chấn thương hoặc bệnh lý.
