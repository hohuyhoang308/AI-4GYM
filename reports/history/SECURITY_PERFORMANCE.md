# Bàn giao kỹ thuật 2 — Security, Evaluation & Performance

Kiểm tra ngày 12/11/2026. Bằng chứng: `security_performance.json/.xlsx`, `performance_local.json/.xlsx`, `../evaluation_results.jsonl` và `../AI-4GYM_train_test_report.xlsx`. Đây là phép đo local trên máy hiện tại, không phải tỷ lệ an toàn hay hiệu năng trên mọi máy.

## Prompt injection và giới hạn nhiệm vụ

`BE/data/curated/security_cases.json` có 7 ca: câu ngoài phạm vi, xin system prompt, đổi vai, giả `[SYSTEM]`, tấn công sau lượt chat, hỏi nối tiếp hợp lệ, lệnh tiếng Anh. Tổng cộng 9 request vì 2 ca nhiều lượt. Lần chạy đầu trước sửa: **3/6 ca đạt**; model đã in `INJECTED_OK` trong 2 ca và trả lời lệch mẫu từ chối trong 1 ca. Sau khi thêm bộ chặn các mẫu tấn công rõ ràng trước RAG/model và củng cố system prompt, lần chạy cuối **7/7 ca đạt**. File JSON/XLSX lưu câu hỏi, câu trả lời, pass/fail và thời gian từng request.

Bộ chặn dùng biểu thức chính quy; kết quả này không chứng minh chống được mọi biến thể prompt injection. Cần tiếp tục thử dữ liệu RAG độc hại, các cách diễn đạt khác và nhiều ngôn ngữ.

## Session và replay

| Tình huống | Hành vi và kiểm chứng |
| --- | --- |
| Đăng nhập | Token ngẫu nhiên chỉ lưu hash SHA-256 trong MySQL; cookie `HttpOnly`, `SameSite=Lax`, `Secure` theo `COOKIE_SECURE`; hết hạn cố định sau 7 ngày. |
| Cookie giả, hết hạn, đã logout | Trả HTTP 401, không tự chuyển thành khách. Test HTTP SQLite xác nhận hết hạn/logout; test đơn vị kiểm tra token lạ. |
| Khách | `session_id` ngẫu nhiên, lịch sử trong RAM tối đa 1 giờ từ hoạt động cuối; ID lạ hoặc hết hạn được đổi mới và bỏ lịch sử cũ. Không lưu khi F5. |
| Replay chat đăng nhập | Frontend gửi `request_id` UUID. Bảng `chat_request_records` ràng buộc duy nhất theo user. Cùng ID và payload trả response cũ, không thêm tin nhắn; cùng ID nhưng payload khác trả HTTP 409. Test HTTP xác nhận. |

`request_id` tùy chọn để giữ tương thích client cũ; client bỏ trường này không có bảo đảm idempotency. Khách không có khóa replay bền vững. Hai request đồng thời có thể cùng gọi model trước khi một transaction thắng ràng buộc duy nhất, nhưng chỉ một cặp tin nhắn được lưu. `session_id` khách không phải token xác thực.

Tại lần kiểm tra cuối, Ollama và Chroma sẵn sàng nhưng MySQL trên Serbay không chạy. Phần xác thực/replay được kiểm bằng HTTP thật với cơ sở dữ liệu SQLite trong bộ test; cần chạy lại kiểm thử tích hợp khi MySQL được bật để xác nhận triển khai Serbay.

## Chấm điểm tự động

Judge v3 vẫn dùng Qwen local chấm 0/1/2, thêm cổng kiểm tra định lượng: nếu đáp án chuẩn yêu cầu 150 phút cardio/aerobic/hoạt động thể chất mỗi tuần, câu trả lời phải nêu rõ mốc này hoặc lịch có *mức tối thiểu* đạt 150. Nếu không, điểm tối đa là 1/2. Unit test xác nhận `3–5 buổi × 20–30 phút` có mức tối thiểu 60 phút, không đủ 2/2; `5 × 30` và `3 × 50` đủ điều kiện. Token F1 và ROUGE-L không quyết định đúng/sai.

