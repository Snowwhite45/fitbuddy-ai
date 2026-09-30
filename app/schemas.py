from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


Intensity = Literal["low", "medium", "high"]


class UserInput(BaseModel):
    username: str = Field(min_length=2, max_length=120)
    user_id: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=20, le=400)
    goal: str = Field(min_length=2, max_length=120)
    intensity: Intensity

    @field_validator("username", "user_id", "goal")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be empty")
        return value


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    feedback: str = Field(min_length=3, max_length=2000)

    @field_validator("user_id", "feedback")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be empty")
        return value


class WorkoutExercise(BaseModel):
    name: str
    sets: int | None = None
    reps: str | None = None
    duration: str | None = None
    rest: str | None = None


class WorkoutDay(BaseModel):
    day: str
    focus: str
    warm_up: str
    exercises: list[WorkoutExercise]
    cooldown: str


class WorkoutPlan(BaseModel):
    days: list[WorkoutDay]


class GenerationResponse(BaseModel):
    user_id: str
    plan: WorkoutPlan
    nutrition_tip: str
