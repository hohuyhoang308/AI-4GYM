# Kiểm tra dự án và phương pháp báo cáo

Ngày rà soát: **04/11/2026**. Trạng thái số câu đã chấm có thể thay đổi khi chạy tiếp; dùng lệnh ở cuối để xem số liệu mới nhất.

## Kết luận sử dụng

Dự án đã có backend FastAPI, LangChain + Chroma + Ollama local, frontend React, MySQL cho tài khoản và lịch sử, bộ dữ liệu JSON, phép chia train/test cố định và báo cáo Excel. **Chưa nên trình bày đây là mô hình đã được chứng minh đạt một tỷ lệ chính xác trên toàn bộ tập test** cho tới khi chấm đủ 193 câu và rà soát độc lập. File Excel hiện được kiểm tra là khớp với các kết quả đã lưu; lệnh kiểm toán không đánh giá độ đúng về thể hình.

## Phương pháp có thể ghi trong báo cáo học thuật

1. **Dữ liệu:** `BE/data/raw/data.xlsx` có 965 cặp hỏi đáp. Chuyển nguyên dữ liệu hợp lệ sang `qa.json`, giữ ID và số dòng Excel. Thêm 10 bài tập biên soạn riêng trong `exercises.json`.
2. **Phép chia:** SHA-256 của câu hỏi đã chuẩn hóa với seed 42, giữ các câu hỏi trùng chữ trong cùng một tập. Kết quả 772 câu train/corpus (80%) và 193 câu test (20%). Chỉ 772 câu train và 10 bài tập được đưa vào Chroma, tổng 782 tài liệu. Test không nằm trong chỉ mục.
3. **Mô hình:** Ollama chạy Qwen local để sinh câu trả lời; Ollama embedding local để truy xuất vector. LangChain ghép tài liệu truy xuất, tối đa 3 lượt hỏi đáp gần nhất và câu hỏi mới. Không cập nhật trọng số model; từ **train** ở đây nghĩa là dữ liệu lập chỉ mục RAG, không phải fine-tuning.
4. **Đánh giá:** mỗi câu test được hỏi trong một phiên độc lập qua cùng `ChatService` phục vụ web. Lưu nguyên văn câu trả lời, ID nguồn RAG và thời gian vào JSONL. Qwen local so câu trả lời với đáp án tham chiếu theo thang 0/1/2. Token F1 và ROUGE-L F1 chỉ đo trùng từ và thứ tự từ. Bảng Excel cho phép nhập điểm duyệt tay 1/0.
5. **Cách tính:** tỷ lệ đạt tự động trên phần đã chạy = số câu điểm 2 / số câu có điểm 0–2. Tỷ lệ duyệt tay = số câu được người duyệt đánh dấu 1 / số câu đã được người duyệt đánh dấu 0 hoặc 1. Chỉ gọi tỷ lệ đầu tiên là kết quả toàn bộ tập test khi số câu đã chấm bằng 193/193.

## Kiểm tra đã thực hiện

| Hạng mục | Kết quả |
| --- | --- |
| Excel gốc ↔ `qa.json` ↔ manifest | Khớp; 965 câu, hash nguồn khớp |
| Train/test | 772/193, không lẫn ID hoặc câu hỏi trùng sau chuẩn hóa |
| Chroma local | 782 tài liệu, không chứa ID test (test tự động đã đạt) |
| Báo cáo Excel ↔ JSONL | Khớp số câu, điểm và câu trả lời đã lưu (lệnh `audit_report`) |
| Frontend | `npm run build` đạt |
| Gói frontend production | `npm audit --omit=dev --audit-level=high` không báo lỗ hổng tại thời điểm rà soát |
| Backend unit test | 10 bài đạt; 1 bài tích hợp chỉ chạy khi MySQL, Ollama và Chroma sẵn sàng |

## Giới hạn cần nêu thẳng

