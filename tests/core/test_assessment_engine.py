"""Tests for core business logic."""

import pytest

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.ai.prompt_template_manager import PromptTemplateManager
from promptheus.core.assessment_engine import AssessmentEngine
from promptheus.core.learning_flow_orchestrator import LearningFlowOrchestrator
from promptheus.core.progress_tracker import ProgressTracker
from promptheus.data.models import (
    LessonStatus,
    SessionState,
    SkillLevel,
)


class TestAssessmentEngine:
    """Tests for AssessmentEngine."""

    @pytest.fixture
    def ai_client(self, mocker):
        """Mock AI client."""
        return mocker.Mock(spec=OpenRouterClient)

    @pytest.fixture
    def template_manager(self, mocker):
        """Mock template manager."""
        return mocker.Mock(spec=PromptTemplateManager)

    @pytest.fixture
    def engine(self, ai_client, template_manager):
        """Create assessment engine."""
        return AssessmentEngine(ai_client, template_manager)

    def test_get_assessment_questions(self, engine):
        """Test getting assessment questions."""
        questions = engine.get_assessment_questions()

        assert len(questions) == 5
        assert all("question" in q for q in questions)
        assert all("options" in q for q in questions)
        assert all("correct" in q for q in questions)

    @pytest.mark.asyncio
    async def test_evaluate_answers_all_correct(self, engine):
        """Test evaluation with all correct answers using AI analysis."""
        answers = ["B", "C", "A", "B", "B"]  # All correct based on questions

        # Mock AI response for perfect assessment
        engine.ai_client.call_with_fallback.return_value = """{
            "score": 95,
            "skill_level": "advanced",
            "analysis": "Excellent understanding of prompt engineering concepts",
            "strengths": ["Perfect answers", "Strong grasp of principles"],
            "areas_for_improvement": []
        }"""
        engine.template_manager.render.return_value = "Mocked prompt"

        result = await engine.evaluate_answers(answers)

        assert result["score"] == 95
        assert result["level"] == "advanced"
        assert "strengths" in result
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_evaluate_answers_beginner(self, engine):
        """Test evaluation for beginner level using AI analysis."""
        answers = ["A", "A", "B", "A", "A"]  # Incorrect answers

        # Mock AI response for beginner assessment
        engine.ai_client.call_with_fallback.return_value = """{
            "score": 25,
            "skill_level": "beginner",
            "analysis": "Basic understanding, needs improvement",
            "strengths": ["Completed assessment"],
            "areas_for_improvement": ["Study fundamental concepts", "Practice more"]
        }"""
        engine.template_manager.render.return_value = "Mocked prompt"

        result = await engine.evaluate_answers(answers)

        assert result["score"] == 25
        assert result["level"] == "beginner"
        assert "strengths" in result
        assert "areas_for_improvement" in result

    @pytest.mark.asyncio
    async def test_evaluate_answers_intermediate(self, engine):
        """Test evaluation for intermediate level using AI analysis."""
        answers = ["B", "C", "A", "A", "A"]  # Mixed answers

        # Mock AI response for intermediate assessment
        engine.ai_client.call_with_fallback.return_value = """{
            "score": 65,
            "skill_level": "intermediate",
            "analysis": "Good progress, some concepts understood",
            "strengths": ["Understands some key principles"],
            "areas_for_improvement": ["Review advanced techniques"]
        }"""
        engine.template_manager.render.return_value = "Mocked prompt"

        result = await engine.evaluate_answers(answers)

        assert result["score"] == 65
        assert result["level"] == "intermediate"
        assert "strengths" in result
        assert "areas_for_improvement" in result

    @pytest.mark.asyncio
    async def test_evaluate_answers_ai_success(self, engine):
        """Test successful AI-powered assessment evaluation."""
        answers = ["B", "C", "A", "B", "B"]

        # Mock AI response
        engine.ai_client.call_with_fallback.return_value = """{
            "score": 85,
            "skill_level": "advanced",
            "analysis": "Strong understanding demonstrated",
            "strengths": ["Excellent role definition knowledge", "Good context understanding"],
            "areas_for_improvement": ["Could explore few-shot prompting more"]
        }"""
        engine.template_manager.render.return_value = "Mocked assessment prompt"

        result = await engine.evaluate_answers(answers)

        # Verify template was rendered with correct data
        engine.template_manager.render.assert_called_once_with(
            "assessment_analysis",
            questions_and_answers=engine._format_questions_and_answers(
                engine.get_assessment_questions(), answers
            ),
        )

        # Verify AI client was called with assessment settings
        engine.ai_client.call_with_fallback.assert_called_once()
        call_args = engine.ai_client.call_with_fallback.call_args
        assert call_args[1]["max_tokens"] == engine.settings.max_tokens_assessment
        assert call_args[1]["temperature"] == engine.settings.temperature_assessment

        assert result["score"] == 85
        assert result["level"] == "advanced"
        assert result["analysis"] == "Strong understanding demonstrated"
        assert len(result["strengths"]) == 2
        assert len(result["areas_for_improvement"]) == 1

    @pytest.mark.asyncio
    async def test_evaluate_answers_ai_failure_fallback(self, engine):
        """Test fallback when AI evaluation fails."""
        answers = ["B", "C", "A", "B", "B"]

        # Mock AI failure
        engine.ai_client.call_with_fallback.side_effect = Exception("AI timeout")

        result = await engine.evaluate_answers(answers)

        # Should use fallback logic
        assert "fallback" in result
        assert isinstance(result["score"], int)
        assert result["level"] in ["beginner", "intermediate", "advanced"]
        assert result["correct"] == 5  # All correct answers
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_evaluate_answers_invalid_question_count(self, engine):
        """Test that evaluation fails if question count is not 5."""
        from promptheus.core.exceptions import AssessmentError

        # Temporarily modify questions to have wrong count
        original_questions = engine.get_assessment_questions
        engine.get_assessment_questions = lambda: []  # Empty list

        with pytest.raises(
            AssessmentError, match="Invalid assessment configuration: expected 5 questions"
        ):
            await engine.evaluate_answers(["A", "B", "C", "A", "B"])

        # Restore original method
        engine.get_assessment_questions = original_questions

    @pytest.mark.asyncio
    async def test_parse_assessment_response_valid_json(self, engine):
        """Test parsing valid AI assessment response."""
        response = """{
            "score": 75,
            "skill_level": "intermediate",
            "analysis": "Good understanding",
            "strengths": ["Strength 1", "Strength 2"],
            "areas_for_improvement": ["Area 1"]
        }"""

        result = engine._parse_assessment_response(response)

        assert result["score"] == 75
        assert result["level"] == "intermediate"
        assert result["analysis"] == "Good understanding"
        assert result["strengths"] == ["Strength 1", "Strength 2"]
        assert result["areas_for_improvement"] == ["Area 1"]

    @pytest.mark.asyncio
    async def test_parse_assessment_response_invalid_json_fallback(self, engine):
        """Test fallback parsing when AI returns invalid JSON."""
        response = "This is not JSON, just some text about good performance."

        result = engine._parse_assessment_fallback(response)

        # Should use heuristic parsing
        assert isinstance(result["score"], int)
        assert result["level"] in ["beginner", "intermediate", "advanced"]
        assert "analysis" in result
        assert "strengths" in result
        assert "areas_for_improvement" in result

    @pytest.mark.asyncio
    async def test_evaluate_user_prompt_uses_template_and_settings(self, engine, mocker):
        """Test that evaluate_user_prompt uses template manager and settings."""
        # Mock settings on the engine instance
        mock_settings = mocker.Mock()
        mock_settings.max_tokens_feedback = 512
        mock_settings.temperature_feedback = 0.3
        engine.settings = mock_settings

        # Mock AI client response
        engine.ai_client.call_with_fallback.return_value = """{
            "score": 8,
            "strengths": ["Good structure", "Clear objective"],
            "improvements": ["Add more context"]
        }"""

        # Mock template manager
        engine.template_manager.render.return_value = "Rendered prompt"

        result = await engine.evaluate_user_prompt(
            user_prompt="Test prompt",
            lesson_id=1,
            exercise_scenario="Test scenario",
            exercise_task="Test task",
            skill_level="beginner",
            learning_goal="academic",
        )

        # Verify template manager was called correctly
        engine.template_manager.render.assert_called_once_with(
            "exercise_feedback",
            user_prompt="Test prompt",
            exercise_scenario="Test scenario",
            exercise_task="Test task",
            skill_level="beginner",
            learning_goal="academic",
        )

        # Verify AI client was called with settings values
        engine.ai_client.call_with_fallback.assert_called_once_with(
            prompt="Rendered prompt", max_tokens=512, temperature=0.3
        )

        assert result["score"] == 8
        assert result["strengths"] == ["Good structure", "Clear objective"]
        assert result["improvements"] == ["Add more context"]

    @pytest.mark.asyncio
    async def test_evaluate_prompt_with_task_mismatch(self, engine, mocker):
        """Test that misaligned prompts receive low scores."""
        # Mock settings
        mock_settings = mocker.Mock()
        mock_settings.max_tokens_feedback = 512
        mock_settings.temperature_feedback = 0.3
        engine.settings = mock_settings

        # Mock AI response for misaligned prompt
        engine.ai_client.call_with_fallback.return_value = """{
            "score": 2,
            "strengths": ["Well-written prompt for a different task"],
            "improvements": [
                "Your prompt addresses business decision analysis, but the task requires a 4-prompt workflow chain for content marketing",
                "Create 4 connected prompts with clear handoffs between them"
            ]
        }"""

        # Mock template manager
        engine.template_manager.render.return_value = "Rendered prompt with task context"

        result = await engine.evaluate_user_prompt(
            user_prompt="Analyze my business decision to expand to new market...",
            lesson_id=12,
            exercise_scenario="You want to create a content marketing workflow",
            exercise_task="Design a 4-prompt chain: topic research → headline generation → outline creation → first draft",
            skill_level="advanced",
            learning_goal="professional",
        )

        assert result["score"] <= 3  # Low score for mismatch
        assert any("task requires" in imp.lower() for imp in result["improvements"])

        # Verify template was called with exercise context
        engine.template_manager.render.assert_called_once()
        call_args = engine.template_manager.render.call_args[1]
        assert "exercise_scenario" in call_args
        assert "exercise_task" in call_args
        assert call_args["exercise_scenario"] == "You want to create a content marketing workflow"
        assert "4-prompt chain" in call_args["exercise_task"]

    @pytest.mark.asyncio
    async def test_evaluate_prompt_with_task_alignment(self, engine, mocker):
        """Test that aligned prompts are evaluated on quality."""
        # Mock settings
        mock_settings = mocker.Mock()
        mock_settings.max_tokens_feedback = 512
        mock_settings.temperature_feedback = 0.3
        engine.settings = mock_settings

        # Mock AI response for aligned prompt
        engine.ai_client.call_with_fallback.return_value = """{
            "score": 8,
            "strengths": [
                "Addresses the task correctly with 4-prompt chain",
                "Clear handoffs between prompts"
            ],
            "improvements": [
                "Could add more specific role definitions",
                "Consider specifying output format for each step"
            ]
        }"""

        engine.template_manager.render.return_value = "Rendered prompt"

        result = await engine.evaluate_user_prompt(
            user_prompt="Prompt 1: Research trending topics in [industry]... Prompt 2: Using the topics from above, generate 10 headlines...",
            lesson_id=12,
            exercise_scenario="You want to create a content marketing workflow",
            exercise_task="Design a 4-prompt chain: topic research → headline generation → outline creation → first draft",
            skill_level="advanced",
            learning_goal="professional",
        )

        assert result["score"] >= 7  # Good score for aligned, quality prompt
        assert "Addresses the task correctly" in result["strengths"][0]

    @pytest.mark.asyncio
    async def test_evaluate_prompt_backward_compatibility(self, engine, mocker):
        """Test that evaluation works without exercise context (backward compatibility)."""
        # Mock settings
        mock_settings = mocker.Mock()
        mock_settings.max_tokens_feedback = 512
        mock_settings.temperature_feedback = 0.3
        engine.settings = mock_settings

        # Mock AI response
        engine.ai_client.call_with_fallback.return_value = """{
            "score": 6,
            "strengths": ["Good attempt"],
            "improvements": ["Add more context"]
        }"""

        engine.template_manager.render.return_value = "Rendered prompt"

        # Call without exercise_scenario and exercise_task (using defaults)
        result = await engine.evaluate_user_prompt(
            user_prompt="Test prompt",
            lesson_id=1,
            skill_level="beginner",
            learning_goal="academic",
        )

        assert result["score"] == 6
        # Verify template was called with empty scenario/task
        call_args = engine.template_manager.render.call_args[1]
        assert call_args["exercise_scenario"] == ""
        assert call_args["exercise_task"] == ""


