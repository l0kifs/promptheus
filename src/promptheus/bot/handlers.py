"""Telegram bot handlers."""

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
from promptheus.data.models import LearningGoal, SkillLevel
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

    async def lesson_start_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle lesson start button - begin showing theory content."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        # Extract lesson ID
        lesson_id = int(update.callback_query.data.split("_")[2])  # type: ignore

        with get_db() as db:
            lesson_repo = LessonRepository(db)
            lesson = lesson_repo.find_by_id(lesson_id)

            if not lesson:
                await update.callback_query.edit_message_text(
                    self.formatter.format_error("Lesson not found")
                )
                return

            # Get theory content
            theory_content = lesson.theory_content  # type: ignore
            sections = theory_content.get("sections", [])

            if not sections:
                await update.callback_query.edit_message_text(
                    self.formatter.format_error("No theory content available")
                )
                return

            # Store current position in context
            context.user_data["current_lesson_id"] = lesson_id  # type: ignore
            context.user_data["theory_section"] = 0  # type: ignore
            context.user_data["lesson_step"] = "theory"  # type: ignore

            # Show first theory section
            first_section = sections[0]
            total_sections = len(sections)

            keyboard = []
            if total_sections > 1:
                keyboard.append(
                    [InlineKeyboardButton("Next ➡️", callback_data=f"theory_next_{lesson_id}")]
                )
            else:
                keyboard.append(
                    [InlineKeyboardButton("Continue ➡️", callback_data=f"examples_{lesson_id}")]
                )
            keyboard.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")])

            await update.callback_query.edit_message_text(
                f"💡 *Theory* (1/{total_sections})\n\n{first_section['content']}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    async def theory_next_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle next theory section button."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        # Extract lesson ID
        lesson_id = int(update.callback_query.data.split("_")[2])  # type: ignore

        # Get current section from context
        current_section = context.user_data.get("theory_section", 0)  # type: ignore
        next_section = current_section + 1

        with get_db() as db:
            lesson_repo = LessonRepository(db)
            lesson = lesson_repo.find_by_id(lesson_id)

            if not lesson:
                await update.callback_query.edit_message_text(
                    self.formatter.format_error("Lesson not found")
                )
                return

            theory_content = lesson.theory_content  # type: ignore
            sections = theory_content.get("sections", [])

            if next_section >= len(sections):
                # Move to examples
                context.user_data["lesson_step"] = "examples"  # type: ignore
                await self._show_examples(update, context, lesson_id, lesson)
                return

            # Update context
            context.user_data["theory_section"] = next_section  # type: ignore

            # Show next section
            section = sections[next_section]
            total_sections = len(sections)

            keyboard = []
            if next_section < total_sections - 1:
                keyboard.append(
                    [InlineKeyboardButton("Next ➡️", callback_data=f"theory_next_{lesson_id}")]
                )
            else:
                keyboard.append(
                    [InlineKeyboardButton("Continue to Examples ➡️", callback_data=f"examples_{lesson_id}")]
                )
            keyboard.append(
                [InlineKeyboardButton("⬅️ Back", callback_data=f"theory_prev_{lesson_id}")]
            )

            await update.callback_query.edit_message_text(
                f"💡 *Theory* ({next_section + 1}/{total_sections})\n\n{section['content']}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    async def examples_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle examples section."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        # Extract lesson ID
        lesson_id = int(update.callback_query.data.split("_")[1])  # type: ignore

        with get_db() as db:
            lesson_repo = LessonRepository(db)
            lesson = lesson_repo.find_by_id(lesson_id)

            if not lesson:
                await update.callback_query.edit_message_text(
                    self.formatter.format_error("Lesson not found")
                )
                return

            await self._show_examples(update, context, lesson_id, lesson)

    async def _show_examples(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        lesson_id: int,
        lesson: Any,
    ) -> None:
        """Show examples section."""
        from promptheus.data.models import Lesson

        if not isinstance(lesson, Lesson):
            return

        examples = lesson.examples  # type: ignore
        comparisons = examples.get("comparisons", [])

        if not comparisons:
            # Skip to exercises
            await update.callback_query.edit_message_text(  # type: ignore
                "No examples available. Moving to practice...",
                parse_mode="Markdown",
            )
            return

        # Show first comparison
        comparison = comparisons[0]

        keyboard = [
            [InlineKeyboardButton("Continue to Practice ➡️", callback_data=f"practice_{lesson_id}")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")],
        ]

        example_text = "📊 *Examples*\n\n"
        example_text += f"❌ *Bad Prompt:*\n{comparison['bad']}\n\n"
        example_text += f"*Problem:* {comparison['bad_reason']}\n\n"
        example_text += f"✅ *Good Prompt:*\n{comparison['good']}\n\n"
        example_text += f"*Why better:* {comparison['good_reason']}"

        await update.callback_query.edit_message_text(  # type: ignore
            example_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def practice_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle practice section."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        # Extract lesson ID
        lesson_id = int(update.callback_query.data.split("_")[1])  # type: ignore

        with get_db() as db:
            lesson_repo = LessonRepository(db)
            lesson = lesson_repo.find_by_id(lesson_id)

            if not lesson:
                await update.callback_query.edit_message_text(
                    self.formatter.format_error("Lesson not found")
                )
                return

            exercises = lesson.exercises  # type: ignore
            scenarios = exercises.get("scenarios", [])

            if not scenarios:
                # No exercises, complete the lesson
                await update.callback_query.edit_message_text(
                    "🎉 *Lesson Complete!*\n\nGreat job finishing this lesson!",
                    parse_mode="Markdown",
                )
                return

            # Show first exercise
            scenario = scenarios[0]

            # Store in context for later submission
            context.user_data["current_lesson_id"] = lesson_id  # type: ignore
            context.user_data["lesson_step"] = "practice"  # type: ignore

            keyboard = [
                [InlineKeyboardButton("💡 Show Hint", callback_data=f"hint_{lesson_id}")],
                [InlineKeyboardButton("⏭️ Skip Exercise", callback_data=f"skip_{lesson_id}")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")],
            ]

            practice_text = "✏️ *Practice Exercise*\n\n"
            practice_text += f"*Scenario:*\n{scenario['scenario']}\n\n"
            practice_text += f"*Your Task:*\n{scenario['task']}\n\n"
            practice_text += "💬 Send your prompt in the next message."

            await update.callback_query.edit_message_text(
                practice_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    async def text_message_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle text messages (user prompt submissions during practice)."""
        if not update.effective_user or not update.message or not update.message.text:
            return

        user_id = update.effective_user.id
        user_prompt = update.message.text

        # Check if user is in practice mode
        lesson_step = context.user_data.get("lesson_step")  # type: ignore

        if lesson_step != "practice":
            # User is not in practice mode, send a helpful message
            await update.message.reply_text(
                "👋 Use /menu to navigate or /start to begin learning!",
                parse_mode="Markdown",
            )
            return

        # Get current lesson
        lesson_id = context.user_data.get("current_lesson_id")  # type: ignore

        if not lesson_id:
            await update.message.reply_text(
                "⚠️ Please start a lesson first using /menu",
                parse_mode="Markdown",
            )
            return

        # Show loading message
        loading_msg = await update.message.reply_text(
            "⏳ Analyzing your prompt...",
            parse_mode="Markdown",
        )

        try:
            # Get AI feedback
            assessment_engine = AssessmentEngine(self.ai_client)
            feedback = await assessment_engine.evaluate_user_prompt(
                user_prompt, lesson_id
            )

            # Update progress
            with get_db() as db:
                progress_tracker = ProgressTracker(db)
                progress_tracker.increment_attempts(user_id, lesson_id)

                # If score is good enough, mark as completed
                if feedback.get("score", 0) >= 7:
                    progress_tracker.complete_lesson(
                        user_id, lesson_id, feedback.get("score", 0)
                    )

            # Format and send feedback
            feedback_text = "📝 *Your Prompt:*\n"
            feedback_text += f"_{user_prompt}_\n\n"
            feedback_text += f"🔍 *Score:* {feedback.get('score', 0)}/10\n\n"

            if feedback.get("strengths"):
                feedback_text += "✅ *Strengths:*\n"
                for strength in feedback.get("strengths", []):
                    feedback_text += f"• {strength}\n"
                feedback_text += "\n"

            if feedback.get("improvements"):
                feedback_text += "💡 *Suggestions for Improvement:*\n"
                for improvement in feedback.get("improvements", []):
                    feedback_text += f"• {improvement}\n"

            keyboard = []
            if feedback.get("score", 0) >= 7:
                keyboard.append(
                    [InlineKeyboardButton("🎉 Lesson Complete!", callback_data=f"lesson_complete_{lesson_id}")]
                )
            else:
                keyboard.append(
                    [InlineKeyboardButton("🔄 Try Again", callback_data=f"practice_{lesson_id}")]
                )
            keyboard.append([InlineKeyboardButton("📚 Back to Menu", callback_data="menu")])

            # Delete loading message and send feedback
            await loading_msg.delete()
            await update.message.reply_text(
                feedback_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error evaluating prompt: {e}")
            await loading_msg.edit_text(
                "❌ Sorry, there was an error evaluating your prompt. Please try again.",
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

    async def continue_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle continue learning callback."""
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

            # Check if user has a current lesson
            if user.current_lesson_id:
                # Resume current lesson
                lesson_repo = LessonRepository(db)
                lesson = lesson_repo.find_by_id(user.current_lesson_id)

                if lesson:
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                "▶️ Resume", callback_data=f"lesson_{lesson.id}"
                            )
                        ],
                        [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
                        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")],
                    ]

                    await update.callback_query.edit_message_text(
                        f"📖 *Resume Learning*\n\nContinue with:\n{lesson.title}",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown",
                    )
                    return

            # No current lesson, show lesson list
            lesson_repo = LessonRepository(db)
            lessons = lesson_repo.find_by_skill_level(user.skill_level)  # type: ignore
            if not lessons:
                lessons = lesson_repo.find_by_skill_level(SkillLevel.BEGINNER)

            if not lessons:
                await update.callback_query.edit_message_text(
                    self.formatter.format_error("No lessons available yet."),
                    parse_mode="Markdown",
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

    async def error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle errors."""
        logger.error(f"Exception while handling an update: {context.error}")
