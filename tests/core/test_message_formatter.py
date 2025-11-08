"""Complete unit tests for MessageFormatter."""

import pytest

from promptheus.bot.message_formatter import MessageFormatter


class TestMessageFormatter:
    """Complete test suite for MessageFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create MessageFormatter instance."""
        return MessageFormatter()

    def test_format_welcome_returns_welcome_message_with_emoji_and_formatting(self, formatter):
        """Test welcome message formatting."""
        message = formatter.format_welcome()

        assert "Welcome" in message
        assert "Promptheus" in message
        assert "👋" in message
        assert "*" in message  # Markdown formatting

    def test_format_assessment_intro_returns_intro_message_with_duration_and_emoji(self, formatter):
        """Test assessment introduction formatting."""
        message = formatter.format_assessment_intro()

        assert "let's determine your level" in message.lower()
        assert "5" in message
        assert "minutes" in message.lower()
        assert "📊" in message
        assert "*" in message

    def test_format_question_returns_formatted_question_with_options_and_progress(self, formatter):
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

    def test_format_goal_selection_returns_goal_selection_message_with_emoji(self, formatter):
        """Test goal selection message formatting."""
        message = formatter.format_goal_selection()

        assert "your learning goal" in message.lower()
        assert "choose the area" in message.lower()
        assert "🎯" in message

    def test_format_personalized_path_returns_path_message_with_skill_level_and_lessons(
        self, formatter
    ):
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

    def test_format_lesson_start_returns_lesson_start_message_with_title_and_duration(
        self, formatter
    ):
        """Test lesson start message formatting."""
        title = "Introduction to Prompting"
        order = 1

        message = formatter.format_lesson_start(title, order)

        assert "Lesson 1: Introduction to Prompting" in message
        assert "Theory" in message
        assert "practice" in message.lower()
        assert "5 minutes" in message
        assert "📘" in message

    def test_format_theory_returns_theory_message_with_content_and_emoji(self, formatter):
        """Test theory content formatting."""
        content = "Prompt engineering is the art of crafting effective prompts for AI models."

        message = formatter.format_theory(content)

        assert "Theory" in message
        assert content in message
        assert "💡" in message

    def test_format_example_good_returns_good_example_message_with_explanation(self, formatter):
        """Test good example formatting."""
        example_type = "good"
        content = "Write a clear, specific prompt with context."
        explanation = "This works because AI needs clear instructions."

        message = formatter.format_example(example_type, content, explanation)

        assert "✅" in message
        assert "Good Prompt" in message
        assert content in message
        assert explanation in message

    def test_format_example_bad_returns_bad_example_message_with_explanation(self, formatter):
        """Test bad example formatting."""
        example_type = "bad"
        content = "Do something."
        explanation = "This is too vague and unclear."

        message = formatter.format_example(example_type, content, explanation)

        assert "❌" in message
        assert "Bad Prompt" in message
        assert content in message
        assert explanation in message

    def test_format_exercise_returns_exercise_message_with_scenario_and_task(self, formatter):
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

    def test_format_feedback_full_returns_multiple_messages_with_score_feedback_and_improvement(
        self, formatter
    ):
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

    def test_format_feedback_minimal_returns_single_message_with_score_and_encouragement(
        self, formatter
    ):
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

    def test_format_feedback_low_score_returns_message_with_score_and_missing_elements(
        self, formatter
    ):
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

    def test_format_lesson_complete_returns_completion_message_with_score_and_attempts(
        self, formatter
    ):
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

    def test_format_progress_returns_progress_summary_with_completion_and_average(self, formatter):
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

    def test_format_error_default_returns_default_error_message_with_emoji(self, formatter):
        """Test default error message formatting."""
        message = formatter.format_error()

        assert "Error" in message
        assert "try again" in message.lower()
        assert "❌" in message

    def test_format_error_custom_returns_custom_error_message_with_emoji(self, formatter):
        """Test custom error message formatting."""
        custom_message = "Database connection failed"
        message = formatter.format_error(custom_message)

        assert "Error" in message
        assert custom_message in message
        assert "❌" in message

    def test_format_loading_returns_loading_message_with_emoji(self, formatter):
        """Test loading message formatting."""
        message = formatter.format_loading()

        assert "Processing" in message
        assert "⏳" in message

    def test_all_methods_are_static_can_be_called_on_class_without_instance(self, formatter):
        """Test that all methods are static (can be called on class)."""
        # Test a few key methods on the class itself
        welcome = MessageFormatter.format_welcome()
        assert "Welcome" in welcome

        error = MessageFormatter.format_error("test")
        assert "test" in error

        loading = MessageFormatter.format_loading()
        assert "Processing" in loading

    def test_chunk_text_by_words_with_typical_content_splits_into_chunks_of_50_to_80_words(self):
        """Test chunking of normal-length content."""
        text = " ".join([f"word{i}" for i in range(150)])  # 150 words
        chunks = MessageFormatter.chunk_text_by_words(text)

        assert len(chunks) >= 2  # Should split into multiple chunks
        for chunk in chunks:
            words_in_chunk = len(chunk.split())
            assert 50 <= words_in_chunk <= 80

    def test_chunk_text_by_words_with_short_content_returns_single_chunk(self):
        """Test chunking of short content."""
        text = "This is a short piece of content with only thirty words that should not be split."
        chunks = MessageFormatter.chunk_text_by_words(text)

        assert len(chunks) == 1  # Should not split short content
        assert len(chunks[0].split()) <= 80

    def test_chunk_text_by_words_with_empty_content_returns_empty_list(self):
        """Test chunking of empty content."""
        chunks = MessageFormatter.chunk_text_by_words("")
        assert chunks == []

        chunks = MessageFormatter.chunk_text_by_words("   ")
        assert chunks == []

    def test_chunk_text_by_words_preserves_sentence_boundaries_when_possible(self):
        """Test that chunking tries to preserve sentence boundaries when possible."""
        text = "This is the first sentence. This is the second sentence with more words to make it longer. This is the third sentence."
        chunks = MessageFormatter.chunk_text_by_words(text, max_words=12)

        # Should create multiple chunks
        assert len(chunks) >= 2
        # At least one chunk should end with sentence punctuation (if sentences are long enough)
        has_sentence_end = any(
            chunk.strip().endswith(".")
            or chunk.strip().endswith("!")
            or chunk.strip().endswith("?")
            for chunk in chunks
        )
        # Either we have sentence endings or the text is short enough to not split
        assert has_sentence_end or len(chunks) == 1

    def test_chunk_text_by_words_with_long_content_splits_and_preserves_all_words(self):
        """Test chunking of very long content."""
        # Create content longer than several chunks
        text = " ".join([f"This is sentence number {i} in a long text." for i in range(50)])
        chunks = MessageFormatter.chunk_text_by_words(text, max_words=60)

        assert len(chunks) >= 3  # Should split into multiple chunks
        total_words = sum(len(chunk.split()) for chunk in chunks)
        assert total_words == len(text.split())  # All words preserved

    def test_chunk_text_by_words_with_custom_limits_respects_min_and_max_word_counts(self):
        """Test chunking with custom word limits."""
        text = " ".join([f"word{i}" for i in range(100)])
        chunks = MessageFormatter.chunk_text_by_words(text, min_words=20, max_words=40)

        assert len(chunks) >= 3  # Should split into more chunks with smaller max
        for chunk in chunks[:-1]:  # All chunks except last should meet min_words
            assert len(chunk.split()) >= 20
        for chunk in chunks:
            assert len(chunk.split()) <= 40

    def test_get_typing_indicator_message_for_analyzing_returns_analyzing_message(self, formatter):
        """Test typing indicator message for analyzing operation."""
        message = formatter.get_typing_indicator_message("analyzing")
        assert "Analyzing your prompt..." in message
        assert "⏳" in message

    def test_get_typing_indicator_message_for_evaluating_returns_evaluating_message(
        self, formatter
    ):
        """Test typing indicator message for evaluating operation."""
        message = formatter.get_typing_indicator_message("evaluating")
        assert "Evaluating your response..." in message
        assert "⏳" in message

    def test_get_typing_indicator_message_for_processing_returns_processing_message(
        self, formatter
    ):
        """Test typing indicator message for processing operation (default)."""
        message = formatter.get_typing_indicator_message("processing")
        assert "⏳ Processing..." in message

    def test_get_typing_indicator_message_for_generating_returns_generating_message(
        self, formatter
    ):
        """Test typing indicator message for generating operation."""
        message = formatter.get_typing_indicator_message("generating")
        assert "⏳ Generating feedback..." in message

    def test_get_typing_indicator_message_for_unknown_operation_returns_default_processing_message(
        self, formatter
    ):
        """Test typing indicator message for unknown operation."""
        message = formatter.get_typing_indicator_message("unknown")
        assert "⏳ Processing..." in message  # Should return default

    def test_get_typing_indicator_message_with_no_operation_returns_default_processing_message(
        self, formatter
    ):
        """Test typing indicator message with no operation specified."""
        message = formatter.get_typing_indicator_message()
        assert "⏳ Processing..." in message
