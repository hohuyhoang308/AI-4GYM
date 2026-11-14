import unittest
from app.services.chat import ChatService
from app.services.plans import make_plan


class MultiTurnFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ChatService()

    def test_multi_turn_home_leg_workout_then_no_equipment(self) -> None:
        session_id = None

        # Turn 1: User asks for leg workout at home
        reply1 = self.service.ask("Tôi muốn tập chân tại nhà.", session_id=session_id)
        session_id = reply1["session_id"]
        self.assertFalse(reply1["refused"])
        self.assertIn("chân", reply1["answer"].lower())
        self.assertIn("squat", reply1["answer"].lower())

        # Turn 2: User says they don't have equipment
        reply2 = self.service.ask("Tôi không có dụng cụ.", session_id=session_id)
        self.assertFalse(reply2["refused"])
        self.assertTrue(any(k in reply2["answer"].lower() for k in ("dụng cụ", "bodyweight", "trọng lượng cơ thể", "squat", "nhà")))

        # Turn 3: User mentions knee pain
        reply3 = self.service.ask("Tôi bị đau khớp gối thì sao?", session_id=session_id)
        self.assertFalse(reply3["refused"])
        self.assertIn("gối", reply3["answer"].lower())
        self.assertTrue(any(k in reply3["answer"].lower() for k in ("dừng", "đau", "nghỉ", "khớp")))

    def test_proactive_clarification_on_generic_request(self) -> None:
        reply = self.service.ask("Tư vấn lịch tập cho tôi")
        self.assertFalse(reply["refused"])
        self.assertIn("Thời gian", reply["answer"])
        self.assertIn("Địa điểm & Dụng cụ", reply["answer"])
        self.assertIn("Mục tiêu chính", reply["answer"])

    def test_personalized_plan_generation(self) -> None:
        # 3 days bodyweight at home
        plan_bw = make_plan(days=3, equipment="home_bodyweight", goal="giam_mo")
        self.assertIn("Không dụng cụ", plan_bw["split"])
        self.assertIn("150 phút", plan_bw["guidance"])

        # 4 days gym hypertrophy
        plan_gym = make_plan(days=4, equipment="gym", goal="tang_co")
        self.assertIn("Upper/Lower", plan_gym["split"])
        self.assertIn("quá tải tiến triển", plan_gym["guidance"])

        # Knee limitation
        plan_knee = make_plan(days=3, limitations=["knee"])
        self.assertIn("khớp gối", plan_knee["guidance"])
        for day in plan_knee["schedule"]:
            ex_names = [e["name"] for e in day["exercises"]]
            self.assertNotIn("Đạp chân trên máy", ex_names)


if __name__ == "__main__":
    unittest.main()