Trong lúc tích hợp, nhóm đã đẩy đủ **193/193 câu test** lên remote. Đã chấm lại trên **cùng câu trả lời chatbot cũ**: `qa-20: 2→1`, `qa-132: 2→1`, `qa-91: 2→2`, `qa-115: 2→2`, `qa-133: 1→1`. Toàn bộ hiện có **115 câu 2/2, 59 câu 1/2, 19 câu 0/2**. Năm dòng có `judge_version=3`, 188 dòng còn `judge_version=2`; tỷ lệ 115/193 là số liệu pha trộn hai phiên bản chấm, không phải ước lượng đồng nhất. Điểm duyệt tay 193 dòng của nhóm vẫn giữ nguyên, theo rubric khác.

**Dữ liệu cần nhóm Data xác minh:** đáp án tham chiếu `qa-132` ghi 15 phút × 2 ngày + 30 phút × 3 ngày = 150 phút, nhưng phép cộng là **120 phút**. Judge v3 đã hạ điểm câu trả lời hiện tại từ 2 xuống 1 vì không bảo đảm mục tiêu 150 phút; tuy vậy đáp án chuẩn vẫn cần được nhóm Data sửa theo quy trình có version.

## Hiệu năng

Đo tuần tự 5 ca, 6 lượt `ChatService.ask`: 4 ca single-turn và 1 ca multi-turn 2 lượt. Tất cả dùng RAG/model local, không tính ca từ chối nhanh. `time.monotonic()` bao gồm truy xuất, sinh câu trả lời và xử lý nội bộ; không gồm mạng frontend/API hoặc judge. Log đầy đủ ở `performance_local.json/.xlsx`.

| Chỉ số | Giá trị |
| --- | ---: |
| Số lượt | 6 |
| Mean | 13,313 giây |
| Median | 12,630 giây |
| Nhanh nhất | 6,633 giây |
| Chậm nhất | 20,760 giây |
| Ca đạt tiêu chí chức năng | 5/5 |

Môi trường: Windows local, Python 3.14.7, Ollama 0.40.13, `qwen3:4b-instruct`, `qwen3-embedding:0.6b`, 782 tài liệu RAG. Digest model nằm trong JSON. Mẫu nhỏ và model đã được dùng trước khi đo; chưa đủ để suy ra SLA. Số 34,5 giây/câu trong báo cáo cũ **không so sánh trực tiếp được** vì bộ câu, điều kiện không đồng nhất; trường `seconds` cũ có thể gồm cả bước judge. Script mới ghi `seconds_measurement=chatbot_only`; dòng cũ khi chấm lại ghi `legacy_unknown_includes_judge_possibly`.

## Chạy lại và nhận test cases từ nhóm Data

Tại `BE/`, khi Ollama và chỉ mục RAG sẵn sàng:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
.\.venv\Scripts\python.exe -m app.scripts.security_performance
.\.venv\Scripts\python.exe -m app.scripts.security_performance --cases data/curated/performance_cases.json --output ../reports/results/performance_local.json
.\.venv\Scripts\python.exe -m app.scripts.evaluate_chatbot --ids qa-20,qa-91,qa-115,qa-132,qa-133
```

Nhóm Data đã đưa đủ 193 câu single-turn vào `test.json` qua commit riêng. Chưa có bộ test prompt injection/multi-turn riêng từ nhóm Data trong repository. Khi nhận được, lưu JSON theo cấu trúc `security_cases.json`, chạy với `--cases <đường dẫn> --output <file riêng>`, ghi version bộ câu và phân biệt single-turn/multi-turn. Không ghi đè 193 câu held-out bằng bộ bảo mật này.
