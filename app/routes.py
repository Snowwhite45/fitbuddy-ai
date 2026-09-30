from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .database import (
    delete_user,
    get_all_plans,
    get_all_users,
    get_original_plan,
    get_user,
    save_plan,
    save_user,
    update_plan,
)
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .gemini_generator import generate_workout_gemini
from .schemas import FeedbackRequest, GenerationResponse, UserInput
from .updated_plan import update_workout_plan

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def plan_to_text(plan) -> str:
    return json.dumps(plan.model_dump(), indent=2, ensure_ascii=False)


def plan_from_text(value: str) -> dict:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {"raw": value}


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "FitBuddy – AI Fitness Plan Generator"},
    )


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    username: Annotated[str, Form()],
    user_id: Annotated[str, Form()],
    age: Annotated[int, Form()],
    weight: Annotated[float, Form()],
    goal: Annotated[str, Form()],
    intensity: Annotated[str, Form()],
):
    try:
        user = UserInput(
            username=username,
            user_id=user_id,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity.lower(),
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"title": "FitBuddy", "error": str(exc)},
            status_code=422,
        )

    plan = generate_workout_gemini(
        user.username, user.age, user.weight, user.goal, user.intensity
    )
    nutrition_tip = generate_nutrition_tip_with_flash(user.goal)

    save_user(
        user.username,
        user.user_id,
        user.age,
        user.weight,
        user.goal,
        user.intensity,
    )
    save_plan(user.user_id, plan_to_text(plan), nutrition_tip)

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "title": "Your FitBuddy Plan",
            "user": user,
            "plan": plan.model_dump(),
            "nutrition_tip": nutrition_tip,
            "message": None,
        },
    )


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(
    request: Request,
    user_id: Annotated[str, Form()],
    feedback: Annotated[str, Form()],
):
    request_data = FeedbackRequest(user_id=user_id, feedback=feedback)
    user = get_user(request_data.user_id)
    stored_plan = get_original_plan(request_data.user_id)

    if not user or not stored_plan:
        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "title": "FitBuddy",
                "error": "User ID or saved plan was not found.",
                "message": None,
            },
            status_code=404,
        )

    updated = update_workout_plan(
        stored_plan.original_plan,
        request_data.feedback,
        user.goal,
        user.intensity,
    )
    update_plan(
        request_data.user_id,
        plan_to_text(updated),
        request_data.feedback,
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "title": "Updated FitBuddy Plan",
            "user": user,
            "plan": updated.model_dump(),
            "nutrition_tip": stored_plan.nutrition_tip,
            "message": "Your workout plan has been updated using your feedback.",
            "feedback": request_data.feedback,
        },
    )


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request):
    users = get_all_users()
    plans = get_all_plans()
    latest_by_user = {}
    for plan in plans:
        latest_by_user.setdefault(plan.user_id, plan)

    rows = []
    for user in users:
        plan = latest_by_user.get(user.user_id)
        rows.append(
            {
                "user": user,
                "plan": plan,
                "original_plan": plan_from_text(plan.original_plan) if plan else None,
                "updated_plan": plan_from_text(plan.updated_plan) if plan and plan.updated_plan else None,
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={"title": "FitBuddy Admin", "rows": rows},
    )


@router.post("/delete-user/{user_id}")
def remove_user(user_id: str):
    delete_user(user_id)
    return RedirectResponse(url="/view-all-users", status_code=303)


@router.get("/health")
def health():
    return {"status": "ok", "service": "fitbuddy"}


@router.post("/api/generate-workout", response_model=GenerationResponse)
def api_generate_workout(user: UserInput):
    plan = generate_workout_gemini(
        user.username, user.age, user.weight, user.goal, user.intensity
    )
    tip = generate_nutrition_tip_with_flash(user.goal)
    save_user(
        user.username, user.user_id, user.age, user.weight, user.goal, user.intensity
    )
    save_plan(user.user_id, plan_to_text(plan), tip)
    return GenerationResponse(
        user_id=user.user_id, plan=plan, nutrition_tip=tip
    )


@router.post("/api/submit-feedback", response_model=GenerationResponse)
def api_submit_feedback(data: FeedbackRequest):
    user = get_user(data.user_id)
    stored_plan = get_original_plan(data.user_id)
    if not user or not stored_plan:
        raise HTTPException(status_code=404, detail="User or plan not found.")

    updated = update_workout_plan(
        stored_plan.original_plan, data.feedback, user.goal, user.intensity
    )
    update_plan(data.user_id, plan_to_text(updated), data.feedback)
    return GenerationResponse(
        user_id=data.user_id, plan=updated, nutrition_tip=stored_plan.nutrition_tip
    )


@router.get("/api/users")
def api_users():
    users = get_all_users()
    plans = get_all_plans()
    latest_by_user = {}
    for plan in plans:
        latest_by_user.setdefault(plan.user_id, plan)

    return [
        {
            "username": user.username,
            "user_id": user.user_id,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity,
            "original_plan": plan_from_text(latest_by_user[user.user_id].original_plan)
            if user.user_id in latest_by_user
            else None,
            "updated_plan": plan_from_text(latest_by_user[user.user_id].updated_plan)
            if user.user_id in latest_by_user and latest_by_user[user.user_id].updated_plan
            else None,
        }
        for user in users
    ]
