"""Build the Vietnamese submission documents and test workbook from real evidence.

Run only after software_test_results, browser_test_results and chatbot_ai_review
contain completed results. This script does not invent or overwrite test outcomes.
"""

from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.chart import BarChart, Reference
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from case_catalog import describe


PROJECT = Path(__file__).resolve().parents[2]
REPORTS = PROJECT / "reports"
EVIDENCE = REPORTS / "evidence"
RESULTS = REPORTS / "results"
NAVY, GREEN, GRAY = "183C32", "38734A", "52625B"
DATE = "25/11/2026"


def read(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def field(paragraph, instruction, placeholder=""):
    run = paragraph.add_run()
    start, code, sep, text, end = (OxmlElement(tag) for tag in
        ("w:fldChar", "w:instrText", "w:fldChar", "w:t", "w:fldChar"))
    start.set(qn("w:fldCharType"), "begin")
    code.set(qn("xml:space"), "preserve")
    code.text = " " + instruction + " "
    sep.set(qn("w:fldCharType"), "separate")
    text.text = placeholder
    end.set(qn("w:fldCharType"), "end")
    for node in (start, code, sep, text, end):
        run._r.append(node)


def paragraph(doc, text, style=None):
    p = doc.add_paragraph(text, style)
    if style is None:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(.8)
    return p


def prose(doc, text):
    for block in text.strip().split("\n\n"):
        paragraph(doc, " ".join(block.splitlines()))


def table(doc, caption, headers, rows, widths=None):
    if caption:
        p = doc.add_paragraph(caption, "Caption")
        p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    t.autofit = False
    for cell, label in zip(t.rows[0].cells, headers):
        cell.text = str(label)
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), NAVY)
        cell._tc.get_or_add_tcPr().append(shading)
        for r in cell.paragraphs[0].runs:
            r.bold = True
            r.font.color.rgb = RGBColor.from_string("FFFFFF")
    repeat = OxmlElement("w:tblHeader")
    t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        cells = t.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = str(value if value is not None else "—")
    for row in t.rows:
        prevent = OxmlElement("w:cantSplit")
        row._tr.get_or_add_trPr().append(prevent)
        for i, cell in enumerate(row.cells):
            if widths:
                cell.width = Cm(widths[i])
            for p in cell.paragraphs:
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing = 1.08
                for run in p.runs:
                    run.font.size = Pt(10.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def image(doc, filename, caption, width=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(EVIDENCE / filename), width=Cm(width))
    p = doc.add_paragraph(caption, "Caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def chapter(doc, title):
    p = doc.add_heading(title, 1)
    p.paragraph_format.page_break_before = True


def make_document(title, subtitle):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin, sec.bottom_margin = Cm(2.3), Cm(2.3)
    sec.left_margin, sec.right_margin = Cm(3), Cm(2)
    sec.header_distance, sec.footer_distance = Cm(1.1), Cm(1.1)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(13)
    normal.paragraph_format.line_spacing = 1.3
    normal.paragraph_format.space_after = Pt(6)
    for name, size in (("Title", 20), ("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 13)):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string("000000")
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(7)
        style.paragraph_format.keep_with_next = True
    doc.styles["Caption"].font.name = "Times New Roman"
    doc.styles["Caption"].font.size = Pt(11)
    doc.styles["Caption"].font.italic = True
    doc.styles["Caption"].font.color.rgb = RGBColor.from_string("333333")
    doc.styles["Caption"].paragraph_format.space_after = Pt(8)
    sec.different_first_page_header_footer = True
    header = sec.header.paragraphs[0]
    header.text = "AI-4GYM  |  CT07PM — Các ứng dụng trong AI"
    header.runs[0].font.size = Pt(9)
    header.runs[0].font.color.rgb = RGBColor.from_string(GRAY)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field(footer, "PAGE")
    doc.core_properties.title = title
    doc.core_properties.subject = subtitle
    doc.core_properties.author = "Nhóm AI-4GYM — CT07PM"
    doc.core_properties.keywords = "AI-4GYM, RAG, chatbot, kiểm thử phần mềm, CT07PM"
    for line in ("BỘ GIÁO DỤC VÀ ĐÀO TẠO", "TRƯỜNG ĐẠI HỌC HÙNG VƯƠNG TP. HỒ CHÍ MINH"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(line).bold = True
    doc.add_paragraph("____________________").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("\n")
    p = doc.add_paragraph(title, "Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("XÂY DỰNG CHATBOT HỖ TRỢ TRA CỨU BÀI TẬP\nVÀ GỢI Ý LỊCH TẬP GYM", "Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in p.runs:
        run.font.size = Pt(16)
    p = doc.add_paragraph(subtitle)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("\n")
    for line in ("Môn học: Các ứng dụng trong AI (2610412601)", "Giảng viên: NGUYỄN THANH TIẾN", "Lớp: CT07PM"):
        paragraph(doc, line)
    table(doc, None, ["Sinh viên thực hiện", "Mã số sinh viên"], [
        ("NGUYỄN HOÀNG ANH KHOA", "2305CT0458"), ("TRẦN TRUNG NGUYÊN", "2305CT0351"),
        ("TRẦN TUẤN ANH", "2305CT0418"), ("HỒ HUY HOÀNG", "2305CT0393")], [10, 6])
    doc.add_paragraph("\nTHÀNH PHỐ HỒ CHÍ MINH, THÁNG 11 NĂM 2026").alignment = WD_ALIGN_PARAGRAPH.CENTER
    return doc


def toc(doc):
    p = doc.add_paragraph("MỤC LỤC", "Title")
    p.paragraph_format.page_break_before = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field(doc.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u', "Mục lục được cập nhật theo các tiêu đề của báo cáo.")


def diagrams(scores):
    EVIDENCE.mkdir(exist_ok=True)
    font = lambda size: ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)

    def draw_diagram(name, boxes, arrows, size=(1800, 950)):
        im = Image.new("RGB", size, "white")
        d = ImageDraw.Draw(im)
        for x1, y1, x2, y2, label in boxes:
            d.rounded_rectangle((x1, y1, x2, y2), radius=20, fill="#eef4ef", outline="#2d6542", width=4)
            lines = label.split("\n")
            heights = len(lines) * 42
            for i, line in enumerate(lines):
                d.text(((x1+x2)/2, (y1+y2)/2-heights/2+i*42), line, font=font(31), fill="#183c32", anchor="mt")
        for start, end, label in arrows:
            d.line([start, end], fill="#53665a", width=5)
            import math
            angle = math.atan2(end[1]-start[1], end[0]-start[0])
            points = [end, (end[0]-22*math.cos(angle-.4), end[1]-22*math.sin(angle-.4)),
                      (end[0]-22*math.cos(angle+.4), end[1]-22*math.sin(angle+.4))]
            d.polygon(points, fill="#53665a")
            if label:
                d.text(((start[0]+end[0])/2, (start[1]+end[1])/2-35), label, font=font(24), fill="#333333", anchor="mm")
        im.save(EVIDENCE / name)

    draw_diagram("architecture.png", [
        (60, 360, 390, 530, "React + TypeScript\nGiao diện chat"),
        (550, 360, 900, 530, "FastAPI\nXác thực / điều phối"),
        (550, 700, 900, 870, "MySQL\n5 bảng ứng dụng"),
        (1090, 360, 1470, 530, "ChatService\nPhạm vi / ngữ cảnh\nĐiều kiện người dùng"),
        (1630, 60, 2070, 230, "Chroma\nTruy xuất RAG"),
        (1630, 360, 2070, 530, "Ollama / Qwen\nSinh câu trả lời"),
        (1090, 700, 1730, 870, "make_plan + exercises.json\nLịch mẫu theo quy tắc"),
    ], [((390,445),(550,445),"HTTP"), ((725,530),(725,700),"Lịch sử"),
        ((900,445),(1090,445),"/chat"), ((1470,380),(1630,200),"Hỏi đáp"),
        ((1850,230),(1850,360),"Ngữ cảnh"), ((1280,530),(1280,700),"Yêu cầu lịch")], size=(2200, 950))
    draw_diagram("data_flow.png", [
        (70, 100, 480, 260, "Excel có nguồn theo câu\n965 cặp hỏi–đáp"),
        (650, 100, 1110, 260, "qa.json + chuẩn hóa\nSHA-256, seed 42"),
        (1300, 100, 1740, 260, "test.json — 193 câu\nGiữ riêng để đánh giá"),
        (650, 420, 1110, 580, "train.json — 772 câu\nKho truy xuất (80%)"),
        (70, 700, 480, 860, "exercises.json\n11 bài tập có cấu trúc"),
        (1300, 700, 1740, 860, "Ollama embedding / Chroma\n783 tài liệu"),
    ], [((480,180),(650,180),"Chuyển đổi"), ((1110,180),(1300,180),"20%"),
        ((880,260),(880,420),"80%"), ((1110,500),(1450,700),"Lập chỉ mục"),
        ((480,780),(1300,780),"Bổ sung kho tri thức")])

    prop = FontProperties(fname="C:/Windows/Fonts/arial.ttf")
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=180)
    labels = ["Đủ ý (2/2)", "Một phần (1/2)", "Sai / từ chối (0/2)"]
    values = [scores[2], scores[1], scores[0]]
    bars = ax.bar(labels, values, color=["#38734A", "#B78932", "#9D4D42"], width=.55)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x()+bar.get_width()/2, value+2, f"{value} ({value/193:.1%})", ha="center", fontproperties=prop)
    for tick in ax.get_xticklabels():
        tick.set_fontproperties(prop)
    ax.set_ylabel("Số câu", fontproperties=prop)
    ax.set_ylim(0, max(values)*1.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Hồ sơ bàn giao 193 câu — số liệu trước đợt sửa lỗi", fontproperties=prop, pad=15)
    fig.tight_layout()
    fig.savefig(EVIDENCE / "historical_scores.png", bbox_inches="tight")
    plt.close(fig)


BUGS = [
    ("RG-01", "Cao", "Lịch tại nhà chỉ có tạ đơn vẫn chứa máy đẩy vai/dây kháng lực.", "Đổi các bài đòi máy/dây sang bài phù hợp danh mục; nêu rõ cần ghế chắc chắn."),
    ("RG-02", "Trung bình", "Nhắc tạ đơn làm mất thông tin đang tập ở phòng gym.", "Ưu tiên địa điểm phòng gym trước loại tạ khi nhận diện dụng cụ."),
    ("RG-03", "Cao", "Điều kiện không dụng cụ cũ lấn điều kiện có tạ ở lượt mới.", "Đọc lịch sử từ gần đến xa và lấy giá trị mới nhất cho từng thuộc tính."),
    ("RG-04", "Cao", "Đổi dụng cụ không dựng lại lịch vừa tạo mà rơi sang nhánh RAG.", "Nhận diện lượt chỉnh điều kiện, dùng lại số buổi và dựng lại lịch theo quy tắc."),
    ("RG-05", "Trung bình", "Mục tiêu giảm mỡ cũ lấn mục tiêu tăng cơ mới.", "Kế thừa mục tiêu từ lượt gần nhất, bổ sung ca thay đổi qua nhiều lượt."),
    ("RG-06", "Cao", "Xuất Excel có thể bỏ qua lỗi chỉ mục; lời gọi vector_store chưa được import.", "Import đúng hàm và để lỗi không khớp chỉ mục được báo ra, không nuốt ngoại lệ."),
    ("RG-07", "Cao", "Lịch 4 buổi kèm đau vai vẫn có bài đẩy vai trên máy.", "Chặn nhánh cấp lịch cho đau vai, giải thích thiếu mẫu phù hợp và khuyên gặp chuyên gia y tế."),
]


def software_sections(doc, software, browser, before, after, number="4"):
    s, b = software["summary"], browser["summary"]
    doc.add_heading(f"{number}.1. Mục tiêu, phạm vi và tiêu chí đánh giá", 2)
    prose(doc, """
    Đợt kiểm thử tập trung xác nhận phần mềm đáp ứng các chức năng được mô tả trong mã nguồn và phát hiện sai lệch có thể tái hiện. Phần kiểm thử phần mềm xem xét API, tài khoản, quyền sở hữu hội thoại, vòng đời phiên, lưu dữ liệu, lịch theo quy tắc, ngữ cảnh, tính toàn vẹn dữ liệu và thao tác trình duyệt. Phần đánh giá nội dung chatbot được tách riêng vì một API trả HTTP 200 chưa chứng minh câu trả lời đúng về chuyên môn.

    Ca kiểm thử có đầu vào, hành vi mong đợi, kết quả thực tế và trạng thái đạt/không đạt. Các giá trị biên gồm lịch 1 và 6 buổi, số buổi 0 và 7, nội dung rỗng, chuỗi một ký tự, độ dài vượt 1000, tên hội thoại vượt 120 và UUID không hợp lệ. Kiểm tra phân quyền dùng hai tài khoản khác nhau. Mô hình và dữ liệu giả lập chỉ dùng trong những ca cần cô lập API hoặc logic; những ca đó được phân biệt với tích hợp MySQL/Ollama và trình duyệt thật.

    Tiêu chí cho chức năng có đầu ra xác định là khớp trạng thái HTTP, cấu trúc dữ liệu, quyền truy cập và tác động ghi dữ liệu đã định. Các ca có mô hình thật được kiểm tra thêm về nội dung phản hồi và nguồn. Tiêu chí nghiệm thu đợt này là không còn lỗi tái hiện trong các ca phần mềm đã thực thi; các giới hạn chưa được bao phủ phải được ghi nhận riêng, không đổi thành kết quả đạt.
    """)
    table(doc, f"Bảng {number}.1. Ma trận phạm vi kiểm thử", ["Nhóm", "Dữ liệu / điều kiện", "Bằng chứng"], [
        ("API và đầu vào", "Danh mục, lịch 1–6, dữ liệu sai và thiếu", "SW-01–SW-09"),
        ("Tài khoản và lịch sử", "Đăng ký, đăng nhập, khách, phân quyền, CRUD, lỗi model", "SW-10–SW-19; auth/security"),
        ("Logic chatbot", "Chặn lệnh chèn, thiếu chứng cứ, ưu tiên tên bài, cửa sổ lịch sử", "SW-20–SW-25; context/scope"),
        ("Hồi quy", "Dụng cụ, đổi mục tiêu, lịch nối tiếp, đau vai, chỉ mục", "RG-01–RG-07"),
        ("Dữ liệu và báo cáo", "Excel ↔ JSON ↔ manifest; ID/nội dung Chroma", "artifact_audit; index_content_audit"),
        ("Trình duyệt", "Desktop 1440×1000 và mobile 390×844, F5, bàn phím", "UI-01–UI-10"),
    ], [3.1, 7.4, 5.5])
    doc.add_heading(f"{number}.2. Môi trường và kết quả thực thi", 2)
    prose(doc, f"Ngày ghi nhận: {DATE}. Mã nguồn nền sau khi cập nhật remote là {software['git_commit'][:12]}; đợt sửa lỗi nằm trên thư mục làm việc sau commit này. Các tệp JSON bằng chứng lưu SHA-256 của các mô-đun thay đổi để nhận diện chính xác phiên bản đã kiểm tra. Môi trường là {software['platform']}, Python {software['python']}, MySQL local trong ServBay, Chroma local và Ollama. Kiểm thử HTTP cô lập dùng SQLite trong RAM; kiểm thử tích hợp riêng dùng MySQL thật.")
    table(doc, f"Bảng {number}.2. Tổng hợp kết quả phần mềm", ["Hạng mục", "Kết quả", "Diễn giải"], [
        ("Backend", f"{s['passed']}/{s['tests_run']} đạt", f"{s['failed']} fail; {s['errors']} error; {s['skipped']} bỏ qua."),
        ("Hồi quy trước sửa", f"{before['summary']['passed']}/7 đạt", "7 nhóm sai lệch được tái hiện bằng kiểm thử."),
        ("Hồi quy sau sửa", f"{after['summary']['passed']}/7 đạt", "Các ca này là một phần của tổng backend, không cộng trùng."),
        ("Trình duyệt Edge", f"{b['passed']}/{b['total']} đạt", f"{b['page_errors']} lỗi JavaScript ở pageerror."),
        ("Build frontend", software['frontend_build']['status'], "TypeScript và Vite build production."),
        ("Toàn vẹn hồ sơ", software['artifact_audit']['artifact_integrity'], "193 kết quả trong Excel khớp JSONL và dữ liệu nguồn."),
        ("Nội dung chỉ mục", software['index_content_audit']['status'], "Đối chiếu ID, văn bản và metadata của 783 tài liệu."),
    ], [4, 3, 9])
    prose(doc, "Kết quả backend là số phương thức kiểm thử unittest; một phương thức có thể kiểm tra nhiều giá trị bằng subTest. Bởi vậy số lượng tổ hợp đầu vào lớn hơn số phương thức đã chạy. Kết quả trình duyệt là 10 kịch bản thao tác, cũng có nhiều bước trong một kịch bản. Không gộp hai đơn vị này để tuyên bố một tỷ lệ chính xác của chatbot.")
    doc.add_heading(f"{number}.3. Lỗi phát hiện, chỉnh sửa và kiểm thử hồi quy", 2)
    table(doc, f"Bảng {number}.3. Nhật ký sai lệch đã xử lý", ["Mã / mức", "Sai lệch trước sửa", "Điều chỉnh đã kiểm tra"],
          [(f"{bid}\n{severity}", issue, fix) for bid, severity, issue, fix in BUGS], [2.2, 6.7, 7.1])
    prose(doc, "Các sai lệch RG-01 đến RG-05 thuộc nhánh lịch theo quy tắc, nên được khắc phục trong mã xử lý thay vì trông chờ mô hình tự sửa câu trả lời. RG-06 liên quan tính đáng tin của báo cáo: một phép kiểm tra bị bỏ qua không thể được dùng làm bằng chứng chỉ mục hợp lệ. RG-07 bổ sung điểm dừng cho yêu cầu có đau vai; hệ thống không tự tạo lịch phục hồi vì chưa có mẫu được kiểm chứng cho điều kiện này.")
    doc.add_heading(f"{number}.4. Kiểm thử trình duyệt và minh chứng", 2)
    table(doc, f"Bảng {number}.4. Kết quả kịch bản giao diện", ["Mã", "Nội dung kiểm tra", "Kết quả"],
          [(c['id'], c['description'], c['status']) for c in browser['cases']], [1.5, 12.4, 2.1])
    prose(doc, "Các thao tác được chạy bằng Playwright với Microsoft Edge ở chế độ headless và backend phục vụ bản build thật. Ca lỗi HTTP 503 được cố ý mô phỏng ở lớp mạng để xác nhận ô nhập được khôi phục và không để lại bong bóng tin nhắn giả. Các ca lưu lịch sử, đổi tên, xóa, F5 và đăng nhập gọi API thật với MySQL. Tài khoản kiểm thử được tạo riêng bằng email ngẫu nhiên và xóa sau khi hoàn tất.")
    image(doc, "ui_mobile_390.png", f"Hình {number}.1. Giao diện thật tại khung nhìn 390×844", width=5.5)
    doc.add_heading(f"{number}.5. Độ bao phủ và giới hạn kiểm thử", 2)
    prose(doc, """
    Bộ kiểm thử đã bao phủ các luồng chính và các giá trị biên nêu trong ma trận. Đợt này chưa đo tỷ lệ bao phủ dòng lệnh/nhánh bằng công cụ coverage; không suy ra mức bao phủ 100% từ việc toàn bộ ca đang có đều đạt. Chưa có kiểm thử tải nhiều người dùng, thử độ bền nhiều giờ, ma trận trình duyệt và thiết bị vật lý, hoặc kiểm định khả năng tiếp cận đầy đủ theo WCAG.

    Các ca ngữ cảnh xác nhận hành vi trong cửa sổ ba lượt gần nhất. Hệ thống chưa có hồ sơ sở thích hoặc sức khỏe lâu dài, nên thông tin cũ có thể rời cửa sổ khi hội thoại kéo dài. Cơ chế chặn prompt injection dùng biểu thức chính quy và chỉ được xác nhận với các mẫu đã thử; chưa chứng minh chống được mọi ngôn ngữ, mã hóa hoặc chỉ dẫn độc hại ẩn trong tài liệu truy xuất.

    Tất cả ảnh trong phần kiểm thử là ảnh chụp ứng dụng local của lần kiểm tra này. Kết quả đạt trên trình duyệt mô phỏng 390px không thay cho thử nghiệm điện thoại vật lý. Các lỗi của công cụ chọn phần tử hoặc môi trường khởi chạy được phân biệt với lỗi sản phẩm khi đọc nhật ký.
    """)


def ai_sections(doc, ai, history, manual, number="5"):
    scores = Counter(r['judge_score'] for r in history)
    versions = Counter(r.get('judge_version') for r in history)
    sm = ai['summary']
    doc.add_heading(f"{number}.1. Hai nguồn bằng chứng đánh giá", 2)
    prose(doc, """
    Đánh giá nội dung sử dụng hai nguồn riêng. Nguồn thứ nhất là 193 bản ghi đơn lượt được nhận từ remote; chúng giúp kiểm toán hồ sơ và phân tích chất lượng đã ghi nhận trước đợt chỉnh sửa. Nguồn thứ hai là 12 tình huống chấp nhận được hỏi mới sau sửa lỗi, gồm kỹ thuật, đối tượng đặc biệt, ngoài phạm vi, lệnh chèn, hỏi bổ sung, lịch có ràng buộc và hội thoại nhiều lượt. Không gộp hai nguồn thành một tỷ lệ của phiên bản mới.

    Bộ tình huống mới được thiết kế để kiểm tra chức năng và hồi quy, trong đó có tình huống phát sinh từ lỗi đã quan sát. Vì vậy đây là mẫu chấp nhận phục vụ bản demo, không phải tập kiểm thử mù độc lập để ước lượng độ chính xác tổng quát. Mỗi tình huống ghi câu hỏi, câu trả lời nguyên văn, nguồn RAG, thời gian chatbot, kiểm tra điều kiện và điểm AI.
    """)
    doc.add_heading(f"{number}.2. Số liệu từ hồ sơ 193 câu bàn giao", 2)
    table(doc, f"Bảng {number}.1. Phân bố điểm đã lưu trên tập đơn lượt", ["Mức", "Số câu", "Tỷ lệ"], [
        ("2 — đúng, đủ ý theo judge", scores[2], f"{scores[2]/len(history):.2%}"),
        ("1 — đúng một phần", scores[1], f"{scores[1]/len(history):.2%}"),
        ("0 — sai hoặc từ chối", scores[0], f"{scores[0]/len(history):.2%}"),
        ("Tổng có điểm", len(history), "100%"),
    ], [9, 3, 4])
    prose(doc, f"Có {versions[2]} dòng dùng judge v2 và {versions[3]} dòng dùng judge v3. Số điểm 2/2 là {scores[2]}/193, tương đương {scores[2]/193:.2%}; đây là thống kê của hồ sơ có hai phiên bản chấm. Nhãn duyệt tay trong Excel có {manual[1]} đạt và {manual[0]} không đạt trên 193 dòng. Hồ sơ không xác lập người chấm thứ hai, chuyên môn y khoa hoặc độ đồng thuận, nên không gọi tỷ lệ nhãn tay là độ chính xác chuyên gia.")
    image(doc, "historical_scores.png", f"Hình {number}.1. Phân bố điểm trên 193 bản ghi từ remote")
    token = sum(r['token_f1'] for r in history)/len(history)
    rouge = sum(r['rouge_l_f1'] for r in history)/len(history)
    prose(doc, f"Token F1 trung bình của hồ sơ là {token:.4f}, ROUGE-L F1 trung bình là {rouge:.4f}. Các chỉ số chỉ phản ánh trùng từ và thứ tự từ sau chuẩn hóa. Một câu trả lời đủ ý nhưng diễn đạt khác có thể có F1 thấp; một câu lặp nhiều từ tham chiếu vẫn có thể sai hoặc thiếu điều kiện. Không dùng chúng thay cho đánh giá nội dung. Theo định nghĩa ROUGE-L, dãy con chung dài nhất là cơ sở đánh giá mức trùng thứ tự [9].")
    prose(doc, "154 dòng cũ không ghi loại phép đo thời gian; 5 dòng ghi thời gian cũ có thể gồm cả judge; 34 dòng ghi chatbot_only. Vì điều kiện không đồng nhất, báo cáo này không tính một độ trễ chatbot chung từ trường seconds của toàn bộ 193 dòng. Hồ sơ cũ cũng không lưu đầy đủ hash mã nguồn cho từng câu, nên không dùng nó chứng minh chất lượng của các thay đổi vừa thực hiện.")
    doc.add_heading(f"{number}.3. Bộ tình huống hỏi mới và AI chấm lại", 2)
    prose(doc, f"Bộ mới có {sm['scenarios']} tình huống, {sm['user_turns']} lượt người dùng, sử dụng ChatService thật với Chroma {ai['indexed_documents']} tài liệu và hai mô hình local. Mô hình chấm là {ai['chat_model']} qua rubric v3, thang 0–2: 2 là đúng và đủ ý chính; 1 là thiếu ý hoặc điều kiện quan trọng; 0 là sai, không trả lời hoặc từ chối sai. Kiểm tra điều kiện xác định được thực hiện riêng với điểm judge.")
    table(doc, f"Bảng {number}.2. Kết quả hỏi mới theo tình huống", ["Mã", "Nhóm tình huống", "Điều kiện", "Điểm AI"],
          [(c['id'], c['category'], "Đạt" if c['contract_passed'] else "Chưa đạt", c.get('judge_score', 'Lỗi')) for c in ai['cases']], [1.6, 8, 3.3, 3.1])
    prose(doc, f"Có {sm['contract_passed']}/{sm['scenarios']} tình huống đạt điều kiện chức năng, {sm['errors']} lỗi gọi chatbot và {sm['judge_errors']} lỗi chấm. Phân bố điểm Qwen: " + "; ".join(f"{score}/2: {count} tình huống" for score, count in sorted(sm['judge_scores'].items())) + ". Điểm AI và kết quả điều kiện là hai phép kiểm tra khác nhau: phản hồi có nguồn và không lỗi vẫn có thể thiếu nội dung.")
    doc.add_heading(f"{number}.4. Độ trễ đo riêng của lần kiểm tra mới", 2)
    table(doc, f"Bảng {number}.3. Thời gian ChatService ở nhóm câu hỏi RAG mới", ["Chỉ số", "Giá trị"], [
        ("Số lượt RAG trong mẫu", sm['rag_turns']), ("Trung bình", f"{sm['rag_mean_seconds']} giây"),
        ("Trung vị", f"{sm['rag_median_seconds']} giây"), ("Nhỏ nhất", f"{sm['rag_min_seconds']} giây"),
        ("Lớn nhất", f"{sm['rag_max_seconds']} giây"),
    ], [10, 6])
    prose(doc, "Thời gian dùng đồng hồ monotonic quanh ChatService.ask, gồm truy xuất, nạp/đổi mô hình nếu có và sinh câu trả lời; không gồm chấm AI hoặc thời gian trình duyệt. Nhóm lịch theo quy tắc và nhóm từ chối nhanh không được trộn với RAG để làm thấp thời gian trung bình. Mẫu nhỏ, chạy tuần tự trên GPU GTX 1650 4 GB cùng máy phát triển, nên kết quả phản ánh đúng điều kiện lần thử này và chưa đại diện cho một cam kết hiệu năng. Câu trả lời sinh dài có thể mất vài phút; đây là hạn chế thực tế khi trình diễn.")
    doc.add_heading(f"{number}.5. Nhận xét rà soát AI và kết luận về chatbot", 2)
    review = RESULTS / "AI_REVIEW_NHAN_XET.md"
    if not review.exists():
        raise FileNotFoundError("Cần hoàn tất rà soát câu trả lời và AI_REVIEW_NHAN_XET.md trước khi tạo báo cáo cuối.")
    for block in review.read_text(encoding="utf-8").split("\n\n"):
        cleaned = re.sub(r"^#{1,6}\s+", "", block.strip())
        if cleaned:
            paragraph(doc, cleaned)
    prose(doc, "Điểm Qwen là đánh giá tự động của cùng họ mô hình đang sinh câu trả lời và có thể thiên lệch hoặc chấm sai. Rà soát AI bổ sung trong báo cáo đọc trực tiếp phản hồi và mã nguồn, nhưng vẫn không phải đánh giá của bác sĩ hoặc huấn luyện viên được xác minh. Không tuyên bố chatbot đạt 100% chính xác hoặc an toàn từ các kết quả trên.")


def build_main(software, browser, before, after, ai, history, manual):
    doc = make_document("TIỂU LUẬN", "Báo cáo dự án, kiểm thử phần mềm và đánh giá chatbot — cập nhật 25/11/2026")
    chapter(doc, "LỜI CẢM ƠN")
    prose(doc, """
    Nhóm em xin gửi lời cảm ơn đến quý thầy cô Trường Đại học Hùng Vương TP. Hồ Chí Minh đã tạo điều kiện để nhóm tiếp cận kiến thức và thực hành xây dựng ứng dụng trí tuệ nhân tạo. Đề tài AI-4GYM giúp nhóm vận dụng kiến thức về mô hình ngôn ngữ, truy xuất tri thức, phát triển ứng dụng web và kiểm thử phần mềm vào một bài toán cụ thể.

    Nhóm em xin chân thành cảm ơn thầy Nguyễn Thanh Tiến, giảng viên môn Các ứng dụng trong AI, đã định hướng nội dung học phần và yêu cầu nhóm chú trọng kiểm thử, đánh giá chất lượng phản hồi. Qua việc đối chiếu mã nguồn với kết quả thực thi, nhóm nhận thấy cần phân biệt rõ tính đúng của chức năng, chất lượng nội dung chatbot và độ tin cậy của phép chấm tự động.

    Nhóm cảm ơn sự phối hợp của các thành viên trong việc chuẩn bị dữ liệu, phát triển frontend và backend, kiểm tra sản phẩm và tổng hợp minh chứng. Báo cáo trình bày nguyên mẫu trong phạm vi học phần; các giới hạn về chất lượng phản hồi, hiệu năng local và đánh giá chuyên môn được ghi nhận để làm cơ sở cải tiến.
    """)
    chapter(doc, "LỜI CAM ĐOAN")
    prose(doc, """
    Nhóm thực hiện trình bày đề tài AI-4GYM trong khuôn khổ môn Các ứng dụng trong AI, lớp CT07PM. Nội dung về kiến trúc, chức năng và dữ liệu được đối chiếu với mã nguồn và hiện vật của dự án. Các kết quả kiểm thử được nêu theo đúng điều kiện và phiên bản có trong nhật ký.

    Báo cáo phân biệt số liệu nhận từ hồ sơ bàn giao, kết quả chạy mới, điểm chấm tự động và nhận xét rà soát bằng AI. Những phần chưa có kiểm chứng chuyên môn hoặc chưa được thử trong đợt này được ghi là giới hạn; không trình bày như kết quả đã xác nhận. Tài liệu và nguồn dữ liệu tham khảo được dẫn ở phần cuối báo cáo.

    Nhóm chịu trách nhiệm đối với nội dung tổng hợp và cách diễn giải kết quả trong phạm vi học phần. Các tài liệu minh chứng được lưu cùng báo cáo để người chấm có thể đối chiếu theo mã ca kiểm thử và mã bản ghi.
    """)
    chapter(doc, "TÓM TẮT ĐỀ TÀI")
    prose(doc, """
    AI-4GYM là ứng dụng hỏi–đáp tiếng Việt hỗ trợ người mới tra cứu bài tập, nhóm cơ, kỹ thuật và tham khảo lịch tập Gym/Fitness. Hệ thống dùng React/TypeScript cho giao diện, FastAPI cho API, MySQL cho tài khoản và lịch sử, Chroma cho chỉ mục vector, LangChain để kết hợp ngữ cảnh với mô hình Qwen chạy local qua Ollama. Hai nhánh xử lý chính là hỏi–đáp dựa trên tài liệu truy xuất và tạo lịch theo quy tắc từ danh mục bài tập.

    Dữ liệu nguồn có 965 cặp hỏi–đáp, chia cố định thành 772 câu lập chỉ mục và 193 câu giữ riêng. Kho truy xuất bổ sung 11 bài tập có cấu trúc, tổng 783 tài liệu. “Train” trong dự án chỉ là corpus dùng cho RAG, không phải huấn luyện lại hoặc fine-tune mô hình. Dữ liệu đã có trường nguồn theo từng câu; số lượng đường dẫn không đồng nghĩa mọi nội dung đã được chuyên gia thẩm định.
    """)
    s, b, a = software['summary'], browser['summary'], ai['summary']
    prose(doc, f"Đợt kiểm tra ngày {DATE} chạy {s['tests_run']} phương thức backend, đạt {s['passed']}, lỗi {s['failed'] + s['errors']}, bỏ qua {s['skipped']}; {b['total']} kịch bản trình duyệt đạt {b['passed']}. Bảy nhóm lỗi được tái hiện và sửa bằng kiểm thử hồi quy. Bộ đánh giá hỏi mới có {a['scenarios']} tình huống/{a['user_turns']} lượt, đạt {a['contract_passed']} điều kiện chức năng; kết quả chấm AI được phân tích riêng ở Chương 5. Hồ sơ bàn giao 193 câu có 132 câu điểm 2, 56 câu điểm 1 và 5 câu điểm 0, nhưng không được coi là phép đo lại toàn bộ phiên bản sau sửa.")
    paragraph(doc, "Từ khóa: chatbot tiếng Việt; RAG; Ollama; Gym/Fitness; kiểm thử phần mềm; đánh giá phản hồi.")
    toc(doc)
    chapter(doc, "DANH MỤC TỪ VIẾT TẮT")
    table(doc, None, ["Ký hiệu", "Nghĩa và cách dùng trong đề tài"], [
        ("AI", "Artificial Intelligence — trí tuệ nhân tạo"), ("LLM", "Large Language Model — mô hình ngôn ngữ lớn"),
        ("RAG", "Retrieval-Augmented Generation — sinh câu trả lời có bổ sung tài liệu truy xuất"),
        ("API", "Application Programming Interface — giao diện lập trình ứng dụng"),
        ("HTTP", "Hypertext Transfer Protocol — giao thức trao đổi giữa trình duyệt và backend"),
        ("CRUD", "Create, Read, Update, Delete — tạo, đọc, cập nhật, xóa"),
        ("JSON/JSONL", "Dữ liệu JSON / mỗi dòng là một bản ghi JSON"),
        ("F1", "Trung bình điều hòa giữa precision và recall"), ("ROUGE-L", "Mức trùng văn bản dựa trên dãy con chung dài nhất"),
        ("ACE", "American Council on Exercise — nguồn thư viện bài tập"),
        ("ACSM", "American College of Sports Medicine — nguồn tham khảo nguyên tắc tập sức mạnh"),
        ("SHA-256", "Hàm băm dùng nhận diện dữ liệu và phiên bản tệp"),
    ], [3, 13])
    chapter(doc, "LỜI MỞ ĐẦU")
    doc.add_heading("1. Lý do chọn đề tài", 2)
    prose(doc, "Người mới tập thường cần câu trả lời cụ thể về tư thế, chuyển động, lỗi cần tránh và cách sắp xếp thời gian tập. Tra cứu bằng ngôn ngữ tự nhiên tạo thuận lợi cho việc đặt câu hỏi nối tiếp, nhưng cũng làm xuất hiện rủi ro trả lời thiếu căn cứ hoặc gợi ý không phù hợp điều kiện cá nhân. Đề tài chọn một phạm vi rõ ràng để kết hợp mô hình ngôn ngữ với kho dữ liệu có thể truy vết và lịch tập có cấu trúc.")
    doc.add_heading("2. Mục tiêu và phạm vi", 2)
    prose(doc, "Mục tiêu là xây dựng chatbot local có thể tra cứu kiến thức Gym/Fitness bằng tiếng Việt, giải thích kỹ thuật từ tài liệu và tạo lịch 1–6 buổi mỗi tuần. Phiên bản hiện tại nhận diện mục tiêu, dụng cụ, một số hạn chế thể chất và ngữ cảnh gần để điều chỉnh mẫu lịch. Hệ thống hỗ trợ chat khách và tài khoản lưu lịch sử; không chẩn đoán, kê đơn, hoặc thiết kế phục hồi chấn thương chuyên môn. Thời lượng mỗi buổi, tải tập và hồ sơ sức khỏe lâu dài chưa được tối ưu tự động.")
    doc.add_heading("3. Cách tiếp cận và đóng góp", 2)
    prose(doc, "Báo cáo đối chiếu toàn bộ các mô-đun frontend/backend, dữ liệu nguồn, hồ sơ đánh giá và kết quả chạy mới. Đóng góp của đợt hoàn thiện gồm chỉnh nội dung báo cáo theo bản remote hiện hành; bổ sung bộ kiểm thử có thể thực thi; tái hiện và sửa sai lệch ở nhánh lịch, ngữ cảnh và kiểm tra chỉ mục; đánh giá chatbot thật bằng bộ tình huống mới có AI chấm lại. Nội dung tiếp theo gồm cơ sở lý thuyết, thiết kế, triển khai, kiểm thử phần mềm và đánh giá nội dung.")
    chapter(doc, "CHƯƠNG 1. CƠ SỞ LÝ THUYẾT")
    doc.add_heading("1.1. Chatbot và mô hình ngôn ngữ lớn", 2)
    prose(doc, """
    Chatbot tiếp nhận ngôn ngữ tự nhiên và trả lời trong một ngữ cảnh hội thoại. Mô hình ngôn ngữ lớn có khả năng diễn đạt linh hoạt, nhưng văn bản mạch lạc không bảo đảm đúng sự kiện. Với ứng dụng tư vấn tập luyện, cần kiểm tra cả phạm vi câu hỏi, nguồn tri thức, mức đầy đủ của kỹ thuật và những điều kiện có thể làm thay đổi khuyến nghị.

    AI-4GYM dùng mô hình qwen3:4b-instruct được phục vụ qua Ollama. Chỉ dẫn hệ thống yêu cầu trả lời tiếng Việt, dựa vào nội dung truy xuất, không bịa nguồn, không chẩn đoán hoặc kê đơn. Chỉ dẫn là cơ chế định hướng; mức tuân thủ phải được xem xét qua các câu trả lời thực tế và kiểm thử đối kháng trong phạm vi đã xác định.
    """)
    doc.add_heading("1.2. Truy xuất tăng cường sinh (RAG)", 2)
    prose(doc, """
    RAG kết hợp mô hình sinh với một nguồn tri thức có thể truy xuất [1]. Giai đoạn lập chỉ mục chuyển tài liệu thành vector và lưu trong cơ sở dữ liệu vector. Khi có câu hỏi, truy vấn được chuyển thành vector, hệ thống tìm tài liệu liên quan và ghép nội dung vào ngữ cảnh để mô hình tạo câu trả lời. LangChain cung cấp các thành phần kết hợp prompt, lịch sử, bộ truy xuất và mô hình [2].

    Trong dự án, đơn vị tài liệu là một cặp hỏi–đáp hoặc một hồ sơ bài tập có cấu trúc. Chroma lưu vector và metadata, trong khi Ollama cung cấp mô hình embedding và mô hình sinh [3][4]. Việc thay đổi kho tri thức được thực hiện bằng cập nhật dữ liệu và chỉ mục. Hệ thống không cập nhật trọng số Qwen hoặc mô hình embedding; do đó phép chia train/test cần được hiểu theo vai trò xây dựng corpus và đánh giá truy xuất–trả lời.
    """)
    doc.add_heading("1.3. Vector, độ liên quan và khả năng truy vết", 2)
    prose(doc, """
    Biểu diễn vector ánh xạ văn bản vào không gian số để tìm kiếm theo độ tương đồng. Chroma của dự án dùng cosine; câu hỏi và tài liệu phải được embedding bằng cùng cấu hình. Tên bộ sưu tập gắn với hash tên mô hình embedding để giảm nguy cơ dùng nhầm chỉ mục của mô hình khác.

    Metadata lưu ID, tiêu đề, loại tài liệu, nguồn và dòng Excel khi có. Điểm liên quan chỉ hỗ trợ lựa chọn tài liệu đưa vào ngữ cảnh, không phải xác suất câu trả lời đúng. Danh sách nguồn trên giao diện xác nhận tài liệu đã được cung cấp cho lần sinh, nhưng cần đối chiếu nội dung nguồn với phát biểu mới có thể đánh giá tính căn cứ.
    """)
    doc.add_heading("1.4. Gợi ý lịch tập theo quy tắc", 2)
    prose(doc, """
    Một đầu ra có cấu trúc như lịch tập có thể được tạo từ mẫu xác định. AI-4GYM ánh xạ số buổi sang lịch ngày trong tuần và nhóm bài; sau đó thay bài theo dụng cụ hoặc một số hạn chế đã nhận diện. Với cùng tham số và cùng dữ liệu, nhánh này trả cấu trúc ổn định, thuận lợi cho kiểm thử tự động.

    Mẫu lịch là thiết kế của dự án dựa trên các nguyên tắc tham khảo, không phải phác đồ điều trị hoặc một lịch chuẩn được ACSM chứng nhận cho từng cá nhân. Thay bài để đáp ứng dụng cụ mới chỉ bảo đảm điều kiện về thiết bị, chưa chứng minh tương đương hoàn toàn về nhóm cơ, tải tập và hiệu quả. Những điểm này được nêu trong phần giới hạn.
    """)
    doc.add_heading("1.5. Kiểm thử phần mềm và đánh giá chatbot", 2)
    prose(doc, """
    Kiểm thử phần mềm kiểm tra hành vi quan sát được khi hệ thống nhận một đầu vào và trạng thái xác định. Kiểm thử đơn vị cô lập logic; kiểm thử tích hợp xác nhận nhiều thành phần phối hợp; kiểm thử trình duyệt kiểm tra thao tác của người dùng trên ứng dụng đã dựng. Các giá trị biên và trường hợp lỗi có vai trò phát hiện thiếu sót mà luồng thông thường không bộc lộ.

    Đánh giá chatbot cần thêm tiêu chí về đúng nội dung, đủ ý, phù hợp đối tượng, giữ ràng buộc và xử lý thiếu dữ liệu. Bộ chấm bằng LLM giúp rà soát nhanh nhiều phản hồi nhưng phụ thuộc rubric và chất lượng mô hình chấm. Do đó, kết quả kiểm thử API, điểm LLM, nhãn duyệt tay và chỉ số trùng từ được báo cáo riêng. Một nhóm đạt không được dùng thay bằng chứng của nhóm khác.
    """)
    chapter(doc, "CHƯƠNG 2. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG")
    doc.add_heading("2.1. Đối tượng sử dụng và yêu cầu", 2)
    table(doc, "Bảng 2.1. Chức năng và giới hạn đầu ra", ["Chức năng", "Hành vi được triển khai"], [
        ("Chat khách", "Hỏi không cần tài khoản; lịch sử trong RAM, giao diện mất khi F5."),
        ("Hỏi–đáp bài tập", "Giải thích tiếng Việt, ưu tiên tài liệu đúng tên bài, kèm nguồn khi có."),
        ("Lịch tập", "Mẫu 1–6 buổi; điều chỉnh theo dụng cụ, mục tiêu và một số hạn chế."),
        ("Hội thoại nhiều lượt", "Tối đa 3 lượt hỏi–đáp gần nhất theo cấu hình mặc định."),
        ("Tài khoản", "Đăng ký/đăng nhập/đăng xuất; lưu, mở, đổi tên và xóa hội thoại."),
        ("Giới hạn", "Từ chối ngoài phạm vi/lệnh chèn; báo thiếu dữ liệu; không thay thế tư vấn y tế."),
    ], [4, 12])
    prose(doc, "Khách và người đăng nhập đều dùng giao diện chat, nhưng cách lưu trạng thái khác nhau. Người đăng nhập được cấp cookie phiên và API kiểm tra quyền sở hữu trước mọi thao tác với hội thoại. Phía giao diện có trạng thái chờ phản hồi, khóa nút gửi khi đang xử lý, thông báo lỗi và khôi phục câu hỏi nếu gửi thất bại. Đây là các yêu cầu cần kiểm tra cùng nội dung AI vì chúng quyết định khả năng sử dụng sản phẩm.")
    doc.add_heading("2.2. Dữ liệu và phép chia cố định", 2)
    table(doc, "Bảng 2.2. Cấu trúc và vai trò dữ liệu", ["Thành phần", "Số lượng", "Vai trò"], [
        ("data/raw/data.xlsx", 965, "Cặp hỏi–đáp có trường nguồn theo từng bản ghi."),
        ("processed/qa.json", 965, "Chuyển đổi từ Excel, giữ ID và dòng nguồn."),
        ("processed/train.json", 772, "80%; dùng xây dựng kho truy xuất."),
        ("processed/test.json", 193, "20%; giữ riêng, không đưa vào Chroma."),
        ("curated/exercises.json", 11, "Bài tập có tên, alias, dụng cụ, kỹ thuật, lỗi và nguồn."),
        ("Chroma", 783, "772 cặp hỏi–đáp cộng 11 hồ sơ bài tập."),
    ], [6.3, 2.2, 7.5])
    prose(doc, """
    Chương trình chuẩn hóa câu hỏi bằng chuyển chữ thường, bỏ dấu kết hợp và đổi đ thành d. Những câu hỏi trùng sau chuẩn hóa được giữ trong cùng một nhóm. Thứ tự nhóm được xác định bằng SHA-256 với seed 42, sau đó lấy đủ 193 câu làm test. Cách chia tái lập không phụ thuộc thứ tự đầu vào và không để cùng câu hỏi chuẩn hóa nằm ở hai tập.

    Bản Excel hiện hành đã có URL nguồn theo câu; 676/965 bản ghi dẫn tới bộ fitness-question-answers trên Hugging Face, các bản ghi còn lại dẫn đến những nguồn sức khỏe và vận động được ghi trong dữ liệu. Đây là thay đổi so với mô tả cũ chỉ có tên data.xlsx. Việc có URL giúp truy vết xuất xứ, nhưng không tự chứng minh chất lượng bản dịch, mức phù hợp của khuyến nghị hoặc việc từng câu đã được chuyên gia đối chiếu.

    Kiểm toán hiện tại phát hiện 1 câu test có Jaccard từ vựng từ 0,8 trở lên với ít nhất một câu train. Đây là dấu hiệu gần trùng cần rà soát, không phải kiểm định rò rỉ ngữ nghĩa đầy đủ. Các câu test về bài tập có thể được hỗ trợ bởi 11 hồ sơ biên soạn bổ sung đang có trong corpus; do đó tập test đánh giá hệ thống RAG với kho tri thức đó, không đo kiến thức hoàn toàn chưa từng xuất hiện dưới dạng khác.
    """)
    image(doc, "data_flow.png", "Hình 2.1. Dòng dữ liệu hiện hành của dự án")
    doc.add_heading("2.3. Kiến trúc tổng thể", 2)
    image(doc, "architecture.png", "Hình 2.2. Các thành phần và hai nhánh trả lời của AI-4GYM")
    prose(doc, "React gửi HTTP tới FastAPI. Ở chế độ phát triển, Vite chuyển /api sang cổng backend; bản production được FastAPI phục vụ từ FE/dist. Dịch vụ chat kiểm tra phạm vi, lấy lịch sử, suy ra các điều kiện rồi chọn nhánh lịch hoặc RAG. MySQL lưu trạng thái tài khoản và hội thoại, Chroma lưu tri thức để tìm kiếm; hai loại lưu trữ không thay thế nhau. Mô hình trả lời và embedding chạy trên địa chỉ Ollama loopback, không dùng API AI bên ngoài trong ứng dụng.")
    doc.add_heading("2.4. Mô hình dữ liệu ứng dụng", 2)
    table(doc, "Bảng 2.3. Năm bảng MySQL đang triển khai", ["Bảng", "Dữ liệu và quan hệ chính"], [
        ("users", "ID, email duy nhất, display_name, mật khẩu băm Argon2, created_at."),
        ("login_sessions", "Hash SHA-256 của token; user_id, thời điểm tạo và hết hạn."),
        ("conversations", "UUID hội thoại, chủ sở hữu user_id, tiêu đề và thời điểm cập nhật."),
        ("chat_messages", "UUID tin nhắn, conversation_id, vai trò, nội dung, nguồn JSON, created_at."),
        ("chat_request_records", "Khóa user_id + request_id duy nhất; hash payload và response JSON để chống lưu lặp."),
    ], [4.8, 11.2])
    prose(doc, "Một người dùng có nhiều hội thoại; một hội thoại có nhiều tin nhắn. Khi xóa hội thoại, các tin nhắn liên quan được xóa theo quan hệ đã cấu hình. Phiên đăng nhập có thời hạn cố định 7 ngày, cookie HttpOnly/SameSite=Lax và Secure theo cấu hình triển khai. Token thô không được lưu trong DB. Request chat của tài khoản có thể mang request_id để lặp yêu cầu mà không thêm cặp tin nhắn lần nữa; cùng ID nhưng payload khác nhận 409.")
    doc.add_heading("2.5. Giao diện API", 2)
    table(doc, "Bảng 2.4. Các điểm vào chính", ["Phương thức / đường dẫn", "Chức năng"], [
        ("GET /health", "Tình trạng Ollama, model, số tài liệu và MySQL."),
        ("POST /chat", "Hỏi mới hoặc nối tiếp; nhận message, mã phiên/hội thoại và request_id."),
        ("GET /exercises; /exercises/{id}", "Danh mục, lọc nhóm cơ và chi tiết bài tập."),
        ("GET /plans?days=1..6", "Lịch mẫu cơ bản; endpoint này chỉ nhận số buổi."),
        ("POST /auth/register; /login; /logout", "Vòng đời tài khoản và cookie phiên."),
        ("GET /auth/me", "Thông tin người đang đăng nhập."),
        ("GET /conversations; /{id}", "Danh sách và chi tiết hội thoại của chủ tài khoản."),
        ("PATCH /conversations/{id}; DELETE /{id}", "Đổi tên hoặc xóa hội thoại thuộc tài khoản."),
    ], [8.1, 7.9])
    prose(doc, "Cần phân biệt /plans với /chat: /plans kiểm tra số buổi bằng tham số có miền 1–6, còn /chat dùng nhận diện ngôn ngữ và có thể hỏi bổ sung. Các điều kiện dụng cụ, mục tiêu và chấn thương được xử lý trong nhánh chat; không có endpoint hồ sơ sức khỏe riêng. /health có thể báo AI ready khi MySQL chưa sẵn sàng vì chat khách không cần DB, nên phải đọc thêm database_running khi kiểm tra chức năng tài khoản.")
    chapter(doc, "CHƯƠNG 3. TRIỂN KHAI VÀ MINH HỌA")
    doc.add_heading("3.1. Công nghệ và tổ chức mã nguồn", 2)
    table(doc, "Bảng 3.1. Thành phần triển khai", ["Thành phần", "Công nghệ / tệp tiêu biểu"], [
        ("Frontend", "React 19, TypeScript, Vite; App.tsx và các thành phần Sidebar, Composer, AuthModal, MessageBubble."),
        ("API và lưu trữ", "FastAPI, Pydantic, SQLAlchemy, PyMySQL; app/api/routes, app/db."),
        ("Truy xuất và mô hình", "LangChain, langchain-chroma, langchain-ollama, ChromaDB, Ollama."),
        ("Dữ liệu và báo cáo", "openpyxl; dataset.py, knowledge.py, ingest.py, audit_report.py, export_report.py."),
        ("Kiểm thử", "unittest, FastAPI TestClient; Playwright/Edge cho trình duyệt."),
    ], [4.2, 11.8])
    doc.add_heading("3.2. Luồng truy xuất và trả lời kỹ thuật", 2)
    prose(doc, """
    Sau khi xác nhận phạm vi và không gặp mẫu chèn lệnh đã biết, dịch vụ dựng truy vấn từ câu hỏi mới và ngữ cảnh liên quan. Chroma tìm k=6 tài liệu; kết quả dưới điểm liên quan 0,18 được loại. Khi nhận diện được tên hoặc alias, hồ sơ bài tập tương ứng được ưu tiên; câu hỏi theo nhóm cơ có thể bổ sung tối đa bốn bài phù hợp mỗi nhóm. Danh sách cuối được khử trùng và giới hạn bảy tài liệu.

    Prompt gồm chỉ dẫn hệ thống, lịch sử gần và nội dung truy xuất. Cấu hình ChatOllama đang dùng temperature=0, num_ctx=4096, num_predict=1500. Phản hồi kỹ thuật được yêu cầu có tư thế chuẩn bị, chuyển động, nhịp thở, lỗi thường gặp và lưu ý an toàn. Nếu không có tài liệu vượt điều kiện lọc hoặc đầu ra trống, hệ thống có thông báo thiếu dữ liệu. Khi tên bài khớp danh mục, nguồn hiển thị đúng ID hồ sơ đã bổ sung, giúp đối chiếu biến thể bài tập.

    Kho tri thức có thêm hồ sơ bent-over-row mô tả bài kéo tạ đơn một tay tựa ghế. Tên trong danh mục vẫn là “Chèo thuyền gập người với tạ đơn”, nên khi phân tích kỹ thuật cần đọc cả mô tả, dụng cụ và biến thể, không chỉ suy từ tên tiếng Anh. Danh mục đã hỗ trợ tra cứu, nhưng chuẩn hóa tên bài và liên kết ACE vẫn là công việc cần duy trì.
    """)
    doc.add_heading("3.3. Ngữ cảnh và cập nhật ràng buộc", 2)
    prose(doc, """
    Theo mặc định, mô hình nhận tối đa ba cặp hỏi–đáp gần nhất. Phiên khách lưu trong RAM và được dọn khi không hoạt động 3600 giây; ID lạ hoặc hết hạn được đổi mới. Với tài khoản, API lấy tin nhắn gần nhất từ MySQL rồi truyền history_override, nên việc khởi tạo lại ChatService không làm mất ngữ cảnh đã lưu trong giới hạn cửa sổ.

    Tên bài trong câu nối tiếp có thể được suy lại từ một bài được nhắc rõ hoặc bài đầu tiên trong lịch. Sau sửa lỗi, dụng cụ, mục tiêu và số buổi được lấy từ lượt người dùng gần nhất có thông tin tương ứng, thay vì nối tất cả câu hỏi rồi để từ khóa cũ lấn thông tin mới. Các hạn chế đau/chấn thương đã nhận diện trong cửa sổ được giữ để tránh vô tình bỏ cảnh báo.

    Nếu đã có lịch và người dùng đổi dụng cụ, mục tiêu hoặc nêu đau gối/lưng, dịch vụ dựng lại lịch với số buổi trước đó. Cách xử lý này làm đầu ra có cấu trúc nhất quán với dữ liệu; phần giải thích kỹ thuật vẫn dùng RAG. Trường hợp đau vai đi vào nhánh giải thích giới hạn và tham khảo bác sĩ, vì chưa có mẫu lịch chuyên biệt đủ căn cứ.
    """)
    doc.add_heading("3.4. Lịch tập theo số buổi và điều kiện", 2)
    table(doc, "Bảng 3.2. Các nhóm mẫu lịch", ["Buổi/tuần", "Mẫu", "Ngày trong mẫu"], [
        (1, "Toàn thân", "Thứ Hai"), (2, "Toàn thân", "Thứ Hai, Thứ Năm"),
        (3, "Toàn thân A/B/A", "Thứ Hai, Thứ Tư, Thứ Sáu"),
        (4, "Upper/Lower", "Thứ Hai, Ba, Năm, Sáu"),
        (5, "Upper/Lower + kỹ thuật nhẹ", "Thứ Hai, Ba, Năm, Sáu, Bảy"),
        (6, "Push/Pull/Legs", "Thứ Hai, Ba, Tư, Sáu, Bảy, Chủ nhật"),
    ], [2.5, 5.3, 8.2])
    prose(doc, """
    Chế độ không dụng cụ ánh xạ các bài dùng máy/tạ sang squat trọng lượng cơ thể, chống đẩy quỳ gối, glute bridge và plank. Chế độ tạ đơn sau sửa không còn máy đẩy vai hoặc dây kháng lực; bài kéo sử dụng hồ sơ tạ đơn có ghế tựa. Mục tiêu giảm mỡ bổ sung định hướng vận động aerobic, còn tăng cơ bổ sung quá tải tiến triển và dinh dưỡng. Những thay đổi này là quy tắc mức cơ bản, chưa phải thuật toán tính tải hoặc tối ưu chương trình tập.

    Với hạn chế gối, mẫu loại squat và leg press; với lưng dưới, mẫu loại các bài kéo cúi người trong danh sách đã cấu hình. Cảnh báo nhấn mạnh dừng động tác gây đau và tham khảo y tế. Việc loại một số bài không chứng minh các bài còn lại phù hợp mọi dạng chấn thương. Số hiệp, lần lặp, khối lượng tạ, thời gian nghỉ và thời lượng buổi tập chưa được cá nhân hóa đầy đủ.
    """)
    doc.add_heading("3.5. Giao diện thực tế", 2)
    image(doc, "ui_desktop.png", "Hình 3.1. Trang chính của bản build chạy local")
    prose(doc, "Giao diện có thanh lịch sử, các thẻ gợi ý, vùng hội thoại, nguồn tham khảo và ô nhập. Tin nhắn của chatbot được render bằng Markdown; liên kết nguồn mở ở thẻ mới với thuộc tính bảo vệ cửa sổ. Nút gửi bị khóa khi trống hoặc đang xử lý, Enter để gửi và Shift+Enter để xuống dòng. Lỗi gửi trả lại câu hỏi vào ô nhập để người dùng không phải gõ lại.")
    image(doc, "ui_chat.png", "Hình 3.2. Câu trả lời lịch thật và phần nguồn tham khảo")
    image(doc, "ui_auth_validation.png", "Hình 3.3. Biểu mẫu đăng ký và thông báo xác nhận mật khẩu", width=12.5)
    prose(doc, "Tài khoản dùng cookie HttpOnly nên frontend không đọc trực tiếp token. Lịch sử được tải bằng API sau khi đăng nhập và sau F5. Người dùng có thể đổi tên, mở lại hoặc xóa hội thoại; khách được thông báo lịch sử sẽ mất khi tải lại trang. Giao diện mobile thu thanh bên thành menu và được kiểm tra ở khung nhìn 390px trong đợt này.")
    chapter(doc, "CHƯƠNG 4. KIỂM THỬ PHẦN MỀM")
    software_sections(doc, software, browser, before, after)
    chapter(doc, "CHƯƠNG 5. ĐÁNH GIÁ VÀ RÀ SOÁT CHATBOT BẰNG AI")
    ai_sections(doc, ai, history, manual)
    chapter(doc, "KẾT LUẬN VÀ KIẾN NGHỊ")
    prose(doc, f"AI-4GYM đã triển khai được chatbot tiếng Việt chạy local với RAG, lịch theo quy tắc, tài khoản và lịch sử có phân quyền. Sau khi cập nhật remote, đợt hoàn thiện bổ sung 25 ca phần mềm và 7 ca hồi quy, xử lý các sai lệch liên quan dụng cụ, mục tiêu, chỉnh lịch, kiểm tra chỉ mục và đau vai. Kết quả thực thi cuối gồm {s['passed']}/{s['tests_run']} phương thức backend đạt và {b['passed']}/{b['total']} kịch bản trình duyệt đạt. Dữ liệu, hồ sơ đánh giá và 783 tài liệu Chroma được đối chiếu trực tiếp.")
    prose(doc, """
    Phần hỏi–đáp được kiểm tra bằng bộ tình huống mới và có AI chấm lại trên phản hồi thật. Các kết quả đủ làm minh chứng cho nguyên mẫu và phần demo trong phạm vi học phần khi trình bày kèm giới hạn. Dữ liệu 193 câu bàn giao vẫn được giữ nguyên và mô tả đúng phiên bản chấm; tỷ lệ của hồ sơ này không được coi là tỷ lệ chính xác đo lại sau sửa lỗi. Độ trễ sinh câu trả lời trên máy local và các nội dung cần thẩm định chuyên môn là những hạn chế phải được nêu khi báo cáo.

    Hướng phát triển ưu tiên là chuẩn hóa tên bài và nguồn, bổ sung tập đánh giá độc lập sau khi chốt chức năng, đo thời gian và tối ưu độ dài ngữ cảnh/đầu ra, mở rộng đánh giá nhiều lượt và tổ chức chuyên gia duyệt những câu liên quan kỹ thuật hoặc sức khỏe. Nếu mở rộng ứng dụng cho nhiều người dùng, cần thêm kiểm thử tải, độ bền phiên, quan sát lỗi và cơ chế kiểm soát tài nguyên. Trước khi cá nhân hóa sâu cần có các thuộc tính và quy tắc được thẩm định, thay vì suy diễn từ vài từ khóa trong câu hỏi.
    """)
    chapter(doc, "TÀI LIỆU THAM KHẢO")
    references = [
        "[1] Lewis, P. và cộng sự (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS. https://arxiv.org/abs/2005.11401",
        "[2] LangChain. Retrieval — tài liệu về kết hợp kho tri thức với mô hình ngôn ngữ. https://docs.langchain.com/oss/python/langchain/retrieval",
        "[3] Chroma. Tài liệu cơ sở dữ liệu vector và bộ sưu tập. https://docs.trychroma.com/",
        "[4] Ollama. Tài liệu chạy mô hình local và API. https://docs.ollama.com/",
        "[5] FastAPI. Tài liệu API, validation và testing. https://fastapi.tiangolo.com/",
        "[6] React. Tài liệu phát triển giao diện. https://react.dev/",
        "[7] American Council on Exercise. Exercise Library. https://www.acefitness.org/resources/everyone/exercise-library/",
        "[8] World Health Organization. Physical activity — fact sheet. https://www.who.int/news-room/fact-sheets/detail/physical-activity",
        "[9] Lin, C.-Y. (2004). ROUGE: A Package for Automatic Evaluation of Summaries. https://aclanthology.org/W04-1013/",
        "[10] Python Software Foundation. unittest — Unit testing framework. https://docs.python.org/3/library/unittest.html",
        "[11] Microsoft. Playwright for Python. https://playwright.dev/python/",
        "[12] Bộ dữ liệu its-myrto/fitness-question-answers. Hugging Face. https://huggingface.co/datasets/its-myrto/fitness-question-answers",
        "[13] ACSM. Liên kết định hướng tập sức mạnh đang được lưu trong dự án. https://acsm.org/resistance-training-guidelines-update-2026/",
        "[14] AI-4GYM. Mã nguồn và dữ liệu dự án, commit nền 9863d6531784; các tệp minh chứng ghi nhận ngày 25/11/2026. https://github.com/hohuyhoang308/AI-4GYM",
    ]
    for ref in references:
        p = paragraph(doc, ref)
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(9)
    prose(doc, "Các URL [7], [8], [12], [13] thể hiện nguồn tham khảo và các đường dẫn có trong hồ sơ dữ liệu. Đợt kiểm tra này đối chiếu nguồn đã lưu trong dự án, chưa tái thẩm định toàn văn mọi tài liệu bên ngoài. Các mẫu lịch của nhóm không được coi là lịch do những tổ chức này cấp riêng hoặc chứng nhận cho cá nhân.")
    chapter(doc, "PHỤ LỤC A. DANH MỤC HỒ SƠ KIỂM CHỨNG")
    table(doc, "Bảng A.1. Tệp kết quả và vai trò", ["Tệp trong reports/", "Nội dung"], [
        ("Bo_kiem_thu_AI_4GYM.xlsx", "Ca kiểm thử phần mềm, trình duyệt, lỗi đã sửa, câu hỏi/câu trả lời và điểm AI."),
        ("results/software_test_results.json/.txt", "Kết quả backend theo test_id, log, build và đối chiếu nội dung chỉ mục."),
        ("results/browser_test_results.json", "10 kịch bản Edge thật và nhật ký pageerror."),
        ("results/regressions_before.json; regressions_after.json", "7 nhóm lỗi trước/sau, dấu vết mã nguồn được kiểm tra."),
        ("results/chatbot_ai_review.json", "12 tình huống mới, 16 lượt hỏi, nguồn, điểm AI và thời gian tách riêng."),
        ("results/AI_REVIEW_NHAN_XET.md", "Rà soát bổ sung bằng AI đối với phản hồi thực tế và giới hạn."),
        ("evaluation_results.jsonl", "193 bản ghi bàn giao từ remote, giữ nguyên trong đợt kiểm tra mới."),
        ("evidence/", "Ảnh ứng dụng thật, sơ đồ và biểu đồ dùng trong báo cáo."),
    ], [7.1, 8.9])
    prose(doc, "Bộ kiểm thử có mã nguồn trong BE/tests/test_software.py và test_submission_regressions.py. Chương trình ghi kết quả nằm ở app/scripts/submission_tests.py và submission_ai_review.py; kiểm tra trình duyệt nằm ở reports/tools/browser_checks.py. Đây là vị trí hiện vật phục vụ đối chiếu khi chấm, không phải một tài liệu hướng dẫn quy trình kiểm thử. Nhật ký lưu nguyên trạng thái chạy, kể cả lỗi hoặc ca bỏ qua nếu có.")
    p = doc.add_heading("A.2. Danh mục bài tập có cấu trúc", 2)
    p.paragraph_format.page_break_before = True
    exercises = json.loads((PROJECT / "BE/data/curated/exercises.json").read_text(encoding="utf-8"))
    table(doc, "Bảng A.2. Mười một bài tập trong kho biên soạn", ["ID", "Tên bài", "Dụng cụ"],
          [(e['id'], e['name'], e['equipment']) for e in exercises], [4.1, 7.2, 4.7])
    prose(doc, "Đối tượng của ứng dụng là người mới, nhưng không phải mọi bài trong danh mục đều được ACE xếp mức Beginner. Ví dụ Front Plank có mức độ tại nguồn cần được cân nhắc theo khả năng người tập. Việc sử dụng các bài thay thế trong lịch là quy tắc của dự án; không mặc định các bài đó có cùng tác động sinh cơ học hoặc cùng độ khó.")
    doc.save(REPORTS / "Tieu_luan_AI_4GYM_CT07PM.docx")


def workbook(software, browser, before, after, ai, history):
    wb = Workbook()
    overview = wb.active
    overview.title = "Tong quan"
    rows = [("AI-4GYM — BỘ KIỂM THỬ VÀ ĐÁNH GIÁ CHATBOT", ""),
            ("Ngày kiểm tra", DATE), ("Commit nền", software['git_commit']),
            ("Backend — số phương thức chạy", software['summary']['tests_run']),
            ("Backend — đạt", software['summary']['passed']), ("Backend — fail/error", software['summary']['failed']+software['summary']['errors']),
            ("Backend — bỏ qua", software['summary']['skipped']),
            ("Trình duyệt — đạt/tổng", f"{browser['summary']['passed']}/{browser['summary']['total']}"),
            ("Hồi quy trước sửa — đạt/tổng", f"{before['summary']['passed']}/7"),
            ("Hồi quy sau sửa — đạt/tổng", f"{after['summary']['passed']}/7"),
            ("Build frontend", software['frontend_build']['status']),
            ("Toàn vẹn dữ liệu", software['artifact_audit']['artifact_integrity']),
            ("Nội dung Chroma", software['index_content_audit']['status']),
            ("Chatbot hỏi mới — số tình huống", ai['summary']['scenarios']),
            ("Chatbot hỏi mới — số lượt", ai['summary']['user_turns']),
            ("Điều kiện chức năng đạt", ai['summary']['contract_passed']),
            ("Chú ý", "Điểm AI, kết quả phần mềm và nhãn duyệt tay là ba loại bằng chứng khác nhau."),
            ("Hồ sơ 193 câu", "Giữ nguyên dữ liệu remote; không dùng làm số đo lại toàn bộ phiên bản đã sửa."),
            ("Mã nguồn được kiểm tra", "Hash từng tệp nằm trong software_test_results.json và chatbot_ai_review.json."),
            ("Phạm vi", "Bản demo học phần; chưa kiểm định y khoa, tải nhiều người dùng hoặc WCAG đầy đủ.")]
    for row in rows:
        overview.append(row)
    sheets = {
        "Ca phan mem": (["Mã ca", "Nội dung", "Tiền điều kiện", "Đầu vào và thao tác kiểm tra", "Kết quả mong đợi", "Kết quả thực tế", "Trạng thái", "Test ID", "Thời gian (s)", "Chi tiết lỗi"],
            [(*describe(c), 'Các assertion về trạng thái, dữ liệu và tác động đều thỏa; đối chiếu test_id và log thực thi.' if c['status']=='PASS' else '\n'.join(c['details']),
              c['status'], c['test_id'], c.get('seconds'), '\n'.join(c['details'])) for c in software['cases']]),
        "Ca trinh duyet": (["Mã", "Kịch bản / kết quả mong đợi", "Kết quả", "Giây", "Chi tiết"],
            [(c['id'], c['description'], c['status'], c['seconds'], c['details']) for c in browser['cases']]),
        "Loi va hoi quy": (["Mã", "Mức ảnh hưởng", "Lỗi trước sửa", "Điều chỉnh", "Trước", "Sau"],
            [(bid, severity, issue, fix, "FAIL", "PASS") for bid, severity, issue, fix in BUGS]),
        "Chatbot AI moi": (["Mã", "Nhóm", "Các lượt hỏi", "Tiêu chí nội dung tham chiếu", "Câu trả lời cuối", "Điều kiện", "Điểm AI", "Lý do AI", "Thời gian judge (s)"],
            [(c['id'], c['category'], "\n".join(c['messages']), c['reference'], c['turns'][-1].get('answer'),
              "PASS" if c['contract_passed'] else "FAIL", c.get('judge_score'), c.get('judge_reason',c.get('judge_error')), c.get('judge_seconds')) for c in ai['cases']]),
        "Tung luot chatbot": (["Mã", "Lượt", "Câu hỏi", "Phản hồi thực tế", "Refused", "ID nguồn", "Nguồn URL", "Giây chatbot"],
            [(c['id'], t['turn'], t['message'], t.get('answer',t.get('error')), t.get('refused'),
              "\n".join(s['id'] for s in t.get('sources',[])), "\n".join(s['source'] for s in t.get('sources',[])), t['chatbot_seconds'])
             for c in ai['cases'] for t in c['turns']]),
    }
    test = {r['id']: r for r in json.loads((PROJECT / 'BE/data/processed/test.json').read_text(encoding='utf-8'))}
    sheets['193 cau ban giao'] = (["ID", "Câu hỏi", "Đáp án tham chiếu", "Phản hồi đã lưu", "Điểm AI cũ", "Judge version", "Lý do đã lưu", "Nguồn", "Loại đo thời gian"],
        [(r['id'], test[r['id']]['question'], test[r['id']]['answer'], r['answer'], r['judge_score'], r.get('judge_version'), r.get('judge_reason'),
          "\n".join(s['id'] for s in r.get('sources',[])), r.get('seconds_measurement','Không ghi loại phép đo')) for r in history])
    independent = read('independent_ai_review.json')
    sheets['Ra soat AI bo sung'] = (["Mã", "Nhận định rà soát", "Vấn đề / phạm vi kết luận"],
        [(c['id'], c['status'], c['finding']) for c in independent['cases']])
    for name, (headers, data) in sheets.items():
        ws = wb.create_sheet(name)
        ws.append(headers)
        for row in data:
            ws.append(row)
        ws.freeze_panes = "C2"
        ws.auto_filter.ref = ws.dimensions
        ws.print_title_rows = "1:1"
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.row_dimensions[1].height = 32
        for col in ws.columns:
            label = str(col[0].value)
            width = 55 if any(s in label.lower() for s in ('câu', 'phản hồi', 'tiêu chí', 'đáp án','lỗi','nội dung','kịch bản','lý do','điều chỉnh')) else 22
            if 'Test ID' in label:
                width = 75
            ws.column_dimensions[col[0].column_letter].width = width
        for row in ws.iter_rows(min_row=2):
            ws.row_dimensions[row[0].row].height = 65
    overview.column_dimensions['A'].width = 48
    overview.column_dimensions['B'].width = 105
    for ws in wb:
        ws.sheet_view.showGridLines = False
        for cell in ws[1]:
            cell.fill = PatternFill('solid',fgColor=NAVY)
            cell.font = Font(name='Aptos',size=11,bold=True,color='FFFFFF')
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.font = Font(name='Aptos',size=11)
                cell.alignment = Alignment(vertical='top',wrap_text=True)
                if cell.data_type == 'f':
                    cell.data_type = 's'
                if cell.value in ('PASS', 'FAIL'):
                    cell.fill = PatternFill('solid',fgColor='E2F0D9' if cell.value=='PASS' else 'FCE4D6')
                elif cell.row % 2 == 0:
                    cell.fill = PatternFill('solid',fgColor='F3F6F3')
    wb.save(REPORTS / 'Bo_kiem_thu_AI_4GYM.xlsx')


def main():
    software, browser = read('software_test_results.json'), read('browser_test_results.json')
    before, after, ai = read('regressions_before.json'), read('regressions_after.json'), read('chatbot_ai_review.json')
    assert 'summary' in ai, 'Đánh giá AI chưa hoàn tất'
    assert len(ai['cases']) == 12, 'Thiếu tình huống AI'
    history = [json.loads(line) for line in (REPORTS/'evaluation_results.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    old = load_workbook(REPORTS/'AI-4GYM_train_test_report.xlsx',read_only=True)
    manual = Counter(row[12] for row in old['Danh gia Test'].iter_rows(min_row=2,values_only=True))
    old.close()
    diagrams(Counter(r['judge_score'] for r in history))
    build_main(software,browser,before,after,ai,history,manual)
    doc = make_document('BÁO CÁO KIỂM THỬ PHẦN MỀM', 'Kèm kết quả rà soát chatbot bằng AI — 25/11/2026')
    toc(doc)
    chapter(doc, '1. KẾT QUẢ KIỂM THỬ PHẦN MỀM')
    software_sections(doc,software,browser,before,after,number='1')
    chapter(doc, '2. ĐÁNH GIÁ CHATBOT')
    ai_sections(doc,ai,history,manual,number='2')
    chapter(doc, '3. HỒ SƠ BÀN GIAO')
    prose(doc,'Bảng ca kiểm thử và phản hồi đầy đủ nằm trong Bo_kiem_thu_AI_4GYM.xlsx. Các tệp JSON/TXT trong reports/results/ lưu kết quả chạy thực tế, thời điểm, ID ca và định danh phiên bản. Tieu_luan_AI_4GYM_CT07PM.docx trình bày cơ sở lý thuyết, thiết kế, triển khai và kết quả kiểm thử trong một báo cáo học phần hoàn chỉnh. Báo cáo này tổng hợp kết quả và lỗi đã xử lý; không chứa phần hướng dẫn quy trình kiểm thử.')
    doc.save(REPORTS/'Bao_cao_kiem_thu_AI_4GYM.docx')
    workbook(software,browser,before,after,ai,history)
    print('Created main report, software test report and test workbook.')


if __name__ == '__main__':
    main()
