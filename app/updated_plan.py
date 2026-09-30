from __future__ import annotations

import json
import os
import re

from .gemini_client import configured, generate_text
from .gemini_generator import _fallback
from .schemas import WorkoutPlan


def update_workout_plan(
    original_plan: str,
    feedback: str,
    goal: str,
    intensity: str,
) -> WorkoutPlan:
    model = os.getenv("GEMINI_PRO_MODEL", "gemini-3.1-pro")
    prompt = f"""
You are updating a FitBuddy 7-day fitness plan.

Goal: {goal}
Intensity: {intensity}

Original plan:
{original_plan}

User feedback:
{feedback}

Return ONLY valid JSON with:
{{
  "days": [
    {{
      "day": "Day 1",
      "focus": "string",
      "warm_up": "string",
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

Keep exactly 7 days. Apply the feedback where it is safe and reasonable.
Do not diagnose medical conditions, prescribe treatment, or suggest dangerous exercise.
"""
    if not configured():
        plan = _fallback(goal, intensity)
        if feedback:
            plan.days[0].focus = f"Adjusted: {plan.days[0].focus}"
            plan.days[0].cooldown += f" Feedback considered: {feedback[:180]}"
        return plan

    try:
        raw = generate_text(prompt, model, json_mode=True)
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return WorkoutPlan.model_validate(json.loads(cleaned))
    except Exception:
        return _fallback(goal, intensity)
