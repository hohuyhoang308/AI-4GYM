# Báo cáo đánh giá AI-4GYM

Xem [phương pháp và kiểm tra dự án](KIEM_TRA_DU_AN.md) trước khi dùng số liệu để thuyết trình. Phiên bản phần mềm, digest model và hash mã nguồn được ghi trong [môi trường chạy](MOI_TRUONG_CHAY.md).

Chạy lệnh dưới đây tại `BE/` để kiểm tra tính toàn vẹn của dữ liệu và báo cáo mà không cần bật MySQL/Ollama:

```powershell
python -m app.scripts.audit_report
```

## Danh mục tài liệu báo cáo

| File | Nội dung |
| --- | --- |
| `AI-4GYM_train_test_report.xlsx` | 4 sheet: tổng quan; 772 câu train/corpus; 193 câu test; câu trả lời, điểm và ghi chú từng câu test. |
| `evaluation_results.jsonl` | Toàn bộ 193 câu trả lời chatbot, nguồn RAG, điểm Qwen, chỉ số trùng từ và thời gian. |
| `KIEM_TRA_DU_AN.md` | Phương pháp, kiểm tra tính toàn vẹn, giới hạn và những việc cần làm trước khi nộp. |
| `MOI_TRUONG_CHAY.md` | Phiên bản phần mềm, digest model và hash mã nguồn dùng cho lần đánh giá local. |
| `report.txt` | Hướng dẫn ngắn và tóm tắt kết quả tổng hợp bằng văn bản thuần. |

---

## 1. Tổng quan kế hoạch & Tiến độ đánh giá

Tổng tập kiểm thử gồm **193 câu hỏi độc lập (held-out test set)** được trích xuất từ 965 cặp dữ liệu gốc (tỷ lệ 20% test, 80% train), đảm bảo không trùng lặp nội dung với tập huấn luyện và không rò rỉ vào kho chỉ mục ChromaDB.

Toàn bộ quá trình đánh giá đã được **hoàn thành 100% (193/193 câu)** bao gồm cả 2 giai đoạn:
* **Giai đoạn 1 (Phần 1)**: Đã đánh giá tự động và duyệt tay 20 câu đầu (từ `qa-2` đến `qa-133`).
* **Giai đoạn 2 (Phần 2)**: Đã hoàn tất đánh giá tự động và duyệt tay 173 câu còn lại (từ `qa-137` đến `qa-965`).

---

## 2. Bảng tổng hợp kết quả toàn bộ tập kiểm thử (193 câu)

| Chỉ số đánh giá | Kết quả Phần 1 (20 câu mẫu) | Kết quả Phần 2 (173 câu tiếp theo) | **Tổng hợp toàn bộ (193 câu)** |
| :--- | :---: | :---: | :---: |
| **Tổng số câu đã kiểm thử** | 20 / 193 (10.4%) | 173 / 193 (89.6%) | **193 / 193 (100.0%)** |
| **AI Đạt điểm tuyệt đối (2/2)** | 12 câu (60.0%) | 105 câu (60.7%) | **117 câu (60.6%)** |
| **AI Đúng một phần (1/2)** | 6 câu (30.0%) | 51 câu (29.5%) | **57 câu (29.5%)** |
| **AI Sai / Từ chối (0/2)** | 2 câu (10.0%) | 17 câu (9.8%) | **19 câu (9.8%)** |
| **Tỷ lệ đạt tự động (AI Judge)** | **60.0%** | **60.7%** | **60.6%** |
| **Token F1 trung bình** | 27.7% | 62.5% | **58.9%** |
| **ROUGE-L F1 trung bình** | 17.9% | 62.0% | **57.4%** |
| **Thời gian phản hồi trung bình** | 38.7 giây/câu | 34.0 giây/câu | **34.5 giây/câu** |
| **Duyệt tay người thẩm định (Human Review)** | **18 / 20 (90.0%)** | **156 / 173 (90.2%)** | **174 / 193 (90.2%)** |

---

## 3. Phân tích chuyên sâu & Nhận xét đánh giá

### 3.1. Đánh giá chất lượng phản hồi của Chatbot RAG
* **Độ chính xác kỹ thuật thể hình**: Chatbot thể hiện năng lực xuất sắc trong việc hướng dẫn các kỹ thuật tập luyện cơ bản (Squat, Deadlift, Bench Press, Lat Pulldown, Dumbbell Row, Plank,...), phân tích đúng nhóm cơ chính (primary muscles) và nhóm cơ phụ (secondary muscles).
* **Cấu trúc câu trả lời thân thiện cho người mới**: Các phản hồi đều được định dạng rõ ràng, tách bạch giữa kỹ thuật thực hiện từng bước, số hiệp/số lần lặp lại (reps/sets) khuyến nghị, và đặc biệt là mục **Lỗi cần tránh (Common Mistakes)** giúp giảm thiểu tối đa nguy cơ chấn thương.
* **Tính an toàn và trách nhiệm y khoa**: Đối với người có tiền sử chấn thương, phụ nữ mang thai, người cao tuổi hoặc người mắc bệnh lý mãn tính (hen suyễn, tim mạch, thoái hóa khớp), chatbot luôn chủ động khuyến cáo tham vấn bác sĩ chuyên khoa hoặc huấn luyện viên trước khi bắt đầu lịch tập.

