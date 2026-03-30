"""
LLM Service - Integration with:
1. Groq (llama-3.3-70b-versatile) - fast free tier
2. Groq (gemma2-9b-it) - free tier
"""

import os
import httpx
import asyncio
from typing import Dict


GROQ_BASE_URL = "https://api.groq.com/openai/v1"


async def _groq_generate(prompt: str, model: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return "Error: GROQ_API_KEY not set"
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant providing information about Sunmarke School."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"


class LLMService:
    @staticmethod
    async def generate_all(prompt: str) -> Dict[str, str]:
        results = await asyncio.gather(
            _groq_generate(prompt, "llama-3.3-70b-versatile"),
            _groq_generate(prompt, "gemma2-9b-it"),
            return_exceptions=True,
        )
        return {
            "gemini": results[0] if not isinstance(results[0], Exception) else str(results[0]),
            "kimi": "",
            "deepseek": results[1] if not isinstance(results[1], Exception) else str(results[1]),
        }
