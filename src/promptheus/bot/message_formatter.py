"""Message formatting for Telegram."""


class MessageFormatter:
    """Formatter for Telegram messages."""

    @staticmethod
    def format_welcome() -> str:
        """Format welcome message."""
        return """👋 *Welcome to Promptheus!*

I'll help you master the art of communicating with AI.

Ready to begin?"""

    @staticmethod
    def format_assessment_intro() -> str:
        """Format assessment introduction."""
        return """📊 *Let's determine your level*

Answer 5 short questions.
This will take 2 minutes.

🚀 *Ready to start?*"""

    @staticmethod
    def format_question(
        question_num: int, total: int, question: str, options: list[str]
    ) -> str:
        """Format assessment question."""
        options_text = "\n".join(options)
        return f"""❓ *Question {question_num}/{total}*

{question}

{options_text}"""

    @staticmethod
    def format_goal_selection() -> str:
        """Format goal selection message."""
        return """🎯 *Your learning goal?*

Choose the area where you'll use prompt engineering most:"""

    @staticmethod
    def format_personalized_path(
        skill_level: str, goal: str, lessons: list[dict]
    ) -> str:
        """Format personalized learning path."""
        lesson_list = "\n".join(
            [f"{i+1}️⃣ {lesson['title']}" for i, lesson in enumerate(lessons[:3])]
        )

        skill_emoji = {"beginner": "🌱", "intermediate": "📈", "advanced": "🚀"}

        return f"""✨ *Your path is ready!*

Level: {skill_emoji.get(skill_level, '🌱')} {skill_level.title()}
Focus: {goal.title()}

*Recommended lessons:*
{lesson_list}

🚀 *Ready to start?*"""

    @staticmethod
    def format_lesson_start(title: str, order: int) -> str:
        """Format lesson start message."""
        return f"""📘 *Lesson {order}: {title}*

In this lesson:
• Theory and key concepts
• Good vs Bad examples
• Hands-on practice

Time: ~5 minutes

*Let's begin!*"""

    @staticmethod
    def format_theory(content: str) -> str:
        """Format theory content."""
        return f"""💡 *Theory*

{content}"""

    @staticmethod
    def format_example(
        example_type: str, content: str, explanation: str
    ) -> str:
        """Format example with explanation."""
        emoji = "✅" if example_type == "good" else "❌"
        return f"""{emoji} *{example_type.title()} Prompt*

{content}

{explanation}"""

    @staticmethod
    def format_exercise(scenario: str, task: str) -> str:
        """Format practice exercise."""
        return f"""✏️ *Practice*

*Scenario:*
{scenario}

*Task:*
{task}

Send your prompt in the next message."""

    @staticmethod
    def format_feedback(
        score: int, missing: str, good: str, improved: str
    ) -> str:
        """Format AI feedback."""
        messages = []

        # Score message
        emoji = "🎉" if score >= 8 else "👍" if score >= 6 else "💪"
        messages.append(f"""{emoji} *Score: {score}/10*

{missing if missing else 'Good effort!'}""")

        # Good points if any
        if good:
            messages.append(f"""✅ *What's good:*

{good}""")

        # Improved version if available
        if improved:
            messages.append(f"""✨ *Improved version:*

{improved}""")

        return messages

    @staticmethod
    def format_lesson_complete(title: str, score: int, attempts: int) -> str:
        """Format lesson completion message."""
        return f"""🎉 *Lesson completed!*

*{title}* ✅
Attempts: {attempts}
Score: {score}/10

*Great job!*"""

    @staticmethod
    def format_progress(
        skill_level: str, completed: int, total: int, avg_score: float
    ) -> str:
        """Format progress summary."""
        skill_emoji = {"beginner": "🌱", "intermediate": "📈", "advanced": "🚀"}

        return f"""📊 *Your Progress*

Level: {skill_emoji.get(skill_level, '🌱')} {skill_level.title()}
Completed: {completed}/{total} lessons
Average score: {avg_score}/10"""

    @staticmethod
    def format_error(message: str = "Something went wrong. Please try again.") -> str:
        """Format error message."""
        return f"""❌ *Error*

{message}"""

    @staticmethod
    def format_loading() -> str:
        """Format loading message."""
        return "⏳ *Processing...*"
