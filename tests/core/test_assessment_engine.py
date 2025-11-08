"""Tests for AssessmentEngine."""

import pytest

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.ai.prompt_template_manager import PromptTemplateManager
from promptheus.core.assessment_engine import AssessmentEngine


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

    def test_get_assessment_questions_returns_five_questions_with_required_fields(self, engine):
        """Test getting assessment questions."""
        questions = engine.get_assessment_questions()

        assert len(questions) == 5
        assert all("question" in q for q in questions)
        assert all("options" in q for q in questions)
        assert all("correct" in q for q in questions)

    @pytest.mark.asyncio
    async def test_evaluate_answers_with_all_correct_answers_returns_perfect_score(self, engine):
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
    async def test_evaluate_answers_with_incorrect_answers_returns_beginner_level(self, engine):
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
    async def test_evaluate_answers_with_mixed_answers_returns_intermediate_level(self, engine):
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
    async def test_evaluate_answers_with_valid_answers_calls_ai_and_returns_assessment(
        self, engine
    ):
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
    async def test_evaluate_answers_when_ai_fails_uses_fallback_logic(self, engine):
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
    async def test_evaluate_answers_with_wrong_question_count_raises_value_error(self, engine):
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
    async def test_parse_assessment_response_with_valid_json_returns_parsed_data(self, engine):
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
    async def test_parse_assessment_fallback_with_text_returns_heuristic_assessment(self, engine):
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
    async def test_evaluate_answers_when_ai_returns_invalid_json_uses_fallback_parsing(
        self, engine
    ):
        """Test that evaluation uses fallback parsing when AI returns invalid JSON."""
        answers = ["B", "C", "A", "B", "B"]

        # Mock AI response with invalid JSON
        engine.ai_client.call_with_fallback.return_value = "This is not JSON, just some text about excellent performance and advanced understanding."
        engine.template_manager.render.return_value = "Mocked prompt"

        result = await engine.evaluate_answers(answers)

        # Should use fallback parsing logic
        assert isinstance(result["score"], int)
        assert result["level"] in ["beginner", "intermediate", "advanced"]
        assert "analysis" in result
        assert "strengths" in result
        assert "areas_for_improvement" in result
        # Should not have fallback key since parsing succeeded (fallback parsing)
        assert "fallback" not in result

    @pytest.mark.asyncio
    async def test_evaluate_user_prompt_uses_template_manager_and_settings_for_ai_call(
        self, engine, mocker
    ):
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
            user_prompt="Test prompt", lesson_id=1, skill_level="beginner", learning_goal="academic"
        )

        # Verify template manager was called correctly
        engine.template_manager.render.assert_called_once_with(
            "exercise_feedback",
            user_prompt="Test prompt",
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
    async def test_evaluate_user_prompt_when_ai_returns_invalid_json_uses_fallback_logic(
        self, engine, mocker
    ):
        """Test that evaluate_user_prompt uses fallback when AI returns invalid JSON."""
        # Mock settings
        mock_settings = mocker.Mock()
        mock_settings.max_tokens_feedback = 512
        mock_settings.temperature_feedback = 0.3
        engine.settings = mock_settings

        # Mock AI client to return invalid JSON
        engine.ai_client.call_with_fallback.return_value = (
            "This is not JSON, just some feedback text about the prompt being good."
        )

        # Mock template manager
        engine.template_manager.render.return_value = "Rendered prompt"

        result = await engine.evaluate_user_prompt(
            user_prompt="Test prompt", lesson_id=1, skill_level="beginner", learning_goal="academic"
        )

        # Should use fallback logic
        assert result["score"] == 5  # Default fallback score
        assert result["strengths"] == ["Good attempt at creating a prompt"]
        assert result["improvements"] == [
            "Try adding more specific context",
            "Consider defining a clear role for the AI",
        ]
