"""Prompt template manager for centralized AI prompt management."""

from typing import Any


class PromptTemplateManager:
    """Centralized management of AI prompt templates."""

    def __init__(self) -> None:
        """Initialize template manager."""
        self.templates: dict[str, str] = {}
        self._register_default_templates()

    def register_template(self, name: str, template: str) -> None:
        """Register a prompt template.

        Args:
            name: Template name identifier
            template: Template string with {placeholders}
        """
        self.templates[name] = template

    def render(self, name: str, **variables: Any) -> str:
        """Render template with variables.

        Args:
            name: Template name
            **variables: Variables to substitute in template

        Returns:
            Rendered prompt string

        Raises:
            ValueError: If template not found
            KeyError: If required variable missing
        """
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        return self.templates[name].format(**variables)

    def get_template(self, name: str) -> str:
        """Get raw template string.

        Args:
            name: Template name

        Returns:
            Raw template string

        Raises:
            ValueError: If template not found
        """
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        return self.templates[name]

    def _register_default_templates(self) -> None:
        """Register default prompt templates."""
        # Assessment evaluation template
        self.register_template(
            "assessment_evaluation",
            """You are an expert in prompt engineering for {skill_level} level users.
User's learning goal: {learning_goal}

User's prompt:
{user_prompt}

Evaluate the prompt based on:
{criteria}

Provide structured feedback in JSON format:
{{
  "score": <0-10>,
  "strengths": ["strength1", "strength2"],
  "improvements": ["improvement1", "improvement2"]
}}""",
        )

        # Exercise feedback template
        self.register_template(
            "exercise_feedback",
            """You are an expert prompt engineering instructor evaluating a student's exercise submission.

Student's Prompt: "{user_prompt}"

Skill Level: {skill_level}
Learning Goal: {learning_goal}

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
}}""",
        )

        # Improved prompt generation template
        self.register_template(
            "improved_prompt_generation",
            """You are an expert prompt engineer. A user submitted this prompt:

"{user_prompt}"

Skill Level: {skill_level}
Learning Goal: {learning_goal}

Create an improved version of this prompt that follows best practices:
- Clear role definition
- Specific context and constraints
- Detailed instructions
- Expected output format

Provide only the improved prompt text, nothing else.""",
        )

        # Assessment analysis template
        self.register_template(
            "assessment_analysis",
            """You are an expert prompt engineering instructor evaluating a student's knowledge assessment.

Assessment Questions and Student Answers:
{questions_and_answers}

Analyze the student's understanding of prompt engineering concepts:
1. Correctness of answers
2. Depth of understanding shown in responses
3. Pattern recognition in prompt engineering principles
4. Practical application knowledge

Provide assessment in JSON format:
{{
  "score": <0-100, nuanced evaluation>,
  "skill_level": "beginner|intermediate|advanced",
  "analysis": "Brief explanation of assessment",
  "strengths": ["key strengths observed"],
  "areas_for_improvement": ["areas needing work"]
}}""",
        )
