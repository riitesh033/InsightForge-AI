import asyncio
from typing import Any

from google import genai
from google.genai import types
import httpx

from app.core.config import settings


# ============================================================
# Exceptions
# ============================================================

class AIProviderError(Exception):
    """Raised when an AI provider cannot generate a response."""


# ============================================================
# Gemini
# ============================================================

async def generate_with_gemini(
    prompt: str,
) -> str:

    if not settings.GEMINI_API_KEY:
        raise AIProviderError(
            "Gemini API key is not configured."
        )

    try:
        client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        response = await asyncio.to_thread(
            client.models.generate_content,
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1200,
            ),
        )

        answer = response.text

        if not answer:
            raise AIProviderError(
                "Gemini returned an empty response."
            )

        return answer.strip()

    except Exception as error:

        raise AIProviderError(
            f"Gemini error: {error}"
        ) from error


# ============================================================
# OpenRouter
# ============================================================

async def generate_with_openrouter(
    prompt: str,
) -> str:

    if not settings.OPENROUTER_API_KEY:
        raise AIProviderError(
            "OpenRouter API key is not configured."
        )

    headers = {
        "Authorization": (
            f"Bearer {settings.OPENROUTER_API_KEY}"
        ),
        "Content-Type": "application/json",
        "HTTP-Referer": (
            settings.FRONTEND_URL
        ),
        "X-OpenRouter-Title": (
            "InsightForge AI"
        ),
    }

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
    }

    try:

        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:

            response = await client.post(
                settings.OPENROUTER_BASE_URL
                + "/chat/completions",
                headers=headers,
                json=payload,
            )

        if response.status_code >= 400:

            raise AIProviderError(
                "OpenRouter returned "
                f"{response.status_code}: "
                f"{response.text[:500]}"
            )

        data = response.json()

        choices = data.get(
            "choices",
            []
        )

        if not choices:
            raise AIProviderError(
                "OpenRouter returned no choices."
            )

        answer = (
            choices[0]
            .get("message", {})
            .get("content")
        )

        if not answer:
            raise AIProviderError(
                "OpenRouter returned an empty response."
            )

        return answer.strip()

    except httpx.HTTPError as error:

        raise AIProviderError(
            f"OpenRouter HTTP error: {error}"
        ) from error


# ============================================================
# Ollama
# ============================================================

async def generate_with_ollama(
    prompt: str,
) -> str:

    try:

        import ollama

        client = ollama.Client(
            host=settings.OLLAMA_BASE_URL
        )

        response = await asyncio.to_thread(
            client.chat,
            model=settings.OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        answer = (
            response
            .get("message", {})
            .get("content")
        )

        if not answer:
            raise AIProviderError(
                "Ollama returned an empty response."
            )

        return answer.strip()

    except Exception as error:

        raise AIProviderError(
            f"Ollama error: {error}"
        ) from error


# ============================================================
# Main AI Router
# ============================================================

async def generate_ai_response(
    prompt: str,
) -> str:

    provider = (
        settings.AI_PROVIDER
        .strip()
        .lower()
    )

    providers = []

    if provider == "gemini":

        providers = [
            ("Gemini", generate_with_gemini),
            ("OpenRouter", generate_with_openrouter),
            ("Ollama", generate_with_ollama),
        ]

    elif provider == "openrouter":

        providers = [
            ("OpenRouter", generate_with_openrouter),
            ("Gemini", generate_with_gemini),
            ("Ollama", generate_with_ollama),
        ]

    elif provider == "ollama":

        providers = [
            ("Ollama", generate_with_ollama),
            ("Gemini", generate_with_gemini),
            ("OpenRouter", generate_with_openrouter),
        ]

    else:

        providers = [
            ("Gemini", generate_with_gemini),
            ("OpenRouter", generate_with_openrouter),
            ("Ollama", generate_with_ollama),
        ]

    errors: list[str] = []

    for name, provider_function in providers:

        try:

            print(
                f"CHAT: Trying {name}..."
            )

            answer = await provider_function(
                prompt
            )

            print(
                f"CHAT: {name} response received."
            )

            return answer

        except AIProviderError as error:

            print(
                f"CHAT: {name} failed: {error}"
            )

            errors.append(
                f"{name}: {error}"
            )

        except Exception as error:

            print(
                f"CHAT: Unexpected {name} error: "
                f"{error}"
            )

            errors.append(
                f"{name}: {error}"
            )

    raise AIProviderError(
        "All AI providers failed. "
        + " | ".join(errors)
    )