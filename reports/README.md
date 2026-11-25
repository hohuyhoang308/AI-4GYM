# Báo cáo và kiểm thử AI-4GYM

## Hồ sơ hiện hành — 25/11/2026

- [Tiểu luận Word](Tieu_luan_AI_4GYM_CT07PM.docx) · [PDF](Tieu_luan_AI_4GYM_CT07PM.pdf)
- [Báo cáo kiểm thử Word](Bao_cao_kiem_thu_AI_4GYM.docx) · [PDF](Bao_cao_kiem_thu_AI_4GYM.pdf)
- [Bộ ca kiểm thử Excel](Bo_kiem_thu_AI_4GYM.xlsx)
- [Danh mục hồ sơ nộp và kết luận](HO_SO_NOP.md)
- [Nhận xét AI về chatbot](results/AI_REVIEW_NHAN_XET.md)
- [Biên bản rà soát báo cáo và docs](../docs/report-review.md)

**Log ngày 25/11/2026 ghi 53/53 kiểm thử backend, 10/10 kịch bản trình duyệt đạt; 7 lỗi đã sửa.** Hỏi mới 12 tình huống/16 lượt đạt điều kiện chức năng, nhưng rà soát nội dung còn 6 tình huống cần xem lại. Đây là kết quả đã lưu, không phải lần chạy lại khi sửa tài liệu. Không coi điểm AI hoặc kết quả chức năng là độ chính xác được chuyên gia xác minh.

## Thư mục

| Vị trí | Nội dung |
| --- | --- |
| Các tệp Word/PDF/Excel ở đây | Bản hoàn chỉnh để đọc và nộp. |
| `results/` | Kết quả chạy mới dạng JSON/TXT, trước/sau sửa lỗi và nhận xét AI. |
| `evidence/` | Ảnh giao diện thật, sơ đồ, biểu đồ, môi trường, kiểm tra tài liệu. |
| `history/` | Hồ sơ kỹ thuật và phép đo cũ, không thay kết quả hiện hành. |
| `tools/` | Mã tạo tài liệu, kiểm tra giao diện, hoàn thiện Word và đóng gói. |
| `releases/` | [ZIP hồ sơ nộp đầy đủ](releases/AI_4GYM_HO_SO_NOP_CT07PM.zip), đã quản lý trên Git cùng các tài liệu riêng lẻ. |
| `evaluation_results.jsonl` | 193 bản ghi đánh giá được bàn giao từ remote, giữ nguyên nội dung. |
| `AI-4GYM_train_test_report.xlsx` | Excel train/test gắn với 193 bản ghi; giữ vị trí để tương thích các script đánh giá. |
| `submission_manifest.json` | SHA-256 các tệp trong bộ hồ sơ đóng gói. |

Các tên bằng chứng được ghi ngắn trong Word/PDF nằm tại `results/`. Vị trí đổi, kết quả chạy không bị viết lại. Hash của mã nguồn trong JSON xác định phiên bản đã được kiểm thử; commit nền không bao gồm các sửa lỗi local lúc chạy.

File xem thử PDF, cache và bản sao Word ban đầu không phải bằng chứng kiểm thử cần nộp. Có thể giữ bản sao riêng trong `.local/backups/`, nhưng thư mục này không được đưa lên Git và không có sẵn sau khi clone. Môi trường `.venv`, `node_modules`, `.env`, chỉ mục Chroma và build frontend cũng không track.

Có thể tải ZIP trực tiếp trong `releases/` hoặc tạo lại bằng `tools/package_submission.py` từ các hiện vật đã lưu (cần thêm thư viện trong `requirements-report.txt`). Bản ZIP không chứa `.env`, tài khoản thật, môi trường Python/Node hoặc chỉ mục local.

Lệnh đóng gói và phạm vi của ZIP được ghi trong [tài liệu cấu trúc dự án](../docs/project-structure.md#chỉnh-sửa-và-đóng-gói-tài-liệu). Chỉnh nội dung trong Word hiện hành rồi xuất lại PDF; công cụ `build_submission.py` sinh lại toàn bộ tài liệu nên không dùng để giữ các chỉnh sửa theo form trường.
