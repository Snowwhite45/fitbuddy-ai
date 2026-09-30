from __future__ import annotations

import os

from .gemini_client import configured, generate_text


def generate_nutrition_tip_with_flash(goal: str) -> str:
    model = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.6-flash")
    prompt = f"""
You are FitBuddy's nutrition and recovery assistant.
User fitness goal: {goal}

Give ONE concise, practical nutrition or recovery tip that supports this goal.
Mention realistic food/recovery habits. Avoid diagnosis, medication, extreme dieting,
guaranteed outcomes, or individualized medical treatment. Keep it under 100 words.
Return plain text only.
"""
    if not configured():
        return (
            f"For {goal}, build consistent meals around protein-rich foods, "
            "vegetables or fruit, adequate fluids, and enough total food to support "
            "your training. Prioritize sleep and recovery as part of the plan."
        )

    try:
        return generate_text(prompt, model)
    except Exception:
        return (
            f"For {goal}, focus on balanced meals, adequate protein, hydration, "
            "and sufficient recovery rather than extreme dietary changes."
        )
