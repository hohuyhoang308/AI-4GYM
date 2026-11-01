from fastapi import APIRouter, HTTPException, Query

from app.services.knowledge import load_exercises, matching_exercises
from app.services.plans import make_plan


router = APIRouter(tags=["catalog"])


@router.get("/exercises")
def exercises(muscle: str | None = None) -> list[dict]:
    return matching_exercises(muscle)


@router.get("/exercises/{exercise_id}")
def exercise_detail(exercise_id: str) -> dict:
    for exercise in load_exercises():
        if exercise["id"] == exercise_id:
            return exercise
    raise HTTPException(status_code=404, detail="Không tìm thấy bài tập")


@router.get("/plans")
def plan(days: int = Query(ge=1, le=6)) -> dict:
    return make_plan(days)
