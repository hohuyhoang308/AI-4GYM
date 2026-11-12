# Báo cáo đánh giá AI-4GYM

Trạng thái kiểm tra ngày 12/11/2026: **193/193 câu test đã có câu trả lời và điểm tự động**. Dùng lệnh dưới tại `BE/` để kiểm tra lại số liệu từ file:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.audit_report
```

| File | Nội dung |
| --- | --- |
| `AI-4GYM_train_test_report.xlsx` | 4 sheet: tổng quan, 772 câu train, 193 câu test, câu trả lời/điểm/duyệt tay từng câu. |
| `evaluation_results.jsonl` | 193 câu trả lời, nguồn RAG, điểm Qwen và chỉ số trùng từ. |
| `SECURITY_PERFORMANCE.md` | Bàn giao kỹ thuật 2: an toàn prompt, session/replay, sửa judge, đo hiệu năng. |
| `security_performance.json/.xlsx` | 7 ca an toàn, 9 request với log pass/fail. |
| `performance_local.json/.xlsx` | 5 ca RAG, 6 lượt đo độ trễ local. |
| `KIEM_TRA_DU_AN.md` | Phương pháp, dữ liệu và giới hạn; bản rà soát gốc ngày 04/11/2026, đọc cùng trạng thái mới ở đây. |
| `MOI_TRUONG_CHAY.md` | Ảnh chụp môi trường và digest model của lần rà soát trước. |

## Kết quả hiện tại

| Điểm tự động | 20 câu đầu | 173 câu sau | Toàn bộ 193 câu |
| --- | ---: | ---: | ---: |
| 2/2 | 10 | 105 | **115 (59,6%)** |
| 1/2 | 8 | 51 | **59 (30,6%)** |
| 0/2 | 2 | 17 | **19 (9,8%)** |

Năm câu được chấm lại theo judge v3 trên **cùng câu trả lời cũ**: `qa-20` từ 2 xuống 1; `qa-132` từ 2 xuống 1; `qa-91`, `qa-115` giữ 2; `qa-133` giữ 1. Còn **188 dòng dùng judge v2**, vì vậy tỷ lệ 59,6% là thống kê của bộ kết quả có hai phiên bản chấm, chưa phải một ước lượng đồng nhất. Cổng định lượng v3 giới hạn điểm khi đáp án chuẩn yêu cầu tối thiểu 150 phút vận động/tuần mà câu trả lời không bảo đảm ngưỡng này.

Sheet `Danh gia Test` có **193/193 nhãn duyệt tay** do nhóm điền; 174 đạt, 19 không đạt theo tiêu chí 1/0 của nhóm. Dữ liệu không ghi bằng chứng về chuyên môn hoặc mức đồng thuận giữa nhiều người chấm. Không gọi tỷ lệ này là độ chính xác được chuyên gia xác minh. Điểm AI do cùng họ model Qwen chấm; Token F1/ROUGE-L chỉ đo mức trùng từ.

Trường `seconds` trong JSONL cũ có thể gồm cả bước judge, nên **34,5 giây/câu không phải phép đo riêng tốc độ chatbot**. Phép đo có điều kiện rõ ràng nằm trong `performance_local.json/.xlsx`: 6 lượt RAG, mean 13,313 giây, median 12,630 giây, min 6,633 giây, max 20,760 giây. Mẫu nhỏ, không so sánh trực tiếp với số cũ.

**Dữ liệu cần xem lại:** `qa-132` tham chiếu cộng lịch 15 phút × 2 ngày + 30 phút × 3 ngày thành 150 phút, nhưng thực tế là 120 phút. Nhóm Data cần kiểm tra nguồn và sửa theo phiên bản dữ liệu mới; không tự sửa tập test hiện tại rồi coi tỷ lệ cũ còn nguyên giá trị. Ngoài ra, 4 câu test có câu train tương đồng từ vựng Jaccard ≥ 0,8; xem `KIEM_TRA_DU_AN.md`.

## Xuất lại và kiểm tra

Đóng Excel trước khi xuất. `export_report` đọc JSONL và giữ các ô duyệt tay M/N đã điền:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.export_report
.\.venv\Scripts\python.exe -m app.scripts.audit_report
```

Để chấm lại một nhóm câu, dùng `python -m app.scripts.evaluate_chatbot --ids qa-20,qa-132`. **Không chạy toàn bộ chỉ để kiểm tra vài câu**: script sẽ chấm lại các dòng cũ theo phiên bản judge mới, thay đổi thang thống kê và mất thời gian. Nếu đổi dữ liệu, prompt, model hoặc bộ lọc phạm vi, tạo tập đánh giá mới trước khi so sánh chất lượng của phiên bản chatbot mới.