class TestProgressTracker:
    """Tests for ProgressTracker."""

    @pytest.fixture
    def tracker(self, mocker):
        """Create progress tracker with mocked repo."""
        mock_repo = mocker.AsyncMock()
        return ProgressTracker(mock_repo)

    @pytest.mark.asyncio
    async def test_start_lesson(self, tracker):
        """Test starting a lesson."""
        user_id = 123
        lesson_id = 456

        # Mock the repo to return None (no existing progress)
        tracker.progress_repo.find_by_user_and_lesson.return_value = None
        tracker.progress_repo.create.return_value = None

        await tracker.start_lesson(user_id, lesson_id)

        # Verify the repo methods were called correctly
        tracker.progress_repo.find_by_user_and_lesson.assert_called_once_with(user_id, lesson_id)
        tracker.progress_repo.create.assert_called_once_with(user_id, lesson_id)

    @pytest.mark.asyncio
    async def test_mark_completed(self, tracker):
        """Test marking lesson as completed."""
        user_id = 123
        lesson_id = 456
        score = 85

        # Create a mock progress object
        mock_progress = type(
            "MockProgress", (), {"status": None, "last_score": None, "completed_at": None}
        )()

        tracker.progress_repo.find_by_user_and_lesson.return_value = mock_progress

        await tracker.mark_completed(user_id, lesson_id, score)

        # Verify the repository methods were called correctly
        tracker.progress_repo.update_status.assert_called_once_with(
            user_id, lesson_id, LessonStatus.COMPLETED
        )
        tracker.progress_repo.update_score.assert_called_once_with(user_id, lesson_id, score)

    @pytest.mark.asyncio
    async def test_record_attempt(self, tracker):
        """Test recording exercise attempt."""
        user_id = 123
        lesson_id = 456
        score = 75

        # Create a mock progress object
        mock_progress = type("MockProgress", (), {"attempts": 0, "last_score": None})()

        tracker.progress_repo.find_by_user_and_lesson.return_value = mock_progress

        await tracker.record_attempt(user_id, lesson_id, score)

        # Verify the repo methods were called
        tracker.progress_repo.increment_attempts.assert_called_once_with(user_id, lesson_id)
        tracker.progress_repo.update_score.assert_called_once_with(user_id, lesson_id, score)

    @pytest.mark.asyncio
    async def test_get_progress_summary(self, tracker):
        """Test getting progress summary."""
        user_id = 123

        # Create mock progress records
        mock_progresses = [
            type("MockProgress", (), {"status": LessonStatus.COMPLETED, "last_score": 80})(),
            type("MockProgress", (), {"status": LessonStatus.COMPLETED, "last_score": 90})(),
            type("MockProgress", (), {"status": LessonStatus.IN_PROGRESS, "last_score": None})(),
        ]

        tracker.progress_repo.find_by_user.return_value = mock_progresses

        summary = await tracker.get_progress_summary(user_id)

        assert summary["completed"] == 2
        assert summary["total"] == 3
        assert summary["average_score"] == 85.0


