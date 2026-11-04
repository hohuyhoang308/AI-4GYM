# Báo cáo đánh giá AI-4GYM

Xem [kiểm tra dự án và phương pháp báo cáo](KIEM_TRA_DU_AN.md) trước khi dùng số liệu để thuyết trình. Tại `BE/`, chạy `.\.venv\Scripts\python.exe -m app.scripts.audit_report` để xem số câu đã chấm mới nhất; lệnh này không cần MySQL hoặc Ollama.

## Kế hoạch phân chia công việc đánh giá (2 Phần)

Tổng tập kiểm thử gồm **193 câu hỏi độc lập (held-out test set)** được trích xuất từ 965 cặp dữ liệu gốc (tỷ lệ 20%). Công việc đánh giá được chia làm 2 giai đoạn:

### ✅ PHẦN 1: Đánh giá & Duyệt tay mẫu 20 câu đầu (Đã hoàn thành)
* **Phạm vi**: 20 câu test đầu tiên (từ `qa-2` đến `qa-133`).
* **Đánh giá tự động bằng AI (Qwen local)**:
  * Đạt tự động (2/2): **12/20 câu** (60.0%).
  * Đúng một phần (1/2): **6/20 câu** (30.0%).
  * Sai hoặc từ chối (0/2): **2/20 câu** (10.0% - do bộ lọc từ khóa scope hoặc RAG chưa có tài liệu tương ứng).
  * Token F1 trung bình: **27.7%** | ROUGE-L F1: **17.9%** | Thời gian phản hồi TB: **38.7 giây/câu**.
* **Duyệt tay độc lập (Human Review)**:
  * **Đã hoàn tất 100%** cột `Duyệt tay (1/0)` và `Ghi chú duyệt tay` cho 20 câu.
  * Tỷ lệ duyệt tay đạt: **18/20 câu (90.0%)**.
  * Nhận xét: Điểm AI tự động chấm khá khắt khe khi chỉ so sánh độ trùng khớp từng từ với đáp án tham chiếu ngắn; trong khi duyệt tay cho thấy chatbot đưa ra nhiều biến thể bài tập và lưu ý kỹ thuật/an toàn rất hữu ích cho người mới tập.

---

### ⏳ PHẦN 2: Bàn giao cho người kiểm thử tiếp theo (173 câu còn lại)
* **Phạm vi**: Từ câu thứ 21 đến câu thứ 193 (từ ID `qa-137` đến hết tập test).
* **Nhiệm vụ của người test sau**:
  1. Chạy tiếp hệ thống đánh giá tự động trên các câu còn lại.
  2. Dựa vào 20 câu mẫu đã duyệt ở Phần 1 để tiếp tục điền cột `Duyệt tay (1/0)` và `Ghi chú duyệt tay` cho các câu tiếp theo.

---

## Hướng dẫn cho người test Phần 2

### Bước 1: Tiếp tục chạy đánh giá tự động
1. Bật Ollama (bằng file `run_ollama.bat` tại thư mục gốc).
2. Đóng file Excel `AI-4GYM_train_test_report.xlsx` nếu đang mở.
3. Mở PowerShell tại thư mục `BE/` và chạy lệnh:
   ```powershell
   .\.venv\Scripts\python.exe -m app.scripts.evaluate_chatbot
   ```
   * *Cơ chế hoạt động*: Script sẽ **tự động nhận diện 20 câu đã làm** từ file `reports/evaluation_results.jsonl`, **giữ nguyên 100% kết quả và nhận xét duyệt tay cũ**, và tiếp tục chạy từ câu 21 (`qa-137`) trở đi.
   * Nếu quá trình chạy bị gián đoạn, chỉ cần gõ lại đúng lệnh trên để tiếp tục.

### Bước 2: Hướng dẫn duyệt tay (Rubric chuẩn)
Người test mở file Excel [AI-4GYM_train_test_report.xlsx](AI-4GYM_train_test_report.xlsx), vào sheet `Danh gia Test` và điền:
* **Cột M (`Duyệt tay (1/0)`)**:
  * Nhập `1`: Nếu câu trả lời của chatbot chính xác, an toàn, hỗ trợ đúng yêu cầu bài tập/kỹ thuật của người tập (dù cách diễn đạt có thể khác đáp án tham chiếu).
  * Nhập `0`: Nếu chatbot từ chối sai (false negative), trả lời sai lệch kỹ thuật, hoặc bịa đặt kiến thức nguy hiểm.
* **Cột N (`Ghi chú duyệt tay`)**: Ghi ngắn gọn lý do vì sao đạt hoặc chưa đạt (tham khảo 20 dòng mẫu từ dòng 2 đến dòng 21).

### Bước 3: Cập nhật lại báo cáo sau khi duyệt tay
Sau khi điền xong trên Excel hoặc cập nhật file JSONL, đứng tại `BE/` và chạy lệnh xuất báo cáo:
```powershell
.\.venv\Scripts\python.exe -m app.scripts.export_report
```
Sheet `Tong quan` sẽ tự động cập nhật biểu đồ và tỷ lệ duyệt tay của toàn bộ tập kiểm thử.
