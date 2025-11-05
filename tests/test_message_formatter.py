"""Complete unit tests for MessageFormatter."""

import pytest

from promptheus.bot.message_formatter import MessageFormatter


class TestMessageFormatter:
    """Complete test suite for MessageFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create MessageFormatter instance."""
        return MessageFormatter()

    def test_format_welcome(self, formatter):
        """Test welcome message formatting."""
        message = formatter.format_welcome()

        assert "Welcome" in message
        assert "Promptheus" in message
        assert "👋" in message
        assert "*" in message  # Markdown formatting

    def test_format_assessment_intro(self, formatter):
        """Test assessment introduction formatting."""
        message = formatter.format_assessment_intro()

        assert "let's determine your level" in message.lower()
        assert "5" in message
        assert "minutes" in message.lower()
        assert "📊" in message
        assert "*" in message

    def test_format_question(self, formatter):
        """Test question formatting."""
        question_num = 2
        total = 5
        question = "What is a good prompt?"
        options = ["A) Short and vague", "B) Clear and specific", "C) Very long"]

        message = formatter.format_question(question_num, total, question, options)

        assert "Question 2/5" in message
        assert "What is a good prompt?" in message
        assert "A) Short and vague" in message
        assert "B) Clear and specific" in message
        assert "C) Very long" in message
        assert "❓" in message

    def test_format_goal_selection(self, formatter):
        """Test goal selection message formatting."""
        message = formatter.format_goal_selection()

        assert "your learning goal" in message.lower()
        assert "choose the area" in message.lower()
        assert "🎯" in message

    def test_format_personalized_path(self, formatter):
        """Test personalized learning path formatting."""
        skill_level = "intermediate"
        goal = "professional"
        lessons = [
            {"title": "Lesson 1: Basics", "id": 1},
            {"title": "Lesson 2: Advanced", "id": 2},
            {"title": "Lesson 3: Expert", "id": 3},
        ]

        message = formatter.format_personalized_path(skill_level, goal, lessons)

        assert "intermediate" in message.lower()
        assert "professional" in message.lower()
        assert "Lesson 1: Basics" in message
        assert "Lesson 2: Advanced" in message
        assert "Lesson 3: Expert" in message
        assert "✨" in message
        assert "🚀" in message

    def test_format_lesson_start(self, formatter):
        """Test lesson start message formatting."""
        title = "Introduction to Prompting"
        order = 1

        message = formatter.format_lesson_start(title, order)

        assert "Lesson 1: Introduction to Prompting" in message
        assert "Theory" in message
        assert "practice" in message.lower()
        assert "5 minutes" in message
        assert "📘" in message

    def test_format_theory(self, formatter):
        """Test theory content formatting."""
        content = "Prompt engineering is the art of crafting effective prompts for AI models."

        message = formatter.format_theory(content)

        assert "Theory" in message
        assert content in message
        assert "💡" in message

    def test_format_example_good(self, formatter):
        """Test good example formatting."""
        example_type = "good"
        content = "Write a clear, specific prompt with context."
        explanation = "This works because AI needs clear instructions."

        message = formatter.format_example(example_type, content, explanation)

        assert "✅" in message
        assert "Good Prompt" in message
        assert content in message
        assert explanation in message

    def test_format_example_bad(self, formatter):
        """Test bad example formatting."""
        example_type = "bad"
        content = "Do something."
        explanation = "This is too vague and unclear."

        message = formatter.format_example(example_type, content, explanation)

        assert "❌" in message
        assert "Bad Prompt" in message
        assert content in message
        assert explanation in message

    def test_format_exercise(self, formatter):
        """Test exercise formatting."""
        scenario = "You need to summarize a long article."
        task = "Write a prompt that asks an AI to create a concise summary."

        message = formatter.format_exercise(scenario, task)

        assert "Practice" in message
        assert "Scenario:" in message
        assert scenario in message
        assert "Task:" in message
        assert task in message
        assert "send your prompt in the next message" in message.lower()
        assert "✏️" in message

    def test_format_feedback_full(self, formatter):
        """Test full feedback formatting with all components."""
        score = 8
        missing = "Add more specific context"
        good = "Clear structure, good examples"
        improved = "Here's an improved version: [improved prompt]"

        messages = formatter.format_feedback(score, missing, good, improved)

        assert len(messages) == 3  # Score+missing, good, improved
        assert "Score: 8/10" in messages[0]
        assert "🎉" in messages[0]
        assert missing in messages[0]
        assert "What's good:" in messages[1]
        assert good in messages[1]
        assert "Improved version:" in messages[2]
        assert improved in messages[2]

    def test_format_feedback_minimal(self, formatter):
        """Test feedback formatting with minimal content."""
        score = 6
        missing = ""
        good = ""
        improved = ""

        messages = formatter.format_feedback(score, missing, good, improved)

        assert len(messages) == 1
        assert "Score: 6/10" in messages[0]
        assert "👍" in messages[0]
        assert "Good effort!" in messages[0]

    def test_format_feedback_low_score(self, formatter):
        """Test feedback formatting for low score."""
        score = 3
        missing = "Missing context and specificity"
        good = ""
        improved = ""

        messages = formatter.format_feedback(score, missing, good, improved)

        assert len(messages) == 1
        assert "Score: 3/10" in messages[0]
        assert "💪" in messages[0]
        assert missing in messages[0]

    def test_format_lesson_complete(self, formatter):
        """Test lesson completion message formatting."""
        title = "Advanced Prompting Techniques"
        score = 9
        attempts = 2

        message = formatter.format_lesson_complete(title, score, attempts)

        assert "lesson completed" in message.lower()
        assert title in message
        assert "9/10" in message
        assert "2" in message
        assert "🎉" in message

    def test_format_progress(self, formatter):
        """Test progress summary formatting."""
        skill_level = "advanced"
        completed = 8
        total = 12
        avg_score = 8.5

        message = formatter.format_progress(skill_level, completed, total, avg_score)

        assert "Your Progress" in message
        assert "advanced" in message.lower()
        assert "8/12" in message
        assert "8.5/10" in message
        assert "📊" in message

    def test_format_error_default(self, formatter):
        """Test default error message formatting."""
        message = formatter.format_error()

        assert "Error" in message
        assert "try again" in message.lower()
        assert "❌" in message

    def test_format_error_custom(self, formatter):
        """Test custom error message formatting."""
        custom_message = "Database connection failed"
        message = formatter.format_error(custom_message)

        assert "Error" in message
        assert custom_message in message
        assert "❌" in message

    def test_format_loading(self, formatter):
        """Test loading message formatting."""
        message = formatter.format_loading()

        assert "Processing" in message
        assert "⏳" in message

    def test_all_methods_are_static(self, formatter):
        """Test that all methods are static (can be called on class)."""
        # Test a few key methods on the class itself
        welcome = MessageFormatter.format_welcome()
        assert "Welcome" in welcome

        error = MessageFormatter.format_error("test")
        assert "test" in error

        loading = MessageFormatter.format_loading()
        assert "Processing" in loading
