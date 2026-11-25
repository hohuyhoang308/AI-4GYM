"""Real Edge browser acceptance checks against the local app; no mocked successes."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import traceback
from uuid import uuid4

from playwright.sync_api import sync_playwright, expect


PROJECT = Path(__file__).resolve().parents[2]
OUTPUT = PROJECT / "reports" / "results" / "browser_test_results.json"
IMAGES = PROJECT / "reports" / "evidence"
sys.path.insert(0, str(PROJECT / "BE"))


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(exist_ok=True)
    report = {"created_at": datetime.now(timezone.utc).isoformat(),
              "base_url": "http://127.0.0.1:8000", "browser": "Microsoft Edge headless",
              "cases": [], "page_errors": []}
    email = f"browser-qa-{uuid4().hex}@example.com"
    password = "qa-" + uuid4().hex
    user_id = None
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="vi-VN")
        page = context.new_page()
        page.on("pageerror", lambda error: report["page_errors"].append(str(error)))
        page.goto(report["base_url"], wait_until="networkidle")
        page.get_by_role("button", name="Đăng nhập", exact=False).first.wait_for()

        def check(case_id, description, action):
            started = time.monotonic()
            try:
                action()
                status, detail = "PASS", ""
            except Exception:
                status, detail = "FAIL", traceback.format_exc()
                page.screenshot(path=str(IMAGES / f"{case_id}_failure.png"), full_page=True)
            report["cases"].append({"id": case_id, "description": description,
                "status": status, "details": detail, "seconds": round(time.monotonic() - started, 3)})
            OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(case_id, status, flush=True)

        def desktop():
            expect(page.get_by_role("heading", level=1)).to_contain_text("Tập đúng hôm nay")
            expect(page.get_by_role("button", name="Gửi câu hỏi")).to_be_disabled()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert page.get_by_role("textbox", name="Nhập câu hỏi").get_attribute("maxlength") == "1000"
            page.screenshot(path=str(IMAGES / "ui_desktop.png"), full_page=True)

        def guest_chat():
            page.get_by_role("textbox", name="Nhập câu hỏi").fill("Gợi ý lịch tập 3 buổi không dụng cụ")
            page.get_by_role("textbox", name="Nhập câu hỏi").press("Enter")
            expect(page.locator(".assistant-message")).to_contain_text("Lịch 3 buổi/tuần", timeout=30000)
            expect(page.get_by_text("nguồn tham khảo", exact=False)).to_be_visible()
            page.get_by_text("nguồn tham khảo", exact=False).click()
            expect(page.locator(".sources-content")).to_be_visible()
            page.screenshot(path=str(IMAGES / "ui_chat.png"), full_page=True)

        def guest_refresh():
            page.reload(wait_until="networkidle")
            expect(page.locator(".assistant-message")).to_have_count(0)
            expect(page.get_by_role("heading", level=1)).to_be_visible()

        def mismatch():
            page.locator(".topbar-login").click()
            page.get_by_role("tab", name="Đăng ký").click()
            page.get_by_label("Tên hiển thị", exact=True).fill("Kiểm thử trình duyệt")
            page.get_by_label("Email", exact=True).fill(email)
            page.get_by_label("Mật khẩu", exact=True).fill(password)
            page.get_by_label("Xác nhận mật khẩu", exact=True).fill("different-password")
            page.get_by_role("button", name="Tạo tài khoản").click()
            expect(page.get_by_role("alert")).to_contain_text("chưa khớp")
            page.screenshot(path=str(IMAGES / "ui_auth_validation.png"), full_page=True)

        def registration_history():
            nonlocal user_id
            page.get_by_label("Xác nhận mật khẩu", exact=True).fill(password)
            page.get_by_role("button", name="Tạo tài khoản").click()
            expect(page.get_by_role("dialog")).to_have_count(0)
            user_id = context.request.get(report["base_url"] + "/auth/me").json()["id"]
            page.get_by_role("textbox", name="Nhập câu hỏi").fill("Gợi ý lịch tập 2 buổi tại nhà")
            page.get_by_role("button", name="Gửi câu hỏi").click()
            expect(page.locator(".assistant-message")).to_contain_text("Lịch 2 buổi/tuần", timeout=30000)
            page.reload(wait_until="networkidle")
            expect(page.locator(".assistant-message")).to_contain_text("Lịch 2 buổi/tuần")
            expect(page.locator(".history-item")).to_have_count(1)

        def rename_delete():
            page.locator(".history-more").click()
            page.get_by_role("button", name="Đổi tên", exact=True).click()
            page.get_by_role("textbox", name="Tên hội thoại mới").fill("Lịch kiểm thử đã đổi tên")
            page.get_by_role("textbox", name="Tên hội thoại mới").press("Enter")
            expect(page.locator(".history-title")).to_have_text("Lịch kiểm thử đã đổi tên")
            page.reload(wait_until="networkidle")
            expect(page.locator(".history-title")).to_have_text("Lịch kiểm thử đã đổi tên")
            page.on("dialog", lambda dialog: dialog.accept())
            page.locator(".history-more").click()
            page.get_by_role("button", name="Xóa hội thoại", exact=True).click()
            expect(page.locator(".history-item")).to_have_count(0)
            expect(page.locator(".assistant-message")).to_have_count(0)

        def logout_login():
            page.get_by_role("button", name="Đăng xuất").click()
            expect(page.locator(".guest-account")).to_be_visible()
            assert context.request.get(report["base_url"] + "/auth/me").status == 401
            page.locator(".topbar-login").click()
            page.get_by_label("Email", exact=True).fill(email)
            page.get_by_label("Mật khẩu", exact=True).fill("invalid-password")
            page.locator(".auth-submit").click()
            expect(page.get_by_role("alert")).to_contain_text("không đúng")
            page.get_by_label("Mật khẩu", exact=True).fill(password)
            page.locator(".auth-submit").click()
            expect(page.get_by_role("dialog")).to_have_count(0)
            expect(page.get_by_role("button", name="Đăng xuất")).to_be_visible()
            page.get_by_role("button", name="Đăng xuất").click()
            expect(page.locator(".guest-account")).to_be_visible()

        def failed_request_restores_input():
            page.route("**/chat", lambda route: route.fulfill(status=503, content_type="application/json",
                                                             body=json.dumps({"detail": "QA simulated unavailable"})))
            try:
                box = page.get_by_role("textbox", name="Nhập câu hỏi")
                box.fill("Câu hỏi kiểm thử khi dịch vụ lỗi")
                page.get_by_role("button", name="Gửi câu hỏi").click()
                expect(page.get_by_role("alert")).to_contain_text("QA simulated unavailable")
                expect(box).to_have_value("Câu hỏi kiểm thử khi dịch vụ lỗi")
                expect(page.locator(".user-bubble")).to_have_count(0)
                box.fill("")
            finally:
                page.unroute("**/chat")

        def mobile():
            page.set_viewport_size({"width": 390, "height": 844})
            page.reload(wait_until="networkidle")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            expect(page.get_by_role("button", name="Mở thanh bên")).to_be_visible()
            page.get_by_role("button", name="Mở thanh bên").click()
            expect(page.locator(".sidebar")).to_have_class("sidebar sidebar-open")
            page.locator(".sidebar-close").click()
            expect(page.locator(".sidebar")).not_to_have_class("sidebar sidebar-open")
            page.wait_for_function("document.querySelector('.sidebar').getBoundingClientRect().right <= 1")
            expect(page.get_by_role("textbox", name="Nhập câu hỏi")).to_be_in_viewport()
            page.screenshot(path=str(IMAGES / "ui_mobile_390.png"), full_page=True)

        def keyboard():
            box = page.get_by_role("textbox", name="Nhập câu hỏi")
            box.fill("Dòng một")
            box.press("Shift+Enter")
            expect(box).to_have_value("Dòng một\n")
            box.fill("")
            page.locator(".topbar-login").click()
            expect(page.get_by_role("dialog")).to_be_visible()
            page.keyboard.press("Escape")
            expect(page.get_by_role("dialog")).to_have_count(0)

        try:
            for case_id, description, action in [
                ("UI-01", "Desktop 1440px, ô nhập, nút gửi và không tràn ngang", desktop),
                ("UI-02", "Chat khách bằng Enter và mở nguồn tham khảo", guest_chat),
                ("UI-03", "F5 xóa hội thoại khách", guest_refresh),
                ("UI-04", "Báo lỗi xác nhận mật khẩu không khớp", mismatch),
                ("UI-05", "Đăng ký và F5 khôi phục lịch sử từ MySQL", registration_history),
                ("UI-06", "Đổi tên, F5 giữ tên và xóa hội thoại", rename_delete),
                ("UI-07", "Đăng xuất, báo sai mật khẩu và đăng nhập lại", logout_login),
                ("UI-08", "Lỗi HTTP 503 khôi phục nội dung người dùng", failed_request_restores_input),
                ("UI-09", "Mobile 390px không tràn ngang, menu và ô nhập hoạt động", mobile),
                ("UI-10", "Shift+Enter xuống dòng và Escape đóng đăng nhập", keyboard),
            ]:
                check(case_id, description, action)
        finally:
            # Remove only the unique account created by this run.
            from sqlalchemy import select
            from app.db.models import User
            from app.db.session import SessionLocal
            with SessionLocal() as db:
                created = db.scalar(select(User).where(User.email == email))
                if created is not None:
                    db.delete(created)
                    db.commit()
            context.close()
            browser.close()
        report["summary"] = {"total": len(report["cases"]),
            "passed": sum(c["status"] == "PASS" for c in report["cases"]),
            "failed": sum(c["status"] == "FAIL" for c in report["cases"]),
            "page_errors": len(report["page_errors"])}
        OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report["summary"]), flush=True)
        raise SystemExit(0 if not report["summary"]["failed"] else 1)


if __name__ == "__main__":
    main()
