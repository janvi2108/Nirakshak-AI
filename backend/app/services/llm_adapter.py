import logging
import json
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


def chat_completion(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 200, temperature: float = 0.0) -> str:
    """Generic chat completion adapter.

    Prefers GROQ if `settings.groq_api_key` and `settings.groq_api_url` are set.
    Otherwise falls back to OpenAI Python client (existing behaviour).
    The GROQ call is a simple HTTP POST to `groq_api_url` and expects a JSON
    response with a `text` or similar field; adapt `response_text` extraction
    as needed for your Groq endpoint.
    """
    # Try GROQ first
    if settings.groq_api_key and settings.groq_api_url:
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            }
            # Use OpenAI-compatible chat payload (messages) for GROQ chat endpoint
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            resp = requests.post(settings.groq_api_url, headers=headers, data=json.dumps(payload), timeout=30)
            resp.raise_for_status()
            data = resp.json()
            # Try common fields to extract text - adapt if your GROQ API differs
            if isinstance(data, dict):
                for key in ("text", "response", "output", "choices"):
                    if key in data and data[key]:
                        if key == "choices" and isinstance(data["choices"], list):
                            first = data["choices"][0]
                            return first.get("text") or first.get("message") or json.dumps(first)
                        return data[key]
            return str(data)
        except Exception as e:
            logger.warning(f"GROQ request failed: {e}")

    # Fallback: OpenAI client (existing behaviour)
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"OpenAI call failed: {e}")
        raise
