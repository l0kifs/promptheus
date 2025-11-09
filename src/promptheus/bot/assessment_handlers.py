"""Assessment handlers for Telegram bot."""

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from promptheus.data.models import LearningGoal, SkillLevel


class AssessmentHandlersMixin:
    """Mixin for user assessment and onboarding."""

    async def start_learning_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle start learning button."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        keyboard = [[InlineKeyboardButton("🚀 Start Test", callback_data="start_assessment")]]

        try:
            await update.callback_query.edit_message_text(
                self.formatter.format_assessment_intro(),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                raise

    async def start_assessment_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle assessment start."""
        if not update.effective_user or not update.callback_query:
            logger.warning("Invalid assessment start: missing user or callback")
            return

        await update.callback_query.answer()

        user_id = update.effective_user.id
        logger.info("Starting assessment", user_id=user_id)

        # Load session context
        session_context = await self.learning_orchestrator.get_session_context(user_id)
        # context.user_data.update(session_context)  # Removed: using DB session instead

        # Initialize assessment in session context
        assessment_engine = self.assessment_engine
        questions = assessment_engine.get_assessment_questions()

        session_context["assessment_questions"] = questions
        session_context["assessment_answers"] = []
        session_context["current_question"] = 0

        # Save session context
        await self.learning_orchestrator.save_session_context(user_id, session_context)

        # Update session state to ONBOARDING
        from promptheus.data.models import SessionState

        await self.learning_orchestrator.update_session_state(
            user_id, SessionState.ONBOARDING, session_context
        )

        logger.debug("Assessment initialized", user_id=user_id, total_questions=len(questions))

        # Show first question
        await self._show_question(update, context)

    async def _show_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show current assessment question."""
        if not update.callback_query:
            return

        user_id = update.effective_user.id
        session_context = await self.learning_orchestrator.get_session_context(user_id)
        # context.user_data.update(session_context)  # Removed: using DB session instead

        questions = session_context.get("assessment_questions", [])
        current = session_context.get("current_question", 0)

        if current >= len(questions):
            await self._finish_assessment(update, context)
            return

        question = questions[current]
        keyboard = [
            [InlineKeyboardButton(opt, callback_data=f"answer_{opt[0]}")]
            for opt in question["options"]  # type: ignore
        ]

        try:
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
        except Exception as e:
            if "Message is not modified" not in str(e):
                raise

    async def answer_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle answer to assessment question."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        user_id = update.effective_user.id
        session_context = await self.learning_orchestrator.get_session_context(user_id)
        # context.user_data.update(session_context)  # Removed: using DB session instead

        # Extract answer
        answer = update.callback_query.data.split("_")[1]  # type: ignore
        session_context["assessment_answers"].append(answer)
        session_context["current_question"] += 1

        # Save session context
        await self.learning_orchestrator.save_session_context(user_id, session_context)

        # Show next question
        await self._show_question(update, context)

    async def _finish_assessment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Finish assessment and show goal selection."""
        if not update.effective_user or not update.callback_query:
            return

        user_id = update.effective_user.id
        session_context = await self.learning_orchestrator.get_session_context(user_id)
        # context.user_data.update(session_context)  # Removed: using DB session instead

        # Show loading message while evaluating
        loading_msg = await update.callback_query.message.reply_text(
            self.formatter.get_typing_indicator_message("evaluating"),
            parse_mode="Markdown",
        )

        # Send typing indicator during AI processing
        await update.callback_query.message.chat.send_action(ChatAction.TYPING)

        # Calculate results
        assessment_engine = self.assessment_engine
        answers = session_context.get("assessment_answers", [])
        results = await assessment_engine.evaluate_answers(answers)

        # Store results in session context
        session_context["assessment_results"] = results

        # Save session context
        await self.learning_orchestrator.save_session_context(user_id, session_context)

        # Show goal selection
        keyboard = [
            [InlineKeyboardButton("🎓 Academic", callback_data="goal_academic")],
            [InlineKeyboardButton("💼 Professional", callback_data="goal_professional")],
            [InlineKeyboardButton("🎨 Creative", callback_data="goal_creative")],
        ]

        try:
            await loading_msg.edit_text(
                self.formatter.format_goal_selection(),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                raise

    async def goal_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle goal selection."""
        if not update.effective_user or not update.callback_query:
            logger.warning("Invalid goal callback: missing user or callback")
            return

        await update.callback_query.answer()

        # Extract goal
        goal_map = {
            "goal_academic": LearningGoal.ACADEMIC,
            "goal_professional": LearningGoal.PROFESSIONAL,
            "goal_creative": LearningGoal.CREATIVE,
        }

        goal = goal_map.get(update.callback_query.data, LearningGoal.PROFESSIONAL)  # type: ignore
        user_id = update.effective_user.id
        logger.info("User selected learning goal", user_id=user_id, goal=goal.value)

        # Load session context
        session_context = await self.learning_orchestrator.get_session_context(user_id)
        # context.user_data.update(session_context)  # Removed: using DB session instead

        # Get assessment results from session context
        results = session_context.get("assessment_results", {})
        skill_level_str = results.get("level", "beginner")
        skill_level = SkillLevel(skill_level_str)

        # Create user
        username = update.effective_user.username

        logger.info(
            "Creating new user",
            user_id=user_id,
            username=username,
            skill_level=skill_level.value,
            goal=goal.value,
            assessment_score=results.get("score", 0),
        )

        try:
            await self.learning_orchestrator.user_repo.create(
                telegram_id=user_id,
                username=username,
                skill_level=skill_level,
                learning_goal=goal,
            )
            await self.learning_orchestrator.user_repo.update_assessment_score(
                user_id, results.get("score", 0)
            )  # type: ignore
            logger.info("User created successfully", user_id=user_id)
        except Exception as e:
            logger.error("Failed to create user", user_id=user_id, error=str(e))
            try:
                await update.callback_query.edit_message_text(
                    self.formatter.format_error("Failed to create user profile. Please try again."),
                    parse_mode="Markdown",
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    raise
            return

        # Clear assessment state from session context
        session_context.pop("assessment_questions", None)
        session_context.pop("assessment_answers", None)
        session_context.pop("current_question", None)
        session_context.pop("assessment_results", None)

        # Save session context
        await self.learning_orchestrator.save_session_context(user_id, session_context)

        # Update session state to MENU (ready for learning)
        from promptheus.data.models import SessionState

        await self.learning_orchestrator.update_session_state(
            user_id, SessionState.MENU, session_context
        )

        # Get personalized path
        lessons = await self.learning_orchestrator.get_personalized_path(user_id, skill_level)

        # If no lessons for this level, fallback to beginner lessons
        if not lessons:
            logger.warning(
                f"No lessons found for {skill_level}, falling back to BEGINNER",
                user_id=user_id,
                skill_level=skill_level.value,
            )
            lessons = await self.learning_orchestrator.get_personalized_path(
                user_id, SkillLevel.BEGINNER
            )

        # Show path
        if lessons:
            logger.info("Generated personalized path", user_id=user_id, lesson_count=len(lessons))
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🚀 First Lesson", callback_data=f"lesson_{lessons[0]['id']}"
                    )
                ],
                [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
            ]

            try:
                await update.callback_query.edit_message_text(
                    self.formatter.format_personalized_path(skill_level_str, goal.value, lessons),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    raise
        else:
            # No lessons available at all
            logger.error("No lessons available in database", user_id=user_id)
            await update.callback_query.edit_message_text(
                self.formatter.format_error("No lessons available yet. Please check back later!"),
                parse_mode="Markdown",
            )
