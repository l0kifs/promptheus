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
    def format_question(question_num: int, total: int, question: str, options: list[str]) -> str:
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
    def format_personalized_path(skill_level: str, goal: str, lessons: list[dict]) -> str:
        """Format personalized learning path."""
        lesson_list = "\n".join(
            [f"{i + 1}️⃣ {lesson['title']}" for i, lesson in enumerate(lessons[:3])]
        )

        skill_emoji = {"beginner": "🌱", "intermediate": "📈", "advanced": "🚀"}

        return f"""✨ *Your path is ready!*

Level: {skill_emoji.get(skill_level, "🌱")} {skill_level.title()}
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
    def format_example(example_type: str, content: str, explanation: str) -> str:
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
    def format_feedback(score: int, missing: str, good: str, improved: str) -> list[str]:
        """Format AI feedback."""
        messages = []

        # Score message
        emoji = "🎉" if score >= 8 else "👍" if score >= 6 else "💪"
        messages.append(f"""{emoji} *Score: {score}/10*

{missing if missing else "Good effort!"}""")

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
    def format_progress(skill_level: str, completed: int, total: int, avg_score: float) -> str:
        """Format progress summary."""
        skill_emoji = {"beginner": "🌱", "intermediate": "📈", "advanced": "🚀"}

        return f"""📊 *Your Progress*

Level: {skill_emoji.get(skill_level, "🌱")} {skill_level.title()}
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

    @staticmethod
    def chunk_text_by_words(text: str, min_words: int = 50, max_words: int = 80) -> list[str]:
        """Split text into chunks of specified word count.

        Preserves sentence boundaries when possible and handles edge cases
        for very short or very long content.

        Args:
            text: The text to split into chunks
            min_words: Minimum words per chunk (except last chunk)
            max_words: Maximum words per chunk

        Returns:
            List of text chunks, each containing min_words to max_words words
        """
        if not text or not text.strip():
            return []

        words = text.split()
        if len(words) <= max_words:
            return [text.strip()]

        chunks = []
        i = 0

        while i < len(words):
            # Start with the maximum chunk size
            chunk_end = min(i + max_words, len(words))

            # If this is the last possible chunk, include all remaining words
            if chunk_end == len(words):
                chunk_words = words[i:chunk_end]
                chunk_text = " ".join(chunk_words).strip()
                if chunk_text:
                    chunks.append(chunk_text)
                break

            # Look backwards from the max chunk size to find a good sentence boundary
            chunk_text = " ".join(words[i:chunk_end])
            best_split_pos = chunk_end  # Default to word boundary

            # Look for sentence endings in the chunk
            sentence_endings = [". ", "! ", "? ", ".\n", "!\n", "?\n"]
            for j in range(
                len(chunk_text) - 1, max(0, len(chunk_text) - 100), -1
            ):  # Last 100 chars
                for ending in sentence_endings:
                    if chunk_text[j : j + len(ending)] == ending:
                        # Found a sentence ending, calculate word position
                        words_before_boundary = len(chunk_text[: j + len(ending)].split())
                        split_pos = i + words_before_boundary
                        # Only use this boundary if it gives us at least min_words
                        if split_pos - i >= min_words and split_pos < chunk_end:
                            best_split_pos = split_pos
                            break
                if best_split_pos != chunk_end:
                    break

            # Create the chunk
            chunk_words = words[i:best_split_pos]
            chunk_text = " ".join(chunk_words).strip()
            if chunk_text:
                chunks.append(chunk_text)
            i = best_split_pos

        return chunks