- **Nguồn 965 câu:** file Excel chỉ ghi `data.xlsx`, không có URL/tác giả/ngày truy cập cho từng câu. Không thể khẳng định toàn bộ 965 câu đã được đối chiếu với nguồn chuyên môn. Mười bài tập bổ sung có URL ACE; nguồn ACSM chỉ hỗ trợ định hướng tập sức mạnh chung, còn các lịch 1–6 buổi là mẫu do dự án biên soạn. Xem [ACE Exercise Library](https://www.acefitness.org/resources/everyone/exercise-library/) và [ACSM 2026 resistance training guidance](https://acsm.org/resistance-training-guidelines-update-2026/).
- **Điểm AI:** cùng họ model Qwen tạo câu trả lời và chấm câu trả lời, nên điểm tự động có thể thiên lệch. Chưa có người chấm độc lập hoặc độ đồng thuận giữa người chấm. Không gọi điểm này là độ chính xác đã xác minh.
- **Phân chia dữ liệu:** đã ngăn trùng câu hỏi theo chữ sau chuẩn hóa. Phép so Jaccard trên tập từ của câu hỏi phát hiện **4 câu test** có độ tương đồng từ vựng ít nhất 0,8 với một câu train; ví dụ câu về chuỗi bài tập tạ chỉ khác cụm tiếng Anh trong ngoặc. Đây là dấu hiệu cần rà soát rò rỉ ngữ nghĩa, chưa phải kết luận cả 4 câu là bản sao. Chưa kiểm tra toàn bộ nội dung đáp án trùng nhau giữa hai tập. Mười bài tập ACE nằm trong corpus ở cả lúc đánh giá, nên một số câu test liên quan trực tiếp có thể được hỗ trợ bởi chúng.
- **Phạm vi:** kiểm tra tĩnh cho thấy bộ lọc từ khóa đánh dấu 14/193 câu test là ngoài phạm vi khi không có lịch sử, dù một số câu có thể liên quan đến hoạt động thể chất. Đây là kết quả đo trên tập test đã giữ riêng; tránh sửa bộ lọc dựa vào từng câu test rồi dùng chính tập này để công bố kết quả mới. Nếu sửa phạm vi hoặc dữ liệu, cần tạo bộ test mới và đánh giá lại.
- **Kiểm thử triển khai:** MySQL Serbay chưa chạy tại thời điểm rà soát, nên luồng đăng ký, lưu lịch sử và khôi phục sau F5 chưa được xác nhận lại bằng test tích hợp ở lượt rà soát này. Test sẽ chạy khi dịch vụ sẵn sàng.
- **Phạm vi đánh giá:** tập 193 câu chỉ kiểm tra hỏi đáp đơn lượt từ Excel. Chưa có bộ đánh giá riêng cho hội thoại nhiều lượt, từ chối câu ngoài Gym, tính đúng của lịch 1–6 buổi, tính an toàn khi có đau/chấn thương hoặc trải nghiệm người dùng.

## Việc còn cần làm trước khi nộp kết quả cuối

1. Chạy `python -m app.scripts.evaluate_chatbot` đến khi `evaluation_complete` là `true`; xuất lại Excel.
2. Có người am hiểu thể hình rà soát câu trả lời, nhất là kỹ thuật, an toàn và các câu điểm 0/1; điền cột `Duyệt tay (1/0)` và ghi chú. Giữ nguyên đáp án gốc khi đánh giá.
3. Bổ sung nguồn gốc từng câu của Excel hoặc ghi rõ đây là bộ dữ liệu được cung cấp, chưa truy vết nguồn; không gán chung nguồn ACE/ACSM cho 965 câu.
4. Bật MySQL Serbay rồi chạy bài test tích hợp và thử thực tế: đăng ký, đăng nhập, chat khách, lưu/mở/xóa hội thoại, F5, logout.
5. Trước khi công bố số liệu của phiên bản mới, chốt phiên bản dữ liệu, model, prompt và mã nguồn; nếu thay đổi hành vi chatbot sau khi xem test, tạo tập đánh giá mới.

## Tự kiểm tra số liệu

Tại `BE/`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.audit_report
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Lệnh đầu không gọi model, MySQL hay Chroma. `artifact_integrity: PASS` nghĩa là các file nguồn, phép chia và kết quả Excel đã xuất không mâu thuẫn với JSONL; **không** có nghĩa chatbot trả lời đúng. Khi đánh giá đang chạy, `report_synced: false` là bình thường vì JSONL ghi từng câu còn Excel chỉ xuất lúc kết thúc; chạy lại `export_report` sau khi dừng để đồng bộ. `evaluation_complete` cho biết đã chấm đủ 193 câu chưa. Test tích hợp được bỏ qua khi thiếu dịch vụ và sẽ được báo là `skipped`.
