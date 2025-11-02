"""Assessment engine for skill level evaluation."""

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.data.models import SkillLevel


class AssessmentEngine:
    """Engine for assessing user skill level."""

    def __init__(self, ai_client: OpenRouterClient) -> None:
        """Initialize assessment engine."""
        self.ai_client = ai_client

    def get_assessment_questions(self) -> list[dict[str, str | list[str]]]:
        """Get assessment questions."""
        return [
            {
                "question": "What is a 'role' in prompt engineering?",
                "options": [
                    "A) Task description",
                    "B) AI persona (e.g., 'expert teacher')",
                    "C) Output format",
                ],
                "correct": "B",
            },
            {
                "question": "Which prompt is better for getting detailed code?",
                "options": [
                    "A) 'Write Python code'",
                    "B) 'Write Python code with comments'",
                    "C) 'As senior dev, write Python code with detailed comments explaining logic'",
                ],
                "correct": "C",
            },
            {
                "question": "What is 'context' in a prompt?",
                "options": [
                    "A) Background information and constraints",
                    "B) The question itself",
                    "C) Expected response length",
                ],
                "correct": "A",
            },
            {
                "question": "What improves AI response quality most?",
                "options": [
                    "A) Longer prompts",
                    "B) Specific, clear instructions with examples",
                    "C) Using complex vocabulary",
                ],
                "correct": "B",
            },
            {
                "question": "What is 'few-shot' prompting?",
                "options": [
                    "A) Asking multiple questions",
                    "B) Providing examples before the main task",
                    "C) Making the prompt shorter",
                ],
                "correct": "B",
            },
        ]

    async def evaluate_answers(self, answers: list[str]) -> dict[str, int | str]:
        """Evaluate user answers and determine skill level."""
        questions = self.get_assessment_questions()
        correct_answers = [q["correct"] for q in questions]

        # Check answers
        results = [ans == correct for ans, correct in zip(answers, correct_answers, strict=True)]

        # Calculate score
        correct_count = sum(results)
        total = len(questions)
        score = int((correct_count / total) * 100) if total > 0 else 0

        # Determine skill level - MVP only has beginner lessons, so be conservative
        # 80%+ = intermediate (but will show beginner lessons)
        # 60-79% = beginner
        # <60% = beginner
        if score >= 80:
            level = SkillLevel.INTERMEDIATE
        elif score >= 60:
            level = SkillLevel.BEGINNER
        else:
            level = SkillLevel.BEGINNER

        return {
            "score": score,
            "level": level.value,
            "correct": correct_count,
            "total": total,
        }

    async def evaluate_user_prompt(
        self, user_prompt: str, lesson_id: int
    ) -> dict[str, int | list[str]]:
        """Evaluate user's prompt submission for a practice exercise.

        Args:
            user_prompt: The prompt submitted by the user
            lesson_id: The ID of the current lesson

        Returns:
            Dictionary with score (0-10), strengths, and improvements
        """
        # Create evaluation prompt
        evaluation_prompt = f"""You are an expert prompt engineering instructor. Evaluate this student's prompt.

Student's Prompt: "{user_prompt}"

Provide a structured evaluation:
1. Score (0-10): Rate the prompt quality
2. Strengths: What's good about it (2-3 points)
3. Improvements: What could be better (2-3 points)

Focus on: role definition, context clarity, specific instructions, and output format.

Respond in this exact JSON format:
{{
  "score": <number>,
  "strengths": ["strength1", "strength2"],
  "improvements": ["improvement1", "improvement2"]
}}"""

        try:
            # Call AI to evaluate using the correct method
            response = await self.ai_client.call_with_fallback(
                prompt=evaluation_prompt,
                max_tokens=512,
                temperature=0.3,
            )

            # Parse response - try to extract JSON
            import json
            import re

            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "score": int(result.get("score", 5)),
                    "strengths": result.get("strengths", []),
                    "improvements": result.get("improvements", []),
                }
            else:
                # Fallback if JSON parsing fails
                return {
                    "score": 5,
                    "strengths": ["Good attempt at creating a prompt"],
                    "improvements": [
                        "Try adding more specific context",
                        "Consider defining a clear role for the AI",
                    ],
                }

        except Exception:
            # Fallback on any error
            return {
                "score": 5,
                "strengths": ["You submitted a prompt"],
                "improvements": [
                    "Add more context and clarity",
                    "Define a specific role for the AI",
                ],
            }
