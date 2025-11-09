"""Tests for lesson slug generation."""

import pytest

from promptheus.data.lesson_loader import generate_slug


class TestSlugGeneration:
    """Test cases for slug generation utility."""

    @pytest.mark.parametrize(
        "title,expected",
        [
            ("Introduction to Prompt Engineering", "introduction-to-prompt-engineering"),
            ("Advanced Techniques & Best Practices", "advanced-techniques-best-practices"),
            ("Chain-of-Thought Prompting", "chain-of-thought-prompting"),
            ("Few-Shot Learning", "few-shot-learning"),
            ("Multi Step Task Decomposition", "multi-step-task-decomposition"),
            ("", ""),
            ("A", "a"),
            ("123 Numbers", "123-numbers"),
            ("Special@#$%Characters", "specialcharacters"),
            ("Multiple   Spaces", "multiple-spaces"),
            ("--Leading and trailing--", "leading-and-trailing"),
        ],
    )
    def test_generate_slug_basic_cases(self, title: str, expected: str) -> None:
        """Test basic slug generation cases."""
        assert generate_slug(title) == expected

    def test_generate_slug_max_length(self) -> None:
        """Test slug truncation at max length."""
        long_title = "A" * 200
        slug = generate_slug(long_title, max_length=50)
        assert len(slug) <= 50
        assert slug == "a" * 50

    def test_generate_slug_removes_trailing_hyphen_after_truncation(self) -> None:
        """Test that trailing hyphens are removed after truncation."""
        # Create a title that would end with a hyphen after truncation
        title = "word-" + "a" * 95  # This would create "word-aaaaa..." then truncate
        slug = generate_slug(title, max_length=10)
        assert not slug.endswith("-")
        assert len(slug) <= 10

    def test_generate_slug_case_insensitive(self) -> None:
        """Test that slug generation is case insensitive."""
        assert generate_slug("TEST TITLE") == "test-title"
        assert generate_slug("Test Title") == "test-title"
        assert generate_slug("test title") == "test-title"

    def test_generate_slug_consecutive_hyphens(self) -> None:
        """Test that consecutive hyphens are reduced to single hyphens."""
        assert generate_slug("test--title") == "test-title"
        assert generate_slug("test   title") == "test-title"
        assert generate_slug("test___title") == "test-title"

    def test_generate_slug_unicode_normalization(self) -> None:
        """Test handling of unicode characters."""
        # This should remove non-ascii characters
        slug = generate_slug("tëst título")
        # The exact behavior depends on the regex, but should be safe
        assert isinstance(slug, str)
        assert len(slug) > 0

    def test_generate_slug_empty_after_processing(self) -> None:
        """Test handling of titles that become empty after processing."""
        assert generate_slug("!!!") == ""
        assert generate_slug("@#$%") == ""
        assert generate_slug("   ") == ""

    def test_generate_slug_preserves_numbers(self) -> None:
        """Test that numbers are preserved in slugs."""
        assert generate_slug("Lesson 1: Introduction") == "lesson-1-introduction"
        assert generate_slug("Step 2 - Advanced") == "step-2-advanced"
