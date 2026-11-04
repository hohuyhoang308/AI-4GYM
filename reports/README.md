# Báo cáo đánh giá AI-4GYM

Xem [phương pháp và kiểm tra dự án](KIEM_TRA_DU_AN.md) trước khi dùng số liệu để thuyết trình. **Số liệu hiện tại nằm trong Excel và JSONL**; chạy lệnh dưới đây tại `BE/` để xem số câu mới nhất mà không cần bật MySQL/Ollama:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.audit_report
```

## Các file

| File | Nội dung |
| --- | --- |
| `AI-4GYM_train_test_report.xlsx` | 4 sheet: tổng quan; 772 câu train/corpus; 193 câu test; câu trả lời, điểm và ghi chú từng câu test. |
| `evaluation_results.jsonl` | Câu trả lời chatbot, nguồn RAG, điểm Qwen, chỉ số trùng từ và thời gian; dùng làm checkpoint khi chạy tiếp. |
| `KIEM_TRA_DU_AN.md` | Phương pháp, kiểm tra tính toàn vẹn, giới hạn và những việc cần làm trước khi nộp. |
| `MOI_TRUONG_CHAY.md` | Phiên bản phần mềm, digest model và hash mã nguồn dùng cho lần đánh giá local. |
| `report.txt` | Hướng dẫn ngắn bằng văn bản thuần cho người được giao phần test tiếp theo. |

## Kết quả 20 câu đầu do nhóm bàn giao ngày 02/11/2026

Trong 20 câu đầu, Qwen local chấm **12 câu điểm 2, 6 câu điểm 1, 2 câu điểm 0**. Người cùng nhóm đã điền cột duyệt tay cho cả 20 câu: **18 đạt, 2 không đạt** theo tiêu chí đúng, an toàn và hữu ích. Các ghi chú gốc nằm trong cột `Ghi chú duyệt tay` của Excel.

Hai tỷ lệ **12/20** và **18/20** dùng *hai tiêu chí khác nhau*: điểm AI 2/2 yêu cầu đủ ý chính so với đáp án tham chiếu; duyệt tay 1/0 chấp nhận câu trả lời đúng và hữu ích dù có thể thiếu ý. Vì vậy không lấy chênh lệch giữa hai tỷ lệ làm độ chính xác của bộ chấm AI. Điểm AI do chính Qwen chấm theo nội dung, còn Token F1/ROUGE-L chỉ đo trùng từ. Trình độ chuyên môn của người điền cột duyệt tay chưa được ghi lại trong dữ liệu, nên không gọi tỷ lệ 18/20 là đánh giá chuyên gia đã xác minh.

Đã giữ nguyên câu trả lời của `qa-133` từ bản bàn giao khi hợp nhất, vì nhận xét tay của câu đó gắn với chính câu trả lời này. Những câu test còn lại trong JSONL là kết quả của các lần chạy tiếp trên máy local.

## Chạy tiếp đến đủ 193 câu

1. Bật Ollama; kiểm tra `ollama list` có `qwen3:4b-instruct` và `qwen3-embedding:0.6b`. Chỉ mục Chroma phải được tạo bằng lệnh `ingest` như [setup.md](../setup.md). Không cần MySQL để chạy script đánh giá.
2. Đóng file Excel báo cáo nếu đang mở. Tại `BE/` chạy:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.evaluate_chatbot
```

Script bỏ qua câu đã chấm và tiếp tục từ JSONL. Mỗi câu được hỏi trong phiên riêng, không dùng câu test trước làm ngữ cảnh. Nếu dừng giữa chừng, chạy lại cùng lệnh. Sau khi hoàn tất, script xuất lại Excel và giữ các ô duyệt tay đã có. Quá trình có thể mất nhiều thời gian trên GTX 1650.

Nếu JSONL có câu mới nhưng Excel chưa cập nhật (`report_synced: false`), chạy:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.export_report
```

Chạy lại `audit_report`; chỉ khi `evaluation_complete: true` mới có kết quả tự động trên toàn bộ 193 câu. Nếu thay dữ liệu test hoặc model, lưu trữ kết quả cũ rồi đánh giá lại từ đầu; không trộn hai cấu hình.

## Duyệt tay các câu còn lại

Mở sheet `Danh gia Test` trong Excel. Cột `Duyệt tay (1/0)`: nhập `1` nếu câu trả lời đúng, an toàn, đáp ứng yêu cầu; nhập `0` nếu từ chối sai, thiếu nội dung cốt lõi hoặc sai kỹ thuật. Cột `Ghi chú duyệt tay`: nêu ngắn lý do. Nên ghi tên người duyệt và ngày duyệt trong tài liệu nộp, đặc biệt nếu nhiều người cùng chấm. Đóng Excel trước khi chạy lại `export_report`; script giữ các ô M/N đã nhập.

Tỷ lệ đạt tự động = số câu điểm 2 / số câu đã chấm. Tỷ lệ duyệt tay = số câu được đánh dấu 1 / số câu được đánh dấu 0 hoặc 1. Chưa nên ghi hai tỷ lệ này là kết quả đã xác minh khi chưa chạy đủ và rà soát độc lập.
