from __future__ import annotations

import json
import os
import re

from .gemini_client import configured, generate_text
from .schemas import WorkoutPlan


FALLBACK_PLAN = {
    "days": [
        {
            "day": "Day 1",
            "focus": "Full Body Foundation",
            "warm_up": "5–10 minutes of easy walking and dynamic mobility.",
            "exercises": [
                {"name": "Bodyweight Squat", "sets": 3, "reps": "10–12", "duration": None, "rest": "60–90 sec"},
                {"name": "Incline Push-up", "sets": 3, "reps": "8–12", "duration": None, "rest": "60–90 sec"},
                {"name": "Glute Bridge", "sets": 3, "reps": "12–15", "duration": None, "rest": "60 sec"},
            ],
            "cooldown": "5 minutes of relaxed walking and gentle stretching.",
        },
        {
            "day": "Day 2",
            "focus": "Cardio and Mobility",
            "warm_up": "5 minutes of easy walking.",
            "exercises": [
                {"name": "Brisk Walk", "sets": None, "reps": None, "duration": "20–30 min", "rest": "As needed"},
                {"name": "Hip Mobility", "sets": 2, "reps": "8 each side", "duration": None, "rest": "30 sec"},
                {"name": "Thoracic Rotation", "sets": 2, "reps": "8 each side", "duration": None, "rest": "30 sec"},
            ],
            "cooldown": "5–10 minutes of gentle mobility.",
        },
        {
            "day": "Day 3",
            "focus": "Upper Body",
            "warm_up": "5–10 minutes of shoulder and upper-body mobility.",
            "exercises": [
                {"name": "Incline Push-up", "sets": 3, "reps": "8–12", "duration": None, "rest": "60–90 sec"},
                {"name": "Backpack Row", "sets": 3, "reps": "10–12", "duration": None, "rest": "60–90 sec"},
                {"name": "Pike Push-up", "sets": 2, "reps": "6–10", "duration": None, "rest": "90 sec"},
            ],
            "cooldown": "Gentle chest, back and shoulder stretches.",
        },
        {
            "day": "Day 4",
            "focus": "Recovery",
            "warm_up": "5 minutes of easy movement.",
            "exercises": [
                {"name": "Easy Walk", "sets": None, "reps": None, "duration": "20 min", "rest": "As needed"},
                {"name": "Full-body Mobility", "sets": 2, "reps": "5–8 each movement", "duration": None, "rest": "30 sec"},
            ],
            "cooldown": "Relaxed breathing and gentle stretching.",
        },
        {
            "day": "Day 5",
            "focus": "Lower Body",
            "warm_up": "5–10 minutes of walking and leg mobility.",
            "exercises": [
                {"name": "Bodyweight Squat", "sets": 3, "reps": "10–15", "duration": None, "rest": "60–90 sec"},
                {"name": "Reverse Lunge", "sets": 3, "reps": "8–10 each side", "duration": None, "rest": "60–90 sec"},
                {"name": "Calf Raise", "sets": 3, "reps": "12–15", "duration": None, "rest": "60 sec"},
            ],
            "cooldown": "Gentle quadriceps, hamstring and calf stretching.",
        },
        {
            "day": "Day 6",
            "focus": "Core and Light Cardio",
            "warm_up": "5 minutes of easy walking.",
            "exercises": [
                {"name": "Dead Bug", "sets": 3, "reps": "8–10 each side", "duration": None, "rest": "45–60 sec"},
                {"name": "Bird Dog", "sets": 3, "reps": "8–10 each side", "duration": None, "rest": "45–60 sec"},
                {"name": "Easy Cardio", "sets": None, "reps": None, "duration": "15–20 min", "rest": "As needed"},
            ],
            "cooldown": "5 minutes of gentle stretching.",
        },
        {
            "day": "Day 7",
            "focus": "Rest and Recovery",
            "warm_up": "Optional 5-minute easy walk.",
            "exercises": [
                {"name": "Rest Day", "sets": None, "reps": None, "duration": "Full day", "rest": "Focus on recovery"},
            ],
            "cooldown": "Hydrate, sleep well and use gentle mobility if comfortable.",
        },
    ]
}


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def _fallback(goal: str, intensity: str) -> WorkoutPlan:
    data = json.loads(json.dumps(FALLBACK_PLAN))
    if goal.lower() in {"weight loss", "fat loss"}:
        data["days"][1]["focus"] = "Cardio and Conditioning"
        data["days"][5]["focus"] = "Core and Moderate Cardio"
    elif "muscle" in goal.lower():
        data["days"][0]["focus"] = "Full Body Strength"
        data["days"][4]["focus"] = "Lower Body Strength"
    if intensity == "low":
        for day in data["days"]:
            for ex in day["exercises"]:
                if ex.get("sets"):
                    ex["sets"] = max(1, ex["sets"] - 1)
    return WorkoutPlan.model_validate(data)


def generate_workout_gemini(
    username: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
) -> WorkoutPlan:
    model = os.getenv("GEMINI_PRO_MODEL", "gemini-3.1-pro")
    prompt = f"""
You are FitBuddy, an AI fitness-plan generator.

Create a safe, practical 7-day workout plan for:
- Name: {username}
- Age: {age}
- Weight: {weight} kg
- Goal: {goal}
- Intensity: {intensity}

Return ONLY valid JSON with this exact shape:
{{
  "days": [
    {{
      "day": "Day 1",
      "focus": "string",
      "warm_up": "5–10 minute warm-up",
      "exercises": [
        {{
          "name": "exercise",
          "sets": 3,
          "reps": "10–12",
          "duration": null,
          "rest": "60–90 sec"
        }}
      ],
      "cooldown": "string"
    }}
  ]
}}

Requirements:
- Exactly 7 days.
- Include warm-up, main workout exercises, sets/reps or duration, rest, and cooldown/recovery.
- Match the selected goal and intensity.
- Include at least one recovery/rest-oriented day.
- Do not diagnose conditions or prescribe medical treatment.
- Do not recommend dangerous, extreme, or intentionally painful exercise.
- Keep the plan understandable for a general user.
"""
    if not configured():
        return _fallback(goal, intensity)

    try:
        raw = generate_text(prompt, model, json_mode=True)
        return WorkoutPlan.model_validate(_extract_json(raw))
    except Exception:
        return _fallback(goal, intensity)
