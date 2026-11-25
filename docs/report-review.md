# Biên bản rà soát báo cáo và tài liệu

Ngày đối chiếu: **25/11/2026**. Phần việc của **Nguyên** là báo cáo và docs; **Anh Trần** phụ trách dọn workspace, **Khoa** phụ trách kiểm thử phần mềm.

## Phạm vi đã hoàn tất

| Hạng mục | Nội dung đã rà và sửa |
| --- | --- |
| [Tiểu luận Word](../reports/Tieu_luan_AI_4GYM_CT07PM.docx) / [PDF](../reports/Tieu_luan_AI_4GYM_CT07PM.pdf) | Giữ nền bản của nhóm; áp dụng form trường, bỏ dòng Khóa, cập nhật nội dung, số liệu, ví dụ, mục lục và danh mục bảng/hình. |
| [Báo cáo kiểm thử Word](../reports/Bao_cao_kiem_thu_AI_4GYM.docx) / [PDF](../reports/Bao_cao_kiem_thu_AI_4GYM.pdf) | Đối chiếu kết luận với log; sửa trích dẫn ROUGE, bổ sung tài liệu tham khảo và xóa dòng chữ đầu trang theo yêu cầu; giữ nội dung và số trang. |
| [README](../README.md) | Đồng bộ chức năng, dữ liệu, trạng thái đánh giá và cách phân biệt kết quả đã lưu với lần chạy mới. |
| [Cài đặt](setup.md) | Sửa đường dẫn mở dự án, cấu hình MySQL, số bài tập, trạng thái đánh giá, nguồn dữ liệu và điều kiện chạy các ca kiểm thử. |
| [Cấu trúc dự án](project-structure.md) | Phân biệt train/test với hiện vật báo cáo; ghi rõ tác động của công cụ tạo lại tài liệu và cách đóng gói. |
| [Danh mục hồ sơ](../reports/HO_SO_NOP.md) và [ZIP](../reports/releases/AI_4GYM_HO_SO_NOP_CT07PM.zip) | Đồng bộ Word/PDF, tài liệu, manifest SHA-256 và nội dung ZIP. |

## Các điểm đối chiếu

- Dữ liệu có 965 cặp hỏi–đáp, chia 772 train/corpus và 193 test; 11 bài tập bổ sung tạo tổng kỳ vọng 783 tài liệu. Test không nằm trong corpus.
- JSONL và Excel bàn giao có 193 kết quả, phân bố điểm 2/1/0 là 132/56/5; 154 dòng judge v2, 39 dòng v3. Nhãn tay là 187 đạt/6 không đạt. Nguồn đối chiếu: [hồ sơ 193 câu](../reports/evaluation_results.jsonl), [Excel](../reports/AI-4GYM_train_test_report.xlsx), [manifest phép chia](../BE/data/processed/split_manifest.json).
- Log phần mềm ghi 53/53 phương thức backend và 10/10 kịch bản Edge đạt; bảy ca hồi quy thuộc tổng backend. Hash mã nguồn được đối chiếu với [log phần mềm](../reports/results/software_test_results.json).
- [Bộ hỏi mới](../reports/results/chatbot_ai_review.json) có 12 tình huống/16 lượt; 12 tình huống đạt điều kiện chức năng nhưng [rà soát bổ sung](../reports/results/independent_ai_review.json) còn sáu cờ nội dung. Năm lượt RAG có thời gian ChatService trung bình 85,205 giây; không trộn với trường thời gian không đồng nhất của 193 bản ghi cũ.
- Các số liệu là kết quả trong bằng chứng đã lưu. Điểm AI, nhãn tay và kết quả chức năng không được gọi là độ chính xác hoặc mức an toàn đã được chuyên gia xác minh.

## Kiểm tra tài liệu và bàn giao

Word/PDF được kiểm tra nội dung, nguồn trích dẫn, mục lục và bố cục; các đường dẫn nội bộ trong tài liệu hiện hành được kiểm tra tồn tại. ZIP và manifest phải khớp hash của từng hiện vật sau lần chỉnh sửa cuối. Thư mục `reports/history/` là hồ sơ lịch sử, giữ số liệu theo ngày ghi trong từng tệp.

Lượt rà soát docs này không chạy lại backend, trình duyệt, MySQL hoặc Ollama và không thay dữ liệu hay kết quả kiểm thử. Khoa xác nhận kết quả chạy phần mềm của đợt bàn giao; nếu có mã nguồn, dữ liệu hoặc log mới thì cập nhật báo cáo theo bằng chứng của đợt đó. Các hạn chế nội dung và bộ chấm đã nêu trong báo cáo được giữ để đối chiếu.

## Kết quả rà soát cuối ngày 25/11/2026

- Tiểu luận có 41 trang, báo cáo kiểm thử có 12 trang; đã xem lại toàn bộ 53 trang PDF, không phát hiện trang trắng hoặc lỗi bố cục cần sửa.
- Tiểu luận có ba trường tự động: mục lục, danh mục bảng và danh mục hình; báo cáo kiểm thử có một mục lục tự động. Đã đối chiếu đủ 74 mục và số trang với vị trí nội dung trong PDF: 60 mục ở tiểu luận, 14 mục ở báo cáo kiểm thử; không có đích liên kết thiếu hoặc số trang sai.
- Nội dung các đoạn Word ngoài mục lục khớp văn bản PDF sau khi bỏ số trang, khoảng trắng và khác biệt trích xuất dấu câu. Không còn nhận xét hoặc thay đổi đang chờ chấp nhận trong hai bản Word.
- Đã kiểm tra 50 đường dẫn nội bộ trong bảy tài liệu Markdown; đối chiếu sáu hash mã nguồn trong log kiểm thử với mã hiện tại; đọc lại 193 dòng kết quả và nhãn tay trong Excel. Số liệu khớp báo cáo; hai workbook không có ô mang kiểu lỗi Excel.
- ZIP có 58 mục, gồm 57 tệp có SHA-256 trong manifest và chính manifest. Nội dung trong ZIP khớp từng tệp hiện hành; kiểm tra giải nén không có lỗi.

Trong phạm vi báo cáo và docs hiện có, chưa phát hiện hạng mục bắt buộc còn thiếu. Phiên bản xuất bản được xác định bằng commit trong lịch sử Git. Trước khi nộp, nhóm chốt thông tin bìa và xác nhận đây là phiên bản bàn giao; nếu Khoa cung cấp kết quả kiểm thử mới hoặc mã nguồn thay đổi thì Nguyên cập nhật lại kết quả, Word/PDF và ZIP theo bằng chứng mới.
