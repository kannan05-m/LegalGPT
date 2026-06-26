import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from legalgpt_backend.config import settings


SYSTEM_PROMPT = """You are LegalGPT, a legal document intelligence assistant.
You explain legal documents in plain English.
You are not a lawyer and do not provide legal advice.
Base every answer only on the provided document context.
If the document context does not contain the answer, say that the document does not specify it.
When possible, cite the clause, section, or paragraph used.
Return structured JSON when asked for JSON and no extra commentary."""


class GroqUnavailable(RuntimeError):
    pass


def _client():
    if not settings.groq_api_key:
        raise GroqUnavailable("GROQ_API_KEY is not configured.")
    try:
        from groq import Groq
    except ImportError as exc:
        raise GroqUnavailable("The groq package is not installed.") from exc
    return Groq(api_key=settings.groq_api_key)


def generate_text(user_prompt: str, *, system_prompt: str = SYSTEM_PROMPT, temperature: float = 0.1) -> str:
    try:
        client = _client()
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
    except GroqUnavailable:
        return _generate_text_via_rest(user_prompt, system_prompt=system_prompt, temperature=temperature)


def _generate_text_via_rest(user_prompt: str, *, system_prompt: str, temperature: float) -> str:
    if not settings.groq_api_key:
        raise GroqUnavailable("GROQ_API_KEY is not configured.")

    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }
    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise GroqUnavailable(f"Groq request failed: {exc}") from exc
    return data["choices"][0]["message"].get("content", "")


def generate_json(user_prompt: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        text = generate_text(user_prompt + "\n\nReturn JSON only. No markdown.")
        return json.loads(_strip_json(text))
    except Exception:
        if fallback is not None:
            return fallback
        raise


def _strip_json(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end >= start:
        return cleaned[start : end + 1]
    return cleaned
