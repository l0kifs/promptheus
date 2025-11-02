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
