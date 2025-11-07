"""Assessment engine for skill level evaluation."""

from typing import Any

from loguru import logger

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.ai.prompt_template_manager import PromptTemplateManager
from promptheus.config import get_settings
from promptheus.data.models import SkillLevel


class AssessmentEngine:
    """Engine for assessing user skill level."""

    def __init__(
        self, ai_client: OpenRouterClient, template_manager: PromptTemplateManager
    ) -> None:
        """Initialize assessment engine."""
        self.ai_client = ai_client
        self.template_manager = template_manager
        self.settings = get_settings()

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

    async def evaluate_answers(self, answers: list[str]) -> dict[str, Any]:
        """Evaluate user answers and determine skill level using AI analysis.

        Uses OpenRouter AI to analyze user responses to assessment questions,
        providing nuanced evaluation based on understanding depth rather than
        simple correct/incorrect counting.

        Args:
            answers: List of user answers (should be exactly 5 answers)

        Returns:
            Dictionary containing:
            - score: AI-determined score (0-100)
            - level: Skill level ("beginner", "intermediate", "advanced")
            - analysis: AI-generated analysis text
            - strengths: List of identified strengths
            - areas_for_improvement: List of improvement suggestions

        Raises:
            ValueError: If assessment questions count is not exactly 5

        Note:
            Falls back to basic answer counting if AI evaluation fails.
            Fallback results include a "fallback" key to indicate limited analysis.
        """
        logger.info("Evaluating assessment answers with AI", answer_count=len(answers))
        questions = self.get_assessment_questions()

        # Validate question count (must be exactly 5 as per US §1.2)
        if len(questions) != 5:
            logger.error("Assessment questions count mismatch", expected=5, actual=len(questions))
            raise ValueError(f"Assessment must have exactly 5 questions, found {len(questions)}")

        # Prepare questions and answers for AI analysis
        questions_and_answers = self._format_questions_and_answers(questions, answers)

        try:
            # Use AI to analyze assessment responses
            analysis_prompt = self.template_manager.render(
                "assessment_analysis",
                questions_and_answers=questions_and_answers,
            )

            response = await self.ai_client.call_with_fallback(
                prompt=analysis_prompt,
                max_tokens=self.settings.max_tokens_assessment,
                temperature=self.settings.temperature_assessment,
            )

            # Parse AI analysis
            analysis = self._parse_assessment_response(response)

            logger.info(
                "AI assessment evaluation successful",
                score=analysis["score"],
                level=analysis["level"],
            )

            return analysis

        except Exception as e:
            logger.error("AI assessment evaluation failed, using fallback", error=str(e))
            # Fallback to basic counting
            return await self._evaluate_answers_fallback(answers)

    def _format_questions_and_answers(
        self, questions: list[dict[str, str | list[str]]], answers: list[str]
    ) -> str:
        """Format questions and answers for AI analysis.

        Creates a structured text representation of the assessment questions
        and user's answers for the AI to analyze patterns and understanding depth.
        """
        formatted = []
        for i, (question, answer) in enumerate(zip(questions, answers, strict=False)):
            q_text = question["question"]
            options = question["options"]
            formatted.append(f"Q{i + 1}: {q_text}")
            formatted.append(f"Options: {', '.join(options)}")
            formatted.append(f"Student's Answer: {answer}")
            formatted.append("")
        return "\n".join(formatted)

    def _parse_assessment_response(self, response: str) -> dict[str, Any]:
        """Parse AI assessment response into structured format.

        Extracts JSON from AI response and validates the assessment data.
        Falls back to heuristic parsing if JSON extraction fails.
        """
        import json
        import re

        # Try to find JSON in response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                score = int(result.get("score", 50))
                skill_level = result.get("skill_level", "beginner")
                analysis = result.get("analysis", "Assessment completed")
                strengths = result.get("strengths", [])
                areas_for_improvement = result.get("areas_for_improvement", [])

                # Validate skill level
                if skill_level not in ["beginner", "intermediate", "advanced"]:
                    skill_level = "beginner"

                return {
                    "score": score,
                    "level": skill_level,
                    "analysis": analysis,
                    "strengths": strengths,
                    "areas_for_improvement": areas_for_improvement,
                }
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("Failed to parse AI assessment response", error=str(e))

        # Fallback parsing if JSON fails
        return self._parse_assessment_fallback(response)

    def _parse_assessment_fallback(self, response: str) -> dict[str, Any]:
        """Fallback parsing for AI assessment response.

        Uses simple keyword-based heuristics to estimate skill level
        when AI response cannot be properly parsed.
        """
        # Simple heuristic parsing
        response_lower = response.lower()

        # Estimate score based on keywords
        score = 50  # Default
        if "excellent" in response_lower or "advanced" in response_lower:
            score = 85
        elif "good" in response_lower or "intermediate" in response_lower:
            score = 70
        elif "basic" in response_lower or "beginner" in response_lower:
            score = 40

        # Determine level
        if score >= 80:
            level = "advanced"
        elif score >= 60:
            level = "intermediate"
        else:
            level = "beginner"

        return {
            "score": score,
            "level": level,
            "analysis": "Assessment completed with limited analysis",
            "strengths": ["Completed the assessment"],
            "areas_for_improvement": ["Further practice recommended"],
        }

    async def _evaluate_answers_fallback(self, answers: list[str]) -> dict[str, Any]:
        """Fallback evaluation using basic answer counting.

        Used when AI evaluation is unavailable. Provides basic assessment
        based on correct/incorrect answer counting with clear indication
        that this is fallback analysis.
        """
        logger.info("Using fallback assessment evaluation")
        questions = self.get_assessment_questions()
        correct_answers = [q["correct"] for q in questions]

        # Handle case where user didn't answer all questions
        min_length = min(len(answers), len(correct_answers))
        answers = answers[:min_length]
        correct_answers = correct_answers[:min_length]

        # Check answers
        results = [ans == correct for ans, correct in zip(answers, correct_answers, strict=True)]

        # Calculate score
        correct_count = sum(results)
        total = len(questions)
        answered = len(answers)
        score = int((correct_count / total) * 100) if total > 0 else 0

        # Determine skill level - conservative approach
        if score >= 80:
            level = SkillLevel.ADVANCED
        elif score >= 60:
            level = SkillLevel.INTERMEDIATE
        else:
            level = SkillLevel.BEGINNER

        logger.info(
            "Fallback assessment evaluated",
            score=score,
            correct=correct_count,
            answered=answered,
            total=total,
            level=level.value,
        )

        return {
            "score": score,
            "level": level.value,
            "correct": correct_count,
            "total": total,
            "answered": answered,
            "fallback": True,  # Indicate fallback was used
        }

    async def evaluate_user_prompt(
        self,
        user_prompt: str,
        lesson_id: int,
        skill_level: str = "beginner",
        learning_goal: str = "general",
    ) -> dict[str, int | list[str]]:
        """Evaluate user's prompt submission for a practice exercise.

        Args:
            user_prompt: The prompt submitted by the user
            lesson_id: The ID of the current lesson

        Returns:
            Dictionary with score (0-10), strengths, and improvements
        """
        logger.info("Evaluating user prompt", lesson_id=lesson_id, prompt_length=len(user_prompt))

        # Create evaluation prompt using template manager
        evaluation_prompt = self.template_manager.render(
            "exercise_feedback",
            user_prompt=user_prompt,
            skill_level=skill_level,
            learning_goal=learning_goal,
        )

        try:
            # Call AI to evaluate using the correct method
            logger.debug("Calling AI for prompt evaluation", lesson_id=lesson_id)
            response = await self.ai_client.call_with_fallback(
                prompt=evaluation_prompt,
                max_tokens=self.settings.max_tokens_feedback,
                temperature=self.settings.temperature_feedback,
            )

            logger.debug("AI evaluation received", lesson_id=lesson_id)

            # Parse response - try to extract JSON
            import json
            import re

            # Try to find JSON in response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                score = int(result.get("score", 5))
                strengths = result.get("strengths", [])
                improvements = result.get("improvements", [])

                logger.info(
                    "Prompt evaluation successful",
                    lesson_id=lesson_id,
                    score=score,
                )

                return {
                    "score": score,
                    "strengths": strengths,
                    "improvements": improvements,
                }
            else:
                # Fallback if JSON parsing fails
                logger.warning(
                    "Failed to parse AI response as JSON, using fallback", lesson_id=lesson_id
                )
                return {
                    "score": 5,
                    "strengths": ["Good attempt at creating a prompt"],
                    "improvements": [
                        "Try adding more specific context",
                        "Consider defining a clear role for the AI",
                    ],
                }

        except Exception as e:
            # Fallback on any error
            logger.error(
                "Error evaluating prompt, using fallback", lesson_id=lesson_id, error=str(e)
            )
            return {
                "score": 5,
                "strengths": ["You submitted a prompt"],
                "improvements": [
                    "Add more context and clarity",
                    "Define a specific role for the AI",
                ],
            }
