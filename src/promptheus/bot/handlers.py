"""Telegram bot handlers."""

import asyncio
from typing import Any

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.bot.message_formatter import MessageFormatter
from promptheus.core.assessment_engine import AssessmentEngine
from promptheus.core.learning_flow_orchestrator import LearningFlowOrchestrator
from promptheus.core.progress_tracker import ProgressTracker
from promptheus.data.database import get_db
from promptheus.data.models import LearningGoal, SessionState, SkillLevel
from promptheus.data.repositories import LessonRepository, UserRepository


class BotHandlers:
    """Handlers for Telegram bot commands and callbacks."""

    def __init__(
        self,
        ai_client: OpenRouterClient,
    ) -> None:
        """Initialize handlers."""
        self.ai_client = ai_client
        self.formatter = MessageFormatter()

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        if not update.effective_user or not update.message:
            return

        user_id = update.effective_user.id

        with get_db() as db:
            user_repo = UserRepository(db)
            user = user_repo.find_by_telegram_id(user_id)

            if user:
                # Returning user
                keyboard = [
                    [InlineKeyboardButton("▶️ Continue", callback_data="continue")],
                    [InlineKeyboardButton("📚 Menu", callback_data="menu")],
                ]
                await update.message.reply_text(
                    "👋 Welcome back!", reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                # New user
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "▶️ Start Learning", callback_data="start_learning"
                        )
                    ]
                ]
                await update.message.reply_text(
                    self.formatter.format_welcome(),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )

    async def start_learning_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle start learning button."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        keyboard = [
            [InlineKeyboardButton("🚀 Start Test", callback_data="start_assessment")]
        ]

        await update.callback_query.edit_message_text(
            self.formatter.format_assessment_intro(),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def start_assessment_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle assessment start."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        # Initialize assessment in context
        assessment_engine = AssessmentEngine(self.ai_client)
        questions = assessment_engine.get_assessment_questions()

        context.user_data["assessment_questions"] = questions  # type: ignore
        context.user_data["assessment_answers"] = []  # type: ignore
        context.user_data["current_question"] = 0  # type: ignore

        # Show first question
        await self._show_question(update, context)

    async def _show_question(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show current assessment question."""
        if not update.callback_query:
            return

        questions = context.user_data.get("assessment_questions", [])  # type: ignore
        current = context.user_data.get("current_question", 0)  # type: ignore

        if current >= len(questions):
            await self._finish_assessment(update, context)
            return

        question = questions[current]
        keyboard = [
            [InlineKeyboardButton(opt, callback_data=f"answer_{opt[0]}")] for opt in question["options"]  # type: ignore
        ]

        await update.callback_query.edit_message_text(
            self.formatter.format_question(
                current + 1,
                len(questions),
                question["question"],  # type: ignore
                question["options"],  # type: ignore
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def answer_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle answer to assessment question."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        # Extract answer
        answer = update.callback_query.data.split("_")[1]  # type: ignore
        context.user_data["assessment_answers"].append(answer)  # type: ignore
        context.user_data["current_question"] += 1  # type: ignore

        # Show next question
        await self._show_question(update, context)

    async def _finish_assessment(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Finish assessment and show goal selection."""
        if not update.effective_user or not update.callback_query:
            return

        # Calculate results
        assessment_engine = AssessmentEngine(self.ai_client)
        answers = context.user_data.get("assessment_answers", [])  # type: ignore
        results = await assessment_engine.evaluate_answers(answers)

        # Store results
        context.user_data["assessment_results"] = results  # type: ignore

        # Show goal selection
        keyboard = [
            [InlineKeyboardButton("🎓 Academic", callback_data="goal_academic")],
            [InlineKeyboardButton("💼 Professional", callback_data="goal_professional")],
            [InlineKeyboardButton("🎨 Creative", callback_data="goal_creative")],
        ]

        await update.callback_query.edit_message_text(
            self.formatter.format_goal_selection(),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def goal_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle goal selection."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        # Extract goal
        goal_map = {
            "goal_academic": LearningGoal.ACADEMIC,
            "goal_professional": LearningGoal.PROFESSIONAL,
            "goal_creative": LearningGoal.CREATIVE,
        }

        goal = goal_map.get(update.callback_query.data, LearningGoal.PROFESSIONAL)  # type: ignore

        # Get assessment results
        results = context.user_data.get("assessment_results", {})  # type: ignore
        skill_level_str = results.get("level", "beginner")
        skill_level = SkillLevel(skill_level_str)

        # Create user
        user_id = update.effective_user.id
        username = update.effective_user.username

        with get_db() as db:
            user_repo = UserRepository(db)
            user_repo.create(
                telegram_id=user_id,
                username=username,
                skill_level=skill_level,
                learning_goal=goal,
            )
            user_repo.update_assessment_score(user_id, results.get("score", 0))  # type: ignore

            # Get personalized path
            orchestrator = LearningFlowOrchestrator(db)
            lessons = orchestrator.get_personalized_path(user_id, skill_level)

            # If no lessons for this level, fallback to beginner lessons
            if not lessons:
                logger.warning(
                    f"No lessons found for {skill_level}, falling back to BEGINNER"
                )
                lessons = orchestrator.get_personalized_path(user_id, SkillLevel.BEGINNER)

            # Show path
            if lessons:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🚀 First Lesson", callback_data=f"lesson_{lessons[0]['id']}"
                        )
                    ],
                    [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
                ]

                await update.callback_query.edit_message_text(
                    self.formatter.format_personalized_path(
                        skill_level_str, goal.value, lessons
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
            else:
                # No lessons available at all
                await update.callback_query.edit_message_text(
                    self.formatter.format_error(
                        "No lessons available yet. Please check back later!"
                    ),
                    parse_mode="Markdown",
                )

    async def lesson_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle lesson selection."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        # Extract lesson ID
        lesson_id = int(update.callback_query.data.split("_")[1])  # type: ignore

        user_id = update.effective_user.id

        with get_db() as db:
            lesson_repo = LessonRepository(db)
            lesson = lesson_repo.find_by_id(lesson_id)

            if not lesson:
                await update.callback_query.edit_message_text(
                    self.formatter.format_error("Lesson not found")
                )
                return

            # Start lesson
            progress_tracker = ProgressTracker(db)
            progress_tracker.start_lesson(user_id, lesson_id)

            # Store lesson in context
            context.user_data["current_lesson_id"] = lesson_id  # type: ignore
            context.user_data["lesson_step"] = "start"  # type: ignore

            keyboard = [
                [InlineKeyboardButton("▶️ Start", callback_data=f"lesson_start_{lesson_id}")],
                [InlineKeyboardButton("⬅️ Back", callback_data="lesson_list")],
            ]

            await update.callback_query.edit_message_text(
                self.formatter.format_lesson_start(
                    lesson.title, lesson.order_index  # type: ignore
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    async def lesson_list_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle lesson list request."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        user_id = update.effective_user.id

        with get_db() as db:
            user_repo = UserRepository(db)
            user = user_repo.find_by_telegram_id(user_id)

            if not user:
                await update.callback_query.edit_message_text(
                    self.formatter.format_error("User not found. Please /start again.")
                )
                return

            lesson_repo = LessonRepository(db)
            # Try to get lessons for user's level, fallback to beginner
            lessons = lesson_repo.find_by_skill_level(user.skill_level)  # type: ignore
            if not lessons:
                lessons = lesson_repo.find_by_skill_level(SkillLevel.BEGINNER)

            if not lessons:
                await update.callback_query.edit_message_text(
                    self.formatter.format_error("No lessons available yet.")
                )
                return

            # Format lesson list
            lesson_list = "\n".join(
                [f"{i+1}. {lesson.title}" for i, lesson in enumerate(lessons)]
            )

            keyboard = [
                [
                    InlineKeyboardButton(
                        f"▶️ Lesson {i+1}", callback_data=f"lesson_{lesson.id}"
                    )
                ]
                for i, lesson in enumerate(lessons[:5])  # Show first 5
            ]
            keyboard.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")])

            await update.callback_query.edit_message_text(
                f"📋 *Available Lessons*\n\n{lesson_list}\n\nChoose a lesson to begin:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    async def menu_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /menu command."""
        if not update.effective_user or not update.message:
            return

        keyboard = [
            [InlineKeyboardButton("📖 Continue Learning", callback_data="continue")],
            [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
            [InlineKeyboardButton("📊 My Progress", callback_data="progress")],
        ]

        await update.message.reply_text(
            "📚 *Main Menu*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def menu_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle menu callback."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        keyboard = [
            [InlineKeyboardButton("📖 Continue Learning", callback_data="continue")],
            [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
            [InlineKeyboardButton("📊 My Progress", callback_data="progress")],
        ]

        await update.callback_query.edit_message_text(
            "📚 *Main Menu*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle errors."""
        logger.error(f"Exception while handling an update: {context.error}")
