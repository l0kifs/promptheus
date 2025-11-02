"""Seed initial lessons into the database."""

from loguru import logger

from promptheus.data.database import Base, engine, get_db
from promptheus.data.models import SkillLevel
from promptheus.data.repositories import LessonRepository


def seed_lessons() -> None:
    """Seed initial 5 foundational lessons."""
    logger.info("Seeding lessons...")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    lessons = [
        {
            "title": "Introduction to Prompt Engineering",
            "skill_level": SkillLevel.BEGINNER,
            "order_index": 1,
            "tags": ["general", "academic", "professional", "creative"],
            "theory_content": {
                "sections": [
                    {
                        "content": "Prompt engineering is the art of crafting effective instructions for AI. Like talking to an expert, clearer questions get better answers."
                    },
                    {
                        "content": "Key principle: AI needs context, clarity, and structure. The more specific you are, the better the response."
                    },
                ]
            },
            "examples": {
                "comparisons": [
                    {
                        "bad": "Tell me about Python",
                        "bad_reason": "Too vague - what aspect? What level?",
                        "good": "Explain Python list comprehensions to a beginner with a simple example",
                        "good_reason": "Specific topic, target audience, and format",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "You need help learning a new programming concept",
                        "task": "Write a prompt asking AI to explain object-oriented programming",
                    }
                ]
            },
        },
        {
            "title": "Defining AI Roles",
            "skill_level": SkillLevel.BEGINNER,
            "order_index": 2,
            "tags": ["role-based", "academic", "professional", "role-definition"],
            "theory_content": {
                "sections": [
                    {
                        "content": "Assigning a role helps AI adopt appropriate tone, expertise, and style. Think 'You are a...' at the start of your prompt."
                    },
                    {
                        "content": "Good roles: specific expert (senior developer), clear persona (patient teacher), defined context (career advisor with 10 years experience)."
                    },
                ]
            },
            "examples": {
                "comparisons": [
                    {
                        "bad": "Explain machine learning",
                        "bad_reason": "No role defined, unclear audience",
                        "good": "You are a university professor. Explain machine learning to first-year students using everyday analogies",
                        "good_reason": "Clear role, defined audience, specific approach",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "You need diet advice for weight loss",
                        "task": "Write a prompt with a nutrition expert role asking for a meal plan",
                    }
                ]
            },
        },
        {
            "title": "Providing Context",
            "skill_level": SkillLevel.BEGINNER,
            "order_index": 3,
            "tags": ["context-heavy", "professional", "context-provision"],
            "theory_content": {
                "sections": [
                    {
                        "content": "Context is background information that helps AI understand your situation. Include: your level, constraints, goals, and relevant details."
                    },
                    {
                        "content": "More context = more relevant answers. But keep it focused - only include what's necessary for the task."
                    },
                ]
            },
            "examples": {
                "comparisons": [
                    {
                        "bad": "Help me with my website",
                        "bad_reason": "What website? What help? No context",
                        "good": "I'm building an e-commerce site for handmade crafts. I need help choosing between WordPress and Shopify. Budget: $500, no coding experience",
                        "good_reason": "Clear purpose, constraints, skill level, budget",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "You're learning Spanish for a 3-month trip to Spain",
                        "task": "Write a prompt with full context asking for a study plan",
                    }
                ]
            },
        },
        {
            "title": "Setting Clear Objectives",
            "skill_level": SkillLevel.BEGINNER,
            "order_index": 4,
            "tags": ["clear-objectives", "professional", "academic"],
            "theory_content": {
                "sections": [
                    {
                        "content": "Clear objectives tell AI exactly what you want. Use action verbs: explain, create, analyze, summarize, compare, list."
                    },
                    {
                        "content": "Be specific about deliverables: 'Write 3 bullet points' is better than 'tell me about'. Define the end result you need."
                    },
                ]
            },
            "examples": {
                "comparisons": [
                    {
                        "bad": "Something about marketing strategies",
                        "bad_reason": "Vague objective, no clear request",
                        "good": "List 5 digital marketing strategies for a small bakery. For each, provide: description, cost range, expected ROI",
                        "good_reason": "Clear number, specific format, defined details",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "You need to prepare a presentation on climate change",
                        "task": "Write a prompt with clear objectives asking for an outline",
                    }
                ]
            },
        },
        {
            "title": "Specifying Output Format",
            "skill_level": SkillLevel.BEGINNER,
            "order_index": 5,
            "tags": ["formatting", "output-formatting", "professional"],
            "theory_content": {
                "sections": [
                    {
                        "content": "Format specification guides how AI structures the response. Options: bullet points, table, step-by-step, code, essay, JSON."
                    },
                    {
                        "content": "Be explicit: 'Format as numbered list' or 'Provide as markdown table'. This ensures you get usable output first time."
                    },
                ]
            },
            "examples": {
                "comparisons": [
                    {
                        "bad": "Compare React and Vue",
                        "bad_reason": "No format specified, unclear how to present",
                        "good": "Compare React and Vue in a table with columns: Feature, React, Vue. Include: learning curve, performance, community, use cases",
                        "good_reason": "Specific format (table), defined structure (columns), clear content (rows)",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "You need a morning routine for productivity",
                        "task": "Write a prompt specifying a step-by-step format with time estimates",
                    }
                ]
            },
        },
    ]

    with get_db() as db:
        lesson_repo = LessonRepository(db)

        for lesson_data in lessons:
            logger.info(f"Creating lesson: {lesson_data['title']}")
            try:
                lesson_repo.create(**lesson_data)  # type: ignore
                logger.success(f"Created: {lesson_data['title']}")
            except Exception as e:
                logger.error(f"Error creating lesson {lesson_data['title']}: {e}")

    logger.success("Lessons seeded successfully!")


if __name__ == "__main__":
    seed_lessons()
