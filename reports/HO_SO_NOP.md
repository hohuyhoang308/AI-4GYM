# Hồ sơ báo cáo và kiểm thử AI-4GYM

Cập nhật **25/11/2026**. Log kiểm thử cùng ngày ghi commit nền `9863d6531784` và hash các mô-đun sau sửa; dùng hash trong bằng chứng để nhận diện bản đã kiểm tra. Ngày cập nhật Word/PDF hoặc commit xuất bản tài liệu không phải thời điểm chạy lại kiểm thử.

## Tệp chính để nộp

Bản ZIP đầy đủ: [releases/AI_4GYM_HO_SO_NOP_CT07PM.zip](releases/AI_4GYM_HO_SO_NOP_CT07PM.zip). Cả ZIP, các tài liệu bên dưới và bằng chứng đều được quản lý trên Git.

| Tệp | Nội dung |
| --- | --- |
| [Tieu_luan_AI_4GYM_CT07PM.docx](Tieu_luan_AI_4GYM_CT07PM.docx) / [PDF](Tieu_luan_AI_4GYM_CT07PM.pdf) | Tiểu luận của nhóm được chỉnh sửa, bổ sung theo biểu mẫu nhà trường và hồ sơ hiện hành; giữ bố cục bốn chương, bỏ dòng Khóa ở bìa và cập nhật mục lục. |
| [Bao_cao_kiem_thu_AI_4GYM.docx](Bao_cao_kiem_thu_AI_4GYM.docx) / [PDF](Bao_cao_kiem_thu_AI_4GYM.pdf) | Báo cáo kiểm thử riêng, lỗi trước/sau và rà soát AI. |
| [Bo_kiem_thu_AI_4GYM.xlsx](Bo_kiem_thu_AI_4GYM.xlsx) | Ma trận ca có điều kiện/đầu vào/kỳ vọng/thực tế; phản hồi mới, 193 bản ghi cũ và nhận xét AI. |
| [AI_REVIEW_NHAN_XET.md](results/AI_REVIEW_NHAN_XET.md) | Đọc lại phản hồi thực tế, nêu các vấn đề nội dung và hạn chế của bộ chấm. |

Mã kiểm thử và log được giữ để đối chiếu. Tiểu luận hiện hành dựa trên bản của nhóm, đã chỉnh theo biểu mẫu trường; bản Word/PDF là cặp tài liệu cần cập nhật cùng nhau. Bản sao local, nếu có, không thuộc gói nộp và không được bảo đảm có sẵn sau khi clone. [Biên bản rà soát](../docs/report-review.md) ghi các hạng mục đã đối chiếu.

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

154 trường thời gian cũ không ghi kiểu đo, 5 trường ghi legacy có thể gồm judge, 34 trường ghi chatbot_only. Không tính latency chung từ chúng. Các phân bố cũ như 115/59/19 hoặc 117/57/19, nhãn tay 174/19 và 782 tài liệu trong hồ sơ lịch sử không thay số liệu hiện hành.

Các tài liệu trong `history/` được giữ làm hồ sơ lịch sử theo ngày ghi trong tệp. Ưu tiên báo cáo mới và JSON khi trích kết quả 25/11/2026.
