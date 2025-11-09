"""OpenRouter API client with fallback chain."""

import asyncio
from typing import Any

import httpx
from loguru import logger

from promptheus.config import get_settings


class OpenRouterClient:
    """Client for OpenRouter API."""

    def __init__(self) -> None:
        """Initialize client."""
        self.settings = get_settings()
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "HTTP-Referer": "https://github.com/l0kifs/promptheus",
            "X-Title": "Promptheus Bot",
        }
        self.timeout = 10.0

    async def call_model(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Call AI model with prompt."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError) as e:
            logger.error(f"Error calling model {model}: {e}")
            raise

    async def call_with_fallback(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Call AI with fallback chain."""
        models = [
            self.settings.ai_model_primary,
            self.settings.ai_model_fallback,
            self.settings.ai_model_alternative,
        ]

        for attempt, model in enumerate(models):
            try:
                logger.info(f"Trying model: {model}")
                result = await self.call_model(prompt, model, max_tokens, temperature)
                logger.info(f"Success with model: {model}")
                return result
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                if attempt < len(models) - 1:  # Not the last model
                    delay = 2**attempt  # 1s, 2s, 4s
                    logger.info(f"Waiting {delay}s before trying next model")
                    await asyncio.sleep(delay)
                continue

        raise RuntimeError("All AI models failed")

    async def test_connection(self) -> bool:
        """Test connection to OpenRouter API without consuming credits."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Use models endpoint which is free and doesn't require credits
                response = await client.get(
                    f"{self.base_url}/models", headers=self.headers, timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenRouter connection test failed: {e}")
            return False

    async def evaluate_prompt(self, user_prompt: str, scenario: str) -> dict[str, Any]:
        """Evaluate user's prompt."""
        evaluation_prompt = f"""You are an expert in prompt engineering. Evaluate this user's prompt.

Scenario: {scenario}

User's prompt: {user_prompt}

Provide evaluation in this format:
Score: [0-10]
Missing: [what's missing, max 2-3 points]
Good: [what's good, max 2-3 points]
Improved: [improved version of the prompt]"""

        try:
            response = await self.call_with_fallback(
                evaluation_prompt,
                max_tokens=self.settings.max_tokens_feedback,
                temperature=self.settings.temperature_feedback,
            )

            # Parse response
            lines = response.strip().split("\n")
            result: dict[str, Any] = {
                "score": 5,
                "missing": "Unable to parse feedback",
                "good": "",
                "improved": "",
            }

            for line in lines:
                if line.startswith("Score:"):
                    try:
                        score_text = line.replace("Score:", "").strip()
                        # Extract number from text like "7/10" or "7"
                        score_num = int(score_text.split("/")[0].strip())
                        result["score"] = min(max(score_num, 0), 10)
                    except (ValueError, IndexError):
                        pass
                elif line.startswith("Missing:"):
                    result["missing"] = line.replace("Missing:", "").strip()
                elif line.startswith("Good:"):
                    result["good"] = line.replace("Good:", "").strip()
                elif line.startswith("Improved:"):
                    result["improved"] = line.replace("Improved:", "").strip()

            return result

        except Exception as e:
            logger.error(f"Error evaluating prompt: {e}")
            return {
                "score": 0,
                "missing": "Error evaluating prompt. Please try again.",
                "good": "",
                "improved": "",
            }

    async def assess_skill_level(self, answers: list[bool]) -> dict[str, Any]:
        """Assess user skill level based on answers."""
        correct_count = sum(answers)
        total = len(answers)
        score = int((correct_count / total) * 100) if total > 0 else 0

        if score < 40:
            level = "beginner"
        elif score < 70:
            level = "intermediate"
        else:
            level = "advanced"

        return {"score": score, "level": level, "correct": correct_count, "total": total}
