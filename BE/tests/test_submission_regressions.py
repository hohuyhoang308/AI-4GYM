"""Regression cases discovered during the 25/11/2026 submission review."""

import unittest
from unittest.mock import Mock, patch

from app.scripts.export_report import load_verified_data
from app.services.knowledge import load_exercises
from app.services.plans import make_plan
from app.services.scope import detect_equipment
import test_software


class SubmissionRegressionTest(unittest.TestCase):
    def test_dumbbell_plan_does_not_require_machines_or_bands(self):
        """RG-01: Chỉ có tạ đơn không được gợi ý máy tập hoặc dây kháng lực."""
        exercises = {e["id"]: e for e in load_exercises()}
        for days in range(1, 7):
            with self.subTest(days=days):
                plan = make_plan(days, equipment="home_dumbbell")
                equipment = [exercises[e["id"]]["equipment"] for d in plan["schedule"] for e in d["exercises"]]
                self.assertFalse(any("Máy" in item or "Dây" in item for item in equipment), equipment)

    def test_gym_location_takes_precedence_over_equipment_mention(self):
        """RG-02: Phòng gym có tạ đơn vẫn được nhận diện là phòng gym."""
        self.assertEqual(detect_equipment("Tôi tập ở phòng gym có tạ đơn và đầy đủ dụng cụ"), "gym")

    def test_latest_equipment_persists_across_next_turn(self):
        """RG-03: Điều kiện dụng cụ mới nhất phải được giữ ở lượt kế tiếp."""
        service = test_software.SoftwareChatLogicTest().service()
        first = service.ask("Gợi ý lịch tập 3 buổi không dụng cụ")
        second = service.ask("Bây giờ tôi có tạ đơn tại nhà", first["session_id"])
        third = service.ask("Gợi ý lịch tập 4 buổi", second["session_id"])
        self.assertIn("Tạ đơn", third["answer"])
        self.assertNotIn("Không dụng cụ", third["answer"])

    def test_equipment_refinement_rebuilds_previous_plan(self):
        """RG-04: Đổi dụng cụ sau lịch 3 buổi phải tạo lại lịch 3 buổi."""
        service = test_software.SoftwareChatLogicTest().service()
        first = service.ask("Gợi ý lịch tập 3 buổi ở phòng gym")
        reply = service.ask("Tôi không có dụng cụ", first["session_id"])
        self.assertIn("Lịch 3 buổi/tuần", reply["answer"])
        self.assertIn("Không dụng cụ", reply["answer"])
        service.chain.invoke.assert_not_called()

    def test_latest_goal_persists_across_next_turn(self):
        """RG-05: Đổi từ giảm mỡ sang tăng cơ không dùng lại mục tiêu cũ."""
        service = test_software.SoftwareChatLogicTest().service()
        first = service.ask("Gợi ý lịch tập 3 buổi giảm mỡ")
        second = service.ask("Tôi muốn chuyển sang tăng cơ", first["session_id"])
        reply = service.ask("Gợi ý lịch tập 4 buổi", second["session_id"])
        self.assertIn("Mục tiêu tăng cơ", reply["answer"])
        self.assertNotIn("Mục tiêu giảm mỡ", reply["answer"])

    def test_export_rejects_stale_index_instead_of_claiming_pass(self):
        """RG-06: Xuất báo cáo phải báo lỗi nếu Chroma không khớp dữ liệu train."""
        fake_store = Mock()
        fake_store.get.return_value = {"ids": ["unexpected-stale-id"]}
        with patch("app.scripts.export_report.vector_store", return_value=fake_store, create=True):
            with self.assertRaisesRegex(ValueError, "Chỉ mục Chroma"):
                load_verified_data()

    def test_shoulder_pain_does_not_generate_an_overhead_press_plan(self):
        """RG-07: Đau vai không tự động cấp lịch có đẩy vai; cần đánh giá y tế."""
        service = test_software.SoftwareChatLogicTest().service()
        reply = service.ask("Gợi ý lịch tập 4 buổi, tôi bị đau vai")
        self.assertNotIn("Đẩy vai trên máy", reply["answer"])
        self.assertTrue(any(term in reply["answer"].lower() for term in ("bác sĩ", "y tế")))


if __name__ == "__main__":
    unittest.main()
