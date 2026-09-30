from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=1)
def get_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    from google import genai

    return genai.Client(api_key=api_key)


def configured() -> bool:
    return get_client() is not None


def generate_text(prompt: str, model: str, *, json_mode: bool = False) -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("Gemini API key is not configured.")

    from google.genai import types

    config = types.GenerateContentConfig(
        temperature=0.4,
        max_output_tokens=6000,
        response_mime_type="application/json" if json_mode else None,
    )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text.strip()
