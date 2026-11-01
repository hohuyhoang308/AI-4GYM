# Cài đặt và chạy AI-4GYM từ A đến Z (Windows)

Hướng dẫn này dành cho máy Windows dùng PowerShell, Serbay/MySQL và Ollama local. Không cần khóa API AI. Làm lần lượt từ bước 1 đến bước 8; những lần sau chỉ cần xem bước 9.

## 1. Cài phần mềm cần thiết

| Phần mềm | Dùng để làm gì | Cách kiểm tra |
| --- | --- | --- |
| [Python](https://www.python.org/downloads/windows/) 3.11 trở lên | Chạy backend FastAPI và LangChain | `python --version` |
| [Node.js](https://nodejs.org/en/download) tương thích Vite (20.19+ hoặc 22.12+) và npm | Chạy, build frontend React | `node --version`, `npm --version` |
| [Ollama](https://ollama.com/download/windows) | Chạy model chat và embedding trên máy | `ollama --version` |
| Serbay với MySQL đang chạy | Lưu tài khoản và lịch sử chat | `Test-NetConnection 127.0.0.1 -Port 3306` |
| Git (tùy chọn) | Tải/cập nhật mã nguồn | `git --version` |

Sau khi cài Python, Node.js hoặc Ollama, mở **cửa sổ PowerShell mới** để cập nhật `PATH`. Khi cài Python, chọn tùy chọn thêm Python vào `PATH` nếu trình cài đặt có hỏi. Dự án đã chạy thử với Python 3.14.7 và Node.js 23.11.1 trên máy phát triển.

## 2. Mở dự án

Nếu đã có thư mục trên Desktop như máy hiện tại:

```powershell
Set-Location 'C:\Users\xnovh\Desktop\AI-4GYM'
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

> Các lệnh ở các bước tiếp theo giả định bạn đang ở thư mục gốc `AI-4GYM`, trừ khi có dòng `Set-Location` khác.

## 3. Bật MySQL trong Serbay

1. Mở Serbay và khởi động dịch vụ **MySQL**.
2. Kiểm tra MySQL nghe cổng `3306`:

```powershell
Test-NetConnection 127.0.0.1 -Port 3306
```

`TcpTestSucceeded` cần là `True`. Trên máy của dự án, tài khoản MySQL là `root`, mật khẩu là `root`. Nếu bạn đã đổi mật khẩu/cổng trong Serbay, ghi nhớ để điền vào `BE/.env` ở bước 5. **Không cần tạo database bằng tay**: lệnh `init_db` sẽ tạo `ai_4gym` và các bảng.

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
Copy-Item .env.example .env
notepad .env
```

Trong file `.env`, đổi `DATABASE_PASSWORD=change_me` thành `DATABASE_PASSWORD=root` nếu Serbay dùng `root/root`. Các giá trị mặc định khác:

```dotenv
OLLAMA_BASE_URL=http://127.0.0.1:11434
CHAT_MODEL=qwen3:4b-instruct
EMBED_MODEL=qwen3-embedding:0.6b
DATABASE_HOST=127.0.0.1
DATABASE_PORT=3306
DATABASE_NAME=ai_4gym
DATABASE_USER=root
DATABASE_PASSWORD=root
COOKIE_SECURE=false
```

Đây chỉ là ví dụ cho **máy local**. Nếu mật khẩu/port khác, sửa theo Serbay của bạn. `COOKIE_SECURE=false` phù hợp khi chạy HTTP ở `127.0.0.1`; nếu sau này phục vụ qua HTTPS, đổi thành `true`. File `.env` và thư mục `.venv` được Git bỏ qua.

## 6. Tạo database và chỉ mục RAG

Vẫn trong `BE/`, khi MySQL và Ollama đều đã chạy:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.init_db
.\.venv\Scripts\python.exe -m app.scripts.ingest
```

`init_db` tạo database `ai_4gym` và bảng tài khoản, phiên đăng nhập, hội thoại, tin nhắn. `ingest` đọc `data/raw/data.xlsx`, chuyển **toàn bộ 965 cặp hỏi đáp** sang `data/processed/qa.json`, thêm 10 bài tập trong `data/curated/exercises.json` và lập chỉ mục Chroma tại `data/index/chroma/` (975 tài liệu). Lần đầu có thể mất vài phút vì phải tạo embedding local.

Nếu chỉ muốn xem JSON mà chưa tải model, dùng:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.ingest --export-only
```

Sau khi sửa Excel hoặc `exercises.json`, chạy lại `ingest` đầy đủ rồi khởi động lại backend để cập nhật dữ liệu truy xuất. **Không chỉnh `qa.json` rồi chạy `ingest`** vì lệnh này sẽ tạo lại JSON từ Excel.

## 7. Chạy backend

Trong cửa sổ PowerShell đang ở `BE/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Giữ cửa sổ này mở. Kiểm tra:

- [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health): `status` là `ready`, `database_running` là `true`, `indexed_documents` là `975`.
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs): tài liệu và giao diện thử API.

## 8. Cài và chạy frontend

Mở **PowerShell thứ hai** tại thư mục gốc `AI-4GYM`:

```powershell
Set-Location FE
npm install
npm run dev
```

Mở [http://127.0.0.1:5173](http://127.0.0.1:5173). Vite tự chuyển `/api` sang backend cổng 8000. Thử hỏi “Gợi ý lịch tập 3 buổi/tuần” khi chưa đăng nhập. F5 sẽ xóa cuộc chat khách. Sau đó đăng ký tài khoản, gửi câu hỏi và F5: hội thoại phải xuất hiện lại từ MySQL.

## 9. Những lần chạy tiếp theo

Mỗi lần sử dụng, bật **MySQL trong Serbay** và **Ollama** trước. Sau đó mở hai PowerShell:

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

Tại `BE/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tại `FE/`:

```powershell
npm run build
```

| Triệu chứng | Cách xử lý |
| --- | --- |
| `python` không nhận | Mở PowerShell mới; thử `py -m venv .venv`; kiểm tra Python đã được thêm vào `PATH`. |
| Không chạy được `Activate.ps1` | Không cần kích hoạt venv; dùng trực tiếp `.\.venv\Scripts\python.exe` như hướng dẫn. |
| `Access denied for user 'root'` | Kiểm tra `DATABASE_USER`/`DATABASE_PASSWORD` trong `BE/.env` và mật khẩu thực tế của Serbay. |
| Không kết nối được MySQL | Bật MySQL trong Serbay; kiểm tra cổng bằng `Test-NetConnection 127.0.0.1 -Port 3306`; sửa `DATABASE_PORT` nếu Serbay dùng cổng khác. |
| `/health` báo thiếu Ollama/model | Mở Ollama, chạy `ollama list`, tải model thiếu bằng `ollama pull ...`. |
| `/health` có `indexed_documents: 0` | Chạy lại `python -m app.scripts.ingest` từ `BE/`. |
| Frontend báo không kết nối | Kiểm tra backend ở cổng 8000, frontend ở 5173; xem `/health`. |
| Cổng 8000 hoặc 5173 đã được dùng | Dừng tiến trình cũ đang dùng cổng; Vite đang cấu hình cổng 5173 cố định. |
| Model trả lời chậm | Ollama có thể đang chạy bằng CPU hoặc model chưa nạp xong; đợi câu hỏi đầu tiên. |

## 11. Dữ liệu local và phạm vi

- `BE/.env`, `BE/.venv`, `BE/data/index/chroma`, `FE/node_modules` và `FE/dist` không được đưa lên Git.
- Mật khẩu tài khoản được băm; cookie phiên đăng nhập đặt cờ `HttpOnly`, và lịch sử tài khoản nằm trong MySQL local.
- Khách không ghi lịch sử vào MySQL; hội thoại khách trong trình duyệt mất khi tải lại trang. Backend có thể giữ ngữ cảnh khách tạm trong RAM khi phiên chat đang mở.
- Kho Excel không có cột nguồn cho từng câu hỏi; câu trả lời nên được kiểm tra trước khi áp dụng vào tập luyện thực tế. Chatbot không thay thế tư vấn chuyên môn khi có chấn thương hoặc bệnh lý.
