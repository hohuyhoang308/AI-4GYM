# Hồ sơ báo cáo và kiểm thử AI-4GYM

Cập nhật **25/11/2026**, sau khi pull remote từ `ba4fd9a` lên `9863d6531784`. Các sửa lỗi mới nằm trong thư mục làm việc sau commit nền; hash tệp đã kiểm tra được lưu trong kết quả.

## Tệp chính để nộp

Bản ZIP local sau khi đóng gói: `releases/AI_4GYM_HO_SO_NOP_CT07PM.zip` (không track để tránh trùng toàn bộ nội dung). Các tài liệu bên dưới và bằng chứng đều được quản lý trên Git.

| Tệp | Nội dung |
| --- | --- |
| [Tieu_luan_AI_4GYM_CT07PM.docx](Tieu_luan_AI_4GYM_CT07PM.docx) / [PDF](Tieu_luan_AI_4GYM_CT07PM.pdf) | Tiểu luận viết lại theo mã nguồn, dữ liệu và kiểm thử hiện hành; mục lục đã cập nhật. |
| [Bao_cao_kiem_thu_AI_4GYM.docx](Bao_cao_kiem_thu_AI_4GYM.docx) / [PDF](Bao_cao_kiem_thu_AI_4GYM.pdf) | Báo cáo kiểm thử riêng, lỗi trước/sau và rà soát AI. |
| [Bo_kiem_thu_AI_4GYM.xlsx](Bo_kiem_thu_AI_4GYM.xlsx) | Ma trận ca có điều kiện/đầu vào/kỳ vọng/thực tế; phản hồi mới, 193 bản ghi cũ và nhận xét AI. |
| [AI_REVIEW_NHAN_XET.md](results/AI_REVIEW_NHAN_XET.md) | Đọc lại phản hồi thực tế, nêu các vấn đề nội dung và hạn chế của bộ chấm. |

Hồ sơ mới **không có phần hướng dẫn quy trình kiểm thử**. Mã kiểm thử và log được giữ để đối chiếu. Word ban đầu được sao lưu tại `.local/backups/Tieu_luan_AI_4GYM_CT07PM_truoc_chinh_sua.docx` (ở gốc workspace, không đưa lên Git).

## Kết quả thực thi mới

- **53/53 phương thức backend đạt**, không fail, error hoặc skip; gồm MySQL/Ollama thật và HTTP SQLite cô lập theo từng nhóm.
- **10/10 kịch bản Edge đạt**, không có `pageerror`; desktop 1440×1000 và mobile 390×844.
- TypeScript/Vite production build: **PASS**.
- Excel/JSON/manifest và hồ sơ 193 câu: **PASS**; ID, nội dung và metadata của **783 tài liệu Chroma** khớp dữ liệu kỳ vọng.
- **7/7 ca hồi quy thất bại trước sửa, 7/7 đạt sau sửa**; đã nằm trong tổng 53, không cộng trùng.
- Hỏi mới chatbot: **12 tình huống/16 lượt**, **12/12 điều kiện chức năng đạt**; Qwen judge cho **10 câu 2/2, 2 câu 1/2**, không lỗi gọi hoặc lỗi chấm.
- Rà soát AI bổ sung gắn **6 cờ cần xem lại nội dung/diễn đạt**; không phải tỷ lệ chính xác được xác minh. Chi tiết trong `AI_REVIEW_NHAN_XET.md`.
- 5 lượt RAG mới: mean **85,205 giây**, median **77,137 giây**, min **48,737 giây**, max **124,407 giây**; đo riêng ChatService, không gồm judge.

Kết luận: các luồng phần mềm đạt trong phạm vi thử nghiệm; nội dung chatbot chưa hoàn toàn ổn. Phản hồi kỹ thuật còn chỗ mâu thuẫn hoặc thêm chi tiết thiếu căn cứ, bộ chấm có trường hợp đánh giá sai. Hồ sơ ghi rõ các điểm này, không đổi kết quả chức năng thành độ chính xác AI.

## Bằng chứng

| Tệp | Vai trò |
| --- | --- |
| `results/software_test_results.json/.txt` | Backend theo test_id, hash tệp, build và kiểm tra nội dung chỉ mục. |
| `results/regressions_before.json/.txt`; `results/regressions_after.json/.txt` | 7 nhóm lỗi trước/sau sửa. |
| `results/browser_test_results.json` | 10 kịch bản Edge và lỗi JavaScript. |
| `results/chatbot_ai_review.json` | Hỏi mới, phản hồi, nguồn, điều kiện, điểm AI và thời gian riêng. |
| `results/independent_ai_review.json` | Rà soát bổ sung theo ca, gắn hash hồ sơ đã đọc; không chấm mù/duyệt chuyên gia. |
| `evidence/` | Ảnh ứng dụng, sơ đồ, biểu đồ, môi trường và kết quả kiểm tra PDF; ảnh xem thử chỉ giữ local. |
| `submission_manifest.json` | Hash hiện vật chính sau khi hoàn thiện. |

## Hồ sơ 193 câu từ remote

`evaluation_results.jsonl` và `AI-4GYM_train_test_report.xlsx` được giữ nguyên trong đợt này. Có **132 câu 2/2 (68,39%), 56 câu 1/2 (29,02%), 5 câu 0/2 (2,59%)**; **154 dòng judge v2, 39 dòng v3**. Excel có **187 nhãn tay đạt/6 không đạt**. Đây là hồ sơ bàn giao, không phải phép đo lại toàn bộ chatbot sau sửa, chưa có xác minh chuyên gia độc lập.

Excel hiện hành có nguồn theo câu; dữ liệu gồm 965 cặp hỏi–đáp, 772 train/corpus, 193 test và 11 bài tập bổ sung. Có 1 câu test gần trùng từ vựng với train theo Jaccard ≥0,8; không trùng ID hoặc câu hỏi chuẩn hóa giữa hai tập. “Train” là corpus RAG, không phải fine-tune Qwen.

154 trường thời gian cũ không ghi kiểu đo, 5 trường ghi legacy có thể gồm judge, 34 trường ghi chatbot_only. Không tính latency chung từ chúng. Số liệu cũ 115/59/19, nhãn tay 174/19 và 782 tài liệu trong một số báo cáo lịch sử không thay số liệu hiện hành.

Các tài liệu trong `history/` được giữ làm hồ sơ lịch sử theo ngày ghi trong tệp. Ưu tiên báo cáo mới và JSON khi trích kết quả 25/11/2026.
