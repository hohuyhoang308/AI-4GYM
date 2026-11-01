# Báo cáo đánh giá AI-4GYM

## Trạng thái bàn giao ngày 01/11/2026

- Tập dữ liệu: **965 câu** từ `BE/data/raw/data.xlsx`; chia **772 train (80%)** và **193 test (20%)**.
- Đã chạy và chấm bằng model local: **19/193 câu test**; gồm **12 đạt, 5 đúng một phần, 2 sai/từ chối**. **174 câu chưa chạy**. Tỷ lệ đạt tự động hiện là **12/19 (63,2%) trên phần đã chạy**, **không được báo cáo là độ chính xác trên toàn bộ tập test**.
- Đã dừng tiến trình đánh giá theo yêu cầu. Không có tiến trình đánh giá chạy nền khi bàn giao.

## Các file

| File | Nội dung |
| --- | --- |
| `AI-4GYM_train_test_report.xlsx` | 4 sheet: tổng quan; danh sách train; danh sách test; câu trả lời chatbot và điểm từng câu test. |
| `evaluation_results.jsonl` | Kết quả từng câu đã chạy, gồm câu trả lời, nguồn RAG, điểm và lý do chấm. Script dùng file này để tiếp tục khi chạy lại. |

## Cách chạy tiếp đến đủ 193 câu

1. Bật Ollama local với `qwen3:4b-instruct` và `qwen3-embedding:0.6b`. Đảm bảo chỉ mục Chroma đã được tạo bằng `ingest` như [setup.md](../setup.md).
2. Đóng file Excel báo cáo nếu đang mở, rồi mở PowerShell tại thư mục `BE/` và chạy:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.evaluate_chatbot
```

Script bỏ qua các câu đã chấm, dùng lại câu trả lời đã lưu nếu bước chấm bị gián đoạn, rồi chạy các câu còn lại. Kết quả được lưu theo từng câu; có thể chạy lại cùng lệnh sau khi dừng. Sau khi hoàn tất, script tạo lại Excel và giữ nguyên các ô đã duyệt tay. Model chạy trên máy, không gọi API AI bên ngoài. Quá trình 193 câu có thể mất nhiều thời gian trên GTX 1650.

Nếu chỉ cần tạo lại Excel từ kết quả đã lưu, không gọi chatbot:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.export_report
```

Nếu đổi dữ liệu test hoặc model, phải đánh giá lại từ đầu; không trộn kết quả của hai cấu hình. Lưu file `evaluation_results.jsonl` cũ sang nơi khác rồi chạy lại.

## Cách đọc điểm

- `Điểm AI (0-2)`: Qwen local so sánh câu trả lời chatbot với đáp án tham chiếu. **2** = đủ ý chính, **1** = đúng một phần, **0** = sai hoặc từ chối. Đây là điểm **tự động**, chưa phải kết luận độc lập của người chấm.
- `Tỷ lệ đạt tự động` = số câu điểm 2 / số câu **đã chạy**. Chỉ dùng làm kết quả toàn bộ tập test khi `Đã chạy test` là `193/193`.
- `Token F1` và `ROUGE-L F1` đo độ trùng từ/cụm từ với đáp án tham chiếu; không tự chứng minh nội dung đúng.
- `Số nguồn` và `ID nguồn RAG` cho biết tài liệu chatbot truy xuất. Tập test được giữ ngoài chỉ mục Chroma.
- Cột `Duyệt tay (1/0)` và `Ghi chú duyệt tay` để người đánh giá kiểm tra lại. Nhập 1 nếu đạt, 0 nếu không đạt; tỷ lệ duyệt tay ở sheet `Tong quan` được Excel tính khi mở file.

Phép chia 80/20 là chia dữ liệu cho RAG và đánh giá; dự án không huấn luyện lại trọng số Qwen. Cần kiểm tra thủ công các câu trả lời và điểm AI trước khi sử dụng trong báo cáo học thuật.
