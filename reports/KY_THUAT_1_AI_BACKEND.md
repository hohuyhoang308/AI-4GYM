# Báo cáo Bàn giao Kỹ thuật 1 — AI Chatbot & Backend

**Dự án:** AI-4GYM — Chatbot hỗ trợ người mới tập Gym / Fitness  
**Vai trò phụ trách:** Kỹ thuật 1 — AI Chatbot & Backend (Logic trả lời, Ngữ cảnh hội thoại, Cá nhân hóa & Tích hợp tri thức)  
**Thời gian hoàn thành:** 13/11/2026  
**File bằng chứng thực nghiệm:** [ky_thuat_1_evidence.json](file:///f:/download/baitap/AI/AI-4GYM/reports/ky_thuat_1_evidence.json)  

---

## 1. Khắc phục lỗi Chatbot trả lời thiếu nội dung (Kỹ thuật bài tập & Câu 214)

### 1.1. Nguyên nhân kỹ thuật
- `SYSTEM_PROMPT` cũ chỉ yêu cầu "ngắn gọn", chưa định hình cấu trúc bắt buộc cho câu hỏi kỹ thuật bài tập.
- `curated/exercises.json` trước đây chỉ có 10 bài tập, thiếu bài `bent-over-row` (chèo thuyền gập người với tạ đơn). Khi gặp câu `qa-214`, chatbot chỉ truy xuất các mảnh dữ liệu chung chung và chỉ mô tả tư thế chuẩn bị: *"Đứng với tạ ở tay trái, đặt ghế dài hoặc ghế tựa ở bên phải..."* rồi dừng lại, hoàn toàn thiếu pha kéo tạ, nhịp thở, siết bả vai và lỗi sai thường gặp.
- Giới hạn sinh token (`num_predict=400`) có thể ngắt câu trả lời giữa chừng khi model trình bày chi tiết.

### 1.2. Giải pháp triển khai
1. **Bổ sung bài tập chuẩn vào kho tri thức**: Thêm bài `bent-over-row` vào [BE/data/curated/exercises.json](file:///f:/download/baitap/AI/AI-4GYM/BE/data/curated/exercises.json) với đầy đủ 4 phần:
   - *Tư thế chuẩn bị (Setup)* với ghế dài và tạ đơn.
   - *Pha kéo tạ (Execution)*: Gập cùi chỏ, ép chặt hai bả vai, kéo tạ về phía mạn sườn/xương sườn, thở ra khi kéo.
   - *Điểm dừng và hạ tạ*: Dừng 1 nhịp ở đỉnh để siết cơ lưng, hít vào hạ tạ từ từ có kiểm soát.
   - *Lỗi sai cần tránh (Common mistakes)*: Cong lưng, vặn người, dùng đà giật tạ, xòe khuỷu tay, thả tạ rơi tự do.
   - *Đổi bên*: Thực hiện từng bên và đổi sang tay/chân đối diện.
2. **Nâng cấp System Prompt**: Ép cấu trúc bắt buộc 4 phần đối với mọi câu hỏi hướng dẫn bài tập, cấm tuyệt đối việc chỉ mô tả tư thế chuẩn bị rồi dừng lại.
3. **Đồng bộ chỉ mục RAG**: Chạy lại `ingest.py` cập nhật chỉ mục Chroma lên 783 tài liệu.
4. **Tăng `num_predict`** lên 600 tokens trong `ChatService`.

---

## 2. Nâng cấp Hội thoại nhiều lượt (Multi-turn Context & State Refinement)

### 2.1. Vấn đề phát hiện
- Trước đây, khi người dùng đưa ra câu nói phụ thuộc như *"Tôi không có dụng cụ"*, `in_scope` trả về `False` (bị coi là ngoài phạm vi) và chatbot ném ra thông báo từ chối chung chung.
- Cơ chế hội thoại chưa nhận biết được việc người dùng muốn **điều chỉnh ràng buộc trên lịch tập vừa đưa ra ở lượt trước** (Constraint Refinement).

### 2.2. Giải pháp triển khai
1. Mở rộng `in_scope` trong [BE/app/services/scope.py](file:///f:/download/baitap/AI/AI-4GYM/BE/app/services/scope.py): nhận diện các câu bổ sung điều kiện khi có ngữ cảnh (`has_context=True`) như: `"khong co dung cu"`, `"khong dung cu"`, `"tai nha"`, `"o nha"`, `"dau goi"`, `"thay the"`.
2. Bổ sung cơ chế **State Inheritance & Adaptive Refinement**:
   - Nếu lượt trước đang thảo luận về lịch tập hoặc tập chân (`target_muscle="chan"`), lượt này người dùng nói *"Tôi không có dụng cụ"*, chatbot giữ nguyên mục tiêu tập chân nhưng hoán đổi toàn bộ các bài dùng máy sang bài tập Bodyweight thuần túy (`Squat trọng lượng cơ thể`, `Nâng hông Glute Bridge`, `Plank`).
   - Nếu lượt kế tiếp người dùng nói *"Tôi bị đau khớp gối thì sao?"*, chatbot ghi nhận hạn chế `"knee"`, lập tức loại bỏ bài Squat/Leg press và ưu tiên bài giảm áp lực lên gối (`Glute Bridge`, `Plank`), kèm lời khuyên dừng động tác gây đau và đi khám bác sĩ.

---

## 3. Cá nhân hóa lịch tập & Hỏi bổ sung chủ động (Personalization)

### 3.1. Động cơ sinh lịch tập đa tiêu chí ([plans.py](file:///f:/download/baitap/AI/AI-4GYM/BE/app/services/plans.py))
Hàm `make_plan` được nâng cấp hỗ trợ đầy đủ 5 tiêu chí:
1. `days`: Số ngày tập (1–6 buổi/tuần).
2. `equipment`:
   - `gym`: Máy tập, tạ đòn, cáp (`Leg press`, `Chest press`, `Lat pulldown`, `Seated row`...).
   - `home_bodyweight`: 100% trọng lượng cơ thể (`Bodyweight squat`, `Bent-knee push-up`, `Glute bridge`, `Front plank`).
   - `home_dumbbell`: Tận dụng tạ đơn tại nhà (`Bent-over row`, `Shoulder press`, `Bodyweight squat`...).
3. `goal`:
   - `giam_mo`: Bổ sung hướng dẫn kết hợp tối thiểu 150 phút aerobic/cardio vừa phải mỗi tuần.
   - `tang_co`: Bổ sung nguyên tắc quá tải tiến triển (progressive overload) và dinh dưỡng protein.
4. `limitations`:
   - `knee`: Loại bỏ `leg-press` và `squat` sâu, thay bằng `glute-bridge` và `front-plank`.
   - `lower_back`: Loại bỏ động tác cúi gập nặng, thay bằng bài có điểm tựa và siết core.
5. `target_muscle`: Lên lịch tập trung vào từng nhóm cơ cụ thể (ví dụ: Chân, Lưng, Ngực...).

### 3.2. Cơ chế hỏi bổ sung chủ động (Clarifying Questions)
Khi người dùng đưa ra yêu cầu chung chung như *"Tư vấn lịch tập cho tôi"* hoặc *"Lên lịch tập"*, chatbot không đoán mò mà chủ động hỏi lại **4 thông tin cốt lõi**:
1. Số buổi/tuần và thời lượng mỗi buổi.
2. Địa điểm & Dụng cụ (phòng gym hay tại nhà không dụng cụ/có tạ đơn).
3. Mục tiêu chính (giảm mỡ, tăng cơ hay rèn luyện sức khỏe).
4. Hạn chế thể chất / chấn thương tiền sử.

---

## 4. Minh chứng Trước / Sau (Before vs After)

| ID | Câu hỏi | Trạng thái trước khi sửa | Trạng thái sau khi sửa |
| :--- | :--- | :--- | :--- |
| **qa-214** | *Làm thế nào để thực hiện bài tập chèo thuyền gập người (bent-over row)?* | **Thiếu nội dung (Điểm 1/2):** Chỉ mô tả tư thế chuẩn bị trên ghế, dừng lại không hướng dẫn kéo tạ. | **Đầy đủ 4 phần (Đạt chuẩn):**<br>1. Setup trên ghế với tạ đơn.<br>2. Pha kéo tạ sát sườn, siết bả vai, thở ra, dừng 1 nhịp ở đỉnh, hạ tạ kiểm soát.<br>3. Lỗi sai: cong lưng, giật người, xòe khuỷu tay, thả tạ rơi.<br>4. Lưu ý an toàn và đổi bên. |
| **qa-90** | *Trẻ em và thanh thiếu niên nên vận động thể chất ở mức độ như thế nào?* | **Sai khuyến nghị (Điểm 1/2):** Trả lời nhầm sang mức 150 phút/tuần của người lớn. | **Chính xác theo WHO/CDC:** Ít nhất **60 phút mỗi ngày** cường độ vừa đến mạnh (aerobic, cơ, xương), hạn chế thời gian ngồi trước màn hình. |
| **qa-371** | *Tôi có thể tập thể dục trong thời gian nhịn ăn (ví dụ: tháng Ramadan) không?* | **Bị từ chối (Điểm 0/2):** Báo câu hỏi ngoài phạm vi Gym/Fitness. | **Trả lời chuẩn y khoa & an toàn:** Có thể tập ở mức nhẹ–vừa phải, chú ý bù nước trong giờ ăn, dừng khi chóng mặt, tham khảo bác sĩ. |

---

## 5. Minh chứng Hội thoại nhiều lượt (Multi-turn Evidence)

```text
[Turn 1] User: "Tôi muốn tập chân tại nhà."
Bot: Lịch 3 buổi/tuần — Toàn thân (Tại nhà - Không dụng cụ):
- Thứ Hai: Toàn thân A (Chân) — Squat trọng lượng cơ thể, Nâng hông.
- Thứ Tư: Toàn thân B (Chân) — Squat trọng lượng cơ thể, Nâng hông.
- Thứ Sáu: Toàn thân A (Chân) — Squat trọng lượng cơ thể, Nâng hông.
(Ghi chú: Thiết kế bằng trọng lượng cơ thể Bodyweight, không cần dụng cụ).

[Turn 2] User: "Tôi không có dụng cụ."
Bot: Mình đã điều chỉnh lịch tập theo yêu cầu của bạn (100% sử dụng trọng lượng cơ thể Bodyweight tại nhà):
- Tiếp tục duy trì các bài tập Bodyweight Squat, Glute Bridge, không dùng bất kỳ tạ hay máy tập nào.

[Turn 3] User: "Tôi bị đau khớp gối thì sao?"
Bot: Mình đã ghi nhận tình trạng đau khớp gối của bạn và điều chỉnh các bài tập an toàn (giảm áp lực lên gối, ưu tiên Nâng hông và Plank):
- Thứ Hai: Toàn thân A (Chân) — Nâng hông, Plank cẳng tay.
- Thứ Tư: Toàn thân B (Chân) — Nâng hông, Plank cẳng tay.
- Thứ Sáu: Toàn thân A (Chân) — Nâng hông, Plank cẳng tay.
Lưu ý khớp gối: Đã loại bỏ squat sâu/đạp chân, ưu tiên Nâng hông (Glute Bridge) và Plank; khuyên dừng nếu đau.
```

---

## 6. Hướng dẫn chạy kiểm chứng độc lập

Tại thư mục `BE/`:
```powershell
# 1. Chạy bộ unit tests (21 tests bao gồm flow multi-turn và personalization)
.\.venv\Scripts\python.exe -m unittest discover -s tests

# 2. Chạy script kiểm chứng toàn diện Kỹ thuật 1 (xuất JSON bằng chứng thực tế)
.\.venv\Scripts\python.exe -m app.scripts.verify_kythuat1
```