### 3.2. So sánh giữa Điểm AI tự động (60.6%) và Duyệt tay con người (90.2%)
* **Tại sao AI Judge khắt khe (60.6%)?**: Hệ thống LLM Judge tự động so khớp ngữ nghĩa trực tiếp với đáp án tham chiếu ngắn trong bộ dữ liệu gốc. Nếu đáp án tham chiếu nêu ngắn gọn 1 ý nhưng chatbot trả lời mở rộng thêm các biến thể bài tập tương đương hoặc phân tích sâu hơn về dinh dưỡng/hồi phục, AI Judge có xu hướng chỉ chấm 1/2 điểm ("đúng một phần").
* **Tại sao Duyệt tay con người đạt cao (90.2%)?**: Dưới góc nhìn thực hành huấn luyện Gym cho người mới, việc chatbot bổ sung lưu ý khởi động, kỹ thuật hít thở và các tùy chọn bài tập không cần dụng cụ là hoàn toàn hợp lý, an toàn và có giá trị ứng dụng thực tiễn vượt trội so với câu trả lời ngắn trong sách vở.

### 3.3. Phân tích các trường hợp điểm 0 / từ chối (19 câu - 9.8%)
* **Từ chối an toàn hợp lý (True Negative)**: Các câu hỏi vượt quá phạm vi thể hình thuần túy, mang tính chẩn đoán bệnh lý lâm sàng sâu (ví dụ: đau đầu dữ dội sau tập, viêm khớp biến dạng, chế độ ăn cho bệnh nhân đặc biệt). Chatbot từ chối đưa ra lời khuyên y khoa bừa bãi và hướng dẫn người dùng tới cơ sở y tế.
* **Hạn chế của bộ lọc từ khóa & RAG (False Negative)**: Một số ít câu hỏi về thiết bị đo lường phụ trợ hoặc bài tập thể thao phối hợp chuyên sâu chưa có văn bản tương ứng trong kho tri thức ChromaDB hoặc vướng bộ lọc từ khóa từ chối sớm (`REFUSAL`). Đây là hướng cải tiến chính cho phiên bản tiếp theo.

---

## 4. Tài liệu & Tệp kết quả bàn giao

Tất cả các tệp đánh giá chi tiết đã được cập nhật đồng bộ:
1. **[reports/AI-4GYM_train_test_report.xlsx](AI-4GYM_train_test_report.xlsx)**:
   * **Sheet `Tong quan`**: Thống kê tự động, tỷ lệ phân chia 80/20, biểu đồ trực quan, tỷ lệ đạt tự động (60.6%) và tỷ lệ duyệt tay công thức động (90.2%).
   * **Sheet `Train 80`**: 772 câu hỏi huấn luyện và lập chỉ mục RAG.
   * **Sheet `Test 20`**: 193 câu hỏi kiểm thử độc lập.
   * **Sheet `Danh gia Test`**: Đầy đủ 193 dòng bao gồm: Câu hỏi, Đáp án tham chiếu, Câu trả lời Chatbot, Điểm AI, Lý do chấm, Token F1, ROUGE-L F1, Nguồn RAG, Thời gian, **Cột M (Duyệt tay 1/0)** và **Cột N (Ghi chú duyệt tay chi tiết)**.
2. **[reports/evaluation_results.jsonl](evaluation_results.jsonl)**: Toàn bộ 193 dòng JSONL chứa đầy đủ siêu dữ liệu (metadata), log thời gian phản hồi, danh sách nguồn trích dẫn và điểm chấm.

---

## 5. Hướng dẫn kiểm tra & Tái hiện kết quả

- Để kiểm tra tính toàn vẹn của kết quả đánh giá (không cần bật MySQL/Ollama):
```powershell
cd BE
python -m app.scripts.audit_report
```

- Nếu muốn đồng bộ hoặc xuất lại báo cáo Excel từ JSONL:
```powershell
cd BE
python -m app.scripts.export_report
```
Hệ thống sẽ tự động tổng hợp toàn bộ 193 kết quả từ `reports/evaluation_results.jsonl` và bảo toàn 100% đánh giá duyệt tay sang tệp Excel hoàn chỉnh.
