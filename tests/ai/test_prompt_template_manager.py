"""Unit tests for PromptTemplateManager."""

import pytest

from promptheus.ai.prompt_template_manager import PromptTemplateManager


class TestPromptTemplateManager:
    """Tests for PromptTemplateManager."""

    @pytest.fixture
    def manager(self):
        """Create fresh template manager for each test."""
        return PromptTemplateManager()

    def test_init_registers_default_templates(self, manager):
        """Test that default templates are registered on init."""
        assert "assessment_evaluation" in manager.templates
        assert "exercise_feedback" in manager.templates
        assert "improved_prompt_generation" in manager.templates

    def test_register_template(self, manager):
        """Test registering a new template."""
        manager.register_template("test_template", "Hello {name}!")
        assert manager.templates["test_template"] == "Hello {name}!"

    def test_render_template_success(self, manager):
        """Test successful template rendering."""
        manager.register_template("greeting", "Hello {user_name}, you are {age} years old!")
        result = manager.render("greeting", user_name="Alice", age=30)
        assert result == "Hello Alice, you are 30 years old!"

    def test_render_template_missing_template(self, manager):
        """Test error when rendering non-existent template."""
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            manager.render("nonexistent", user_name="Alice")

    def test_render_template_missing_variable(self, manager):
        """Test error when required variable is missing."""
        manager.register_template("greeting", "Hello {name}!")
        with pytest.raises(KeyError):
            manager.render("greeting")  # Missing 'name' variable

    def test_get_template_success(self, manager):
        """Test getting raw template."""
        template = "Test template with {placeholder}"
        manager.register_template("test", template)
        assert manager.get_template("test") == template

    def test_get_template_missing_template(self, manager):
        """Test error when getting non-existent template."""
        with pytest.raises(ValueError, match="Template 'missing' not found"):
            manager.get_template("missing")

    def test_default_assessment_evaluation_template(self, manager):
        """Test default assessment_evaluation template structure."""
        template = manager.get_template("assessment_evaluation")
        assert "{skill_level}" in template
        assert "{learning_goal}" in template
        assert "{user_prompt}" in template
        assert "{criteria}" in template
        assert "JSON format" in template

    def test_default_exercise_feedback_template(self, manager):
        """Test default exercise_feedback template structure."""
        template = manager.get_template("exercise_feedback")
        assert "{user_prompt}" in template
        assert "{skill_level}" in template
        assert "{learning_goal}" in template
        assert "JSON format" in template

    def test_default_improved_prompt_generation_template(self, manager):
        """Test default improved_prompt_generation template structure."""
        template = manager.get_template("improved_prompt_generation")
        assert "{user_prompt}" in template
        assert "{skill_level}" in template
        assert "{learning_goal}" in template
        assert "improved version" in template

    def test_render_default_template(self, manager):
        """Test rendering a default template."""
        result = manager.render(
            "assessment_evaluation",
            skill_level="beginner",
            learning_goal="academic",
            user_prompt="Write a summary",
            criteria="clarity, structure",
        )
        assert "beginner" in result
        assert "academic" in result
        assert "Write a summary" in result
        assert "clarity, structure" in result
