"""Script xuất ma trận kiểm thử 20 ca mở rộng ra file Excel."""

from pathlib import Path
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def create_extended_test_matrix():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "20 Ca Kiem Thu Mo Rong"

    # Title
    ws.merge_cells("A1:G1")
    ws["A1"] = "BỘ CA KIỂM THỬ PHẦN MỀM MỞ RỘNG (20 TEST CASES) - DỰ ÁN AI-4GYM"
    ws["A1"].font = Font(name="Segoe UI", size=14, bold=True, color="1F4E78")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("A2:G2")
    ws["A2"] = "Môn: Kiểm thử phần mềm / Công nghệ phần mềm | Phương pháp: BVA, EP, Decision Table, State Transition & Security"
    ws["A2"].font = Font(name="Segoe UI", size=10, italic=True, color="595959")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

    headers = [
        "Mã ca",
        "Nhóm kỹ thuật",
        "Tên ca kiểm thử & Mô tả",
        "Điều kiện tiên quyết",
        "Dữ liệu đầu vào & Thao tác",
        "Kết quả mong đợi",
        "Trạng thái",
    ]

    ws.append([])  # blank row 3
    ws.append(headers)  # row 4

    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    pass_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    pass_font = Font(name="Segoe UI", size=10, bold=True, color="375623")

    test_cases = [
        # BVA
        (
            "TC-BVA-01",
            "Phân tích giá trị biên (BVA)",
            "Biên số ngày tạo lịch days=1 (min) và days=6 (max)",
            "API /plans sẵn sàng",
            "GET /plans?days=1 và GET /plans?days=6",
            "Mã 200 OK; days=1 có 1 ngày (Toàn thân), days=6 có 6 ngày (Push/Pull/Legs)",
            "PASS",
        ),
        (
            "TC-BVA-02",
            "Phân tích giá trị biên (BVA)",
            "Biên ngoài ngưỡng ngày days=0, 7, -1, 100",
            "API /plans sẵn sàng",
            "GET /plans với days in [0, 7, -1, 100]",
            "Mã 422 Unprocessable Entity, chặn giá trị ngoài khoảng [1, 6]",
            "PASS",
        ),
        (
            "TC-BVA-03",
            "Phân tích giá trị biên (BVA)",
            "Biên độ dài tin nhắn chat (1, 2, 1000, 1001 ký tự)",
            "API /chat sẵn sàng",
            "POST /chat với chuỗi dài 1, 2, 1000, 1001 ký tự",
            "1 và 1001 ký tự nhận 422; 2 và 1000 ký tự nhận 200 OK",
            "PASS",
        ),
        (
            "TC-BVA-04",
            "Phân tích giá trị biên (BVA)",
            "Biên độ dài tên hiển thị đăng ký (1, 2, 80, 81 ký tự)",
            "API /auth/register sẵn sàng",
            "POST /auth/register với display_name dài 1, 2, 80, 81 ký tự",
            "1 và 81 ký tự trả 422; 2 và 80 ký tự đăng ký thành công (201)",
            "PASS",
        ),
        (
            "TC-BVA-05",
            "Phân tích giá trị biên (BVA)",
            "Biên độ dài mật khẩu đăng ký (7, 8, 128, 129 ký tự)",
            "API /auth/register sẵn sàng",
            "POST /auth/register với password dài 7, 8, 128, 129 ký tự",
            "7 và 129 ký tự trả 422; 8 và 128 ký tự đăng ký thành công (201)",
            "PASS",
        ),
        # EP
        (
            "TC-EP-01",
            "Phân vùng tương đương (EP)",
            "Lọc bài tập theo nhóm cơ hợp lệ",
            "Danh mục bài tập load_exercises sẵn sàng",
            "GET /exercises?muscle={nguc, lung, chan, vai, tay}",
            "Mã 200 OK; danh sách trả về đúng các bài có nhóm cơ truy vấn",
            "PASS",
        ),
        (
            "TC-EP-02",
            "Phân vùng tương đương (EP)",
            "Lọc bài tập với chuỗi chưa chuẩn hóa (hoa/thường, khoảng trắng, không dấu)",
            "Danh mục bài tập sẵn sàng",
            "GET /exercises?muscle='  NGỰC  ' và muscle='nguc'",
            "Hệ thống tự chuẩn hóa (trim, casefold, bỏ dấu), kết quả khớp 100% với ngực",
            "PASS",
        ),
        (
            "TC-EP-03",
            "Phân vùng tương đương (EP)",
            "Lọc bài tập với nhóm cơ không tồn tại",
            "Danh mục bài tập sẵn sàng",
            "GET /exercises?muscle={dau_long, tim, 12345}",
            "Mã 200 OK, trả về mảng rỗng [], không bị lỗi crash 500",
            "PASS",
        ),
        (
            "TC-EP-04",
            "Phân vùng tương đương (EP)",
            "Phân vùng định dạng Email hợp lệ và không hợp lệ",
            "API /auth/register sẵn sàng",
            "Email chuẩn (subdomain, plus tag) vs email sai cú pháp (user@, space)",
            "Email đúng trả 201; email sai cấu trúc trả 422 Unprocessable Entity",
            "PASS",
        ),
        (
            "TC-EP-05",
            "Phân vùng tương đương (EP)",
            "Phân vùng ký tự đặc biệt: Tiếng Việt có dấu và Emoji",
            "DB lưu trữ và API auth/chat sẵn sàng",
            "Tên 'Nguyễn Văn Tập Gym 💪🏋️' và chat 'Tập squat thế nào cho đùi khỏe? 🔥💪'",
            "Dữ liệu lưu và đọc lại từ /auth/me và lịch sử chat nguyên vẹn, không lỗi font UTF-8",
            "PASS",
        ),
        # Decision Table
        (
            "TC-DT-01",
            "Bảng quyết định (Decision Table)",
            "Tổ hợp: Không dụng cụ + Tăng cơ + Đau gối",
            "make_plan logic sẵn sàng",
            "days=3, equipment=home_bodyweight, goal=tang_co, limitations=[knee]",
            "Lịch đổi sang bài bodyweight, loại squat/đạp chân, hướng dẫn quá tải tiến triển & lưu ý gối",
            "PASS",
        ),
        (
            "TC-DT-02",
            "Bảng quyết định (Decision Table)",
            "Tổ hợp: Tạ đơn + Giảm mỡ",
            "make_plan logic sẵn sàng",
            "days=3, equipment=home_dumbbell, goal=giam_mo",
            "Lịch đổi bài máy sang tạ đơn (bent-over-row), kèm khuyến cáo 150 phút aerobic",
            "PASS",
        ),
        (
            "TC-DT-03",
            "Bảng quyết định (Decision Table)",
            "Tổ hợp: Phòng Gym + Đa chấn thương (đau gối AND đau lưng dưới)",
            "make_plan logic sẵn sàng",
            "days=4, limitations=[knee, lower_back]",
            "Loại bỏ đồng thời 4 bài nguy cơ (squat, leg-press, seated-row, bent-over-row); đủ 2 lưu ý y tế",
            "PASS",
        ),
        (
            "TC-DT-04",
            "Bảng quyết định (Decision Table)",
            "Tổ hợp: Chuyên biệt nhóm cơ chân + Không dụng cụ",
            "make_plan logic sẵn sàng",
            "days=2, equipment=home_bodyweight, target_muscle=chan",
            "Tất cả các ngày đều định hướng cơ chân; chỉ dùng bài bodyweight (glute-bridge)",
            "PASS",
        ),
        (
            "TC-DT-05",
            "Bảng quyết định (Decision Table)",
            "Cân bằng nhóm cơ chu kỳ Đẩy - Kéo - Chân (PPL 6 ngày)",
            "make_plan logic sẵn sàng",
            "days=6 (Push/Pull/Legs)",
            "Xác nhận đúng chu kỳ tuần hoàn Đẩy -> Kéo -> Chân 2 vòng; không trùng lặp phân bổ",
            "PASS",
        ),
        # State Transition & Security
        (
            "TC-ST-01",
            "Chuyển trạng thái & An toàn",
            "Vòng đời hội thoại đầy đủ (Tạo -> Chat -> Đổi tên -> Xóa)",
            "DB và API hội thoại sẵn sàng",
            "POST /chat -> PATCH /conversations/{id} -> GET -> DELETE",
            "Mã 200/204; hội thoại đổi tên đúng; khi xóa thì toàn bộ tin nhắn liên quan bị xóa sạch",
            "PASS",
        ),
        (
            "TC-ST-02",
            "Chuyển trạng thái & An toàn",
            "Chuyển trạng thái khách sang thành viên đăng nhập",
            "DB và API auth/chat sẵn sàng",
            "Khách chat (không lưu DB) -> Đăng ký -> Thành viên chat (lưu DB)",
            "Khách có conversation_id=None (0 bản ghi DB); thành viên có 1 hội thoại và 2 tin nhắn",
            "PASS",
        ),
        (
            "TC-SEC-01",
            "Chuyển trạng thái & An toàn",
            "Phòng chống XSS / Script Injection qua Input người dùng",
            "API auth và chat sẵn sàng",
            "Payload <script>alert(1)</script><img src=x onerror=alert(1)> vào name, message, title",
            "Lưu trữ an toàn, API trả về text nguyên bản, không làm sập serializer hay lỗi 500",
            "PASS",
        ),
        (
            "TC-SEC-02",
            "Chuyển trạng thái & An toàn",
            "Kiểm soát truy cập ngang (IDOR) giữa User A và User B",
            "Hai tài khoản A và B độc lập",
            "User B cố tình GET/PATCH/DELETE hoặc gửi chat vào conversation_id của User A",
            "Tất cả request trái phép của User B đều nhận 404 Not Found, bảo vệ tuyệt đối dữ liệu User A",
            "PASS",
        ),
        (
            "TC-SEC-03",
            "Chuyển trạng thái & An toàn",
            "Chống Replay Attack và Duplicate Request",
            "API /chat và bảng chat_request_records",
            "Gửi 2 request cùng request_id; thử đổi payload ở request sau",
            "Request trùng trả về kết quả cũ mà không gọi lại AI; đổi payload trả 409 Conflict",
            "PASS",
        ),
    ]

    for row_idx, tc in enumerate(test_cases, start=5):
        ws.append(tc)
        for col_idx in range(1, 8):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = Font(name="Segoe UI", size=10)
            cell.border = thin_border
            if col_idx in (1, 7):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(vertical="center", wrap_text=True)

            if col_idx == 7:  # Status
                cell.fill = pass_fill
                cell.font = pass_font

    # Format header row
    for col_idx in range(1, 8):
        cell = ws.cell(row=4, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align
        cell.border = thin_border

    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 20
    ws.row_dimensions[4].height = 28
    for r in range(5, 25):
        ws.row_dimensions[r].height = 35

    col_widths = {1: 14, 2: 26, 3: 35, 4: 25, 5: 38, 6: 45, 7: 12}
    for col, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width

    out_path = Path(__file__).resolve().parent.parent / "Bo_kiem_thu_phan_mem_mo_rong_20_ca.xlsx"
    wb.save(out_path)
    print("Saved to:", out_path)


if __name__ == "__main__":
    create_extended_test_matrix()