class TestLearningFlowOrchestrator:
    """Tests for LearningFlowOrchestrator."""

    @pytest.fixture
    async def orchestrator(self, mocker):
        """Create orchestrator with mocked repos."""
        mock_user_repo = mocker.AsyncMock()
        mock_lesson_repo = mocker.AsyncMock()
        mock_session_repo = mocker.AsyncMock()
        return LearningFlowOrchestrator(mock_user_repo, mock_lesson_repo, mock_session_repo)

    @pytest.mark.asyncio
    async def test_get_personalized_path(self, orchestrator):
        """Test getting personalized lesson path."""
        user_id = 123

        # Mock user and lessons
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_lessons = [
            type("MockLesson", (), {"id": 1, "title": "Lesson 1", "position": 1})(),
            type("MockLesson", (), {"id": 2, "title": "Lesson 2", "position": 2})(),
            type("MockLesson", (), {"id": 3, "title": "Lesson 3", "position": 3})(),
        ]

        orchestrator.user_repo.find_by_telegram_id.return_value = mock_user
        orchestrator.lesson_repo.find_by_skill_level.return_value = mock_lessons

        path = await orchestrator.get_personalized_path(user_id, SkillLevel.BEGINNER)

        assert len(path) == 3
        assert path[0]["title"] == "Lesson 1"
        assert path[1]["title"] == "Lesson 2"
        assert path[2]["title"] == "Lesson 3"

    @pytest.mark.asyncio
    async def test_get_next_lesson(self, orchestrator):
        """Test getting next lesson in sequence."""
        user_id = 123
        current_lesson_id = 1

        # Mock user and lessons
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_current_lesson = type("MockLesson", (), {"position": 1})()
        mock_next_lesson = type(
            "MockLesson", (), {"id": 2, "title": "Lesson 2", "position": 2}
        )()

        orchestrator.user_repo.find_by_telegram_id.return_value = mock_user
        orchestrator.lesson_repo.find_by_id.return_value = mock_current_lesson
        orchestrator.lesson_repo.find_next_lesson.return_value = mock_next_lesson

        next_lesson = await orchestrator.get_next_lesson(user_id, current_lesson_id)

        assert next_lesson is not None
        assert next_lesson["title"] == "Lesson 2"
        assert next_lesson["order"] == 2

    @pytest.mark.asyncio
    async def test_get_next_lesson_last_lesson(self, orchestrator):
        """Test getting next lesson when on last lesson."""
        user_id = 123
        current_lesson_id = 3

        # Mock user and lessons
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_current_lesson = type("MockLesson", (), {"position": 3})()

        orchestrator.user_repo.find_by_telegram_id.return_value = mock_user
        orchestrator.lesson_repo.find_by_id.return_value = mock_current_lesson
        orchestrator.lesson_repo.find_next_lesson.return_value = None

        next_lesson = await orchestrator.get_next_lesson(user_id, current_lesson_id)

        assert next_lesson is None

    @pytest.mark.asyncio
    async def test_update_session_state(self, orchestrator):
        """Test updating session state."""
        user_id = 123
        context = {"current_step": "assessment", "question": 1}

        await orchestrator.update_session_state(user_id, SessionState.ONBOARDING, context)

        # Verify the session repo was called
        orchestrator.session_repo.create_or_update.assert_called_once_with(
            user_id, SessionState.ONBOARDING, context
        )


class TestMessageFormatter:
    """Tests for MessageFormatter."""

    def test_format_welcome(self):
        """Test welcome message formatting."""
        from promptheus.bot.message_formatter import MessageFormatter

        formatter = MessageFormatter()
        message = formatter.format_welcome()

        assert "Welcome" in message
        assert "Promptheus" in message

    def test_format_question(self):
        """Test question formatting."""
        from promptheus.bot.message_formatter import MessageFormatter

        formatter = MessageFormatter()
        message = formatter.format_question(
            1, 5, "What is prompt engineering?", ["A) Option 1", "B) Option 2"]
        )

        assert "Question 1/5" in message
        assert "What is prompt engineering?" in message
        assert "A) Option 1" in message

    def test_format_lesson_complete(self):
        """Test lesson completion message."""
        from promptheus.bot.message_formatter import MessageFormatter

        formatter = MessageFormatter()
        message = formatter.format_lesson_complete("Test Lesson", 85, 2)

        assert "completed" in message.lower()
        assert "Test Lesson" in message
        assert "85" in message
        assert "2" in message
