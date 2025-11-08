"""Practice handlers for Telegram bot."""

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes


class PracticeHandlersMixin:
    """Mixin for practice exercises and user prompts."""

    async def practice_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle practice section."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        # Extract lesson ID
        lesson_id = int(update.callback_query.data.split("_")[1])  # type: ignore

        user_id = update.effective_user.id

        # Load session context
        session_context = await self.learning_orchestrator.get_session_context(user_id)
        # context.user_data.update(session_context)  # Removed: using DB session instead

        lesson = await self.learning_orchestrator.lesson_repo.find_by_id(lesson_id)

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

        # Store in session context for later submission
        session_context["current_lesson_id"] = lesson_id
        session_context["lesson_step"] = "practice"

        # Save session context
        await self.learning_orchestrator.save_session_context(user_id, session_context)

        keyboard = [
            [InlineKeyboardButton("💡 Show Hint", callback_data=f"hint_{lesson_id}")],
            [InlineKeyboardButton("⏭️ Skip Exercise", callback_data=f"skip_{lesson_id}")],
            [InlineKeyboardButton("⬅️ Back to Examples", callback_data=f"examples_{lesson_id}")],
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

    async def hint_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle hint request during practice."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        # Extract lesson ID
        lesson_id = int(update.callback_query.data.split("_")[1])  # type: ignore

        lesson = await self.learning_orchestrator.lesson_repo.find_by_id(lesson_id)

        if not lesson:
            await update.callback_query.edit_message_text(
                self.formatter.format_error("Lesson not found")
            )
            return

        # Get hint from examples
        examples = lesson.examples  # type: ignore
        comparisons = examples.get("comparisons", [])

        hint_text = "💡 *Hint*\n\n"
        if comparisons:
            first_example = comparisons[0]
            hint_text += f"*Good Example:*\n_{first_example['good']}_\n\n"
            hint_text += f"*Why it works:*\n{first_example['good_reason']}\n\n"
            hint_text += "Now try writing your own prompt based on this example!"
        else:
            hint_text += "Think about the lesson concepts and apply them to the scenario.\n\n"
            hint_text += (
                "Remember: Be specific, provide context, and structure your prompt clearly."
            )

        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Exercise", callback_data=f"practice_{lesson_id}")],
            [InlineKeyboardButton("📚 Back to Menu", callback_data="menu")],
        ]

        await update.callback_query.edit_message_text(
            hint_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def skip_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle skip exercise request - allows user to skip without marking lesson complete."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        user_id = update.effective_user.id
        lesson_id = int(update.callback_query.data.split("_")[1])  # type: ignore

        logger.info("User skipping exercise", user_id=user_id, lesson_id=lesson_id)

        # Get user and lesson using async repositories
        user = await self.learning_orchestrator.user_repo.find_by_telegram_id(user_id)

        if not user:
            await update.callback_query.edit_message_text(
                self.formatter.format_error("User not found")
            )
            return

        current_lesson = await self.learning_orchestrator.lesson_repo.find_by_id(lesson_id)

        if current_lesson:
            next_lesson = await self.learning_orchestrator.lesson_repo.find_next_lesson(
                current_lesson.skill_level,  # type: ignore
                current_lesson.order_index,  # type: ignore
            )

            if next_lesson:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "➡️ Next Lesson", callback_data=f"lesson_{next_lesson.id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Try Exercise Again", callback_data=f"practice_{lesson_id}"
                        )
                    ],
                    [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
                    [InlineKeyboardButton("📚 Menu", callback_data="menu")],
                ]

                await update.callback_query.edit_message_text(
                    f"⏭️ *Exercise Skipped*\n\nYou can practice this later!\n\nThe lesson is NOT marked as complete.\n\n*Next available:* {next_lesson.title}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
            else:
                # No more lessons
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🔄 Try Exercise Again", callback_data=f"practice_{lesson_id}"
                        )
                    ],
                    [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
                    [InlineKeyboardButton("📊 View Progress", callback_data="progress")],
                    [InlineKeyboardButton("📚 Menu", callback_data="menu")],
                ]

                await update.callback_query.edit_message_text(
                    "⏭️ *Exercise Skipped*\n\nYou can practice this later!\n\nThe lesson is NOT marked as complete.\n\nYou can try the exercise again or explore other lessons.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
        else:
            keyboard = [
                [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
                [InlineKeyboardButton("📚 Menu", callback_data="menu")],
            ]
            await update.callback_query.edit_message_text(
                "⏭️ *Exercise Skipped*\n\nThe lesson is NOT marked as complete.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    async def text_message_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle text messages (user prompt submissions during practice)."""
        if not update.effective_user or not update.message or not update.message.text:
            logger.warning("Invalid text message: missing user, message, or text")
            return

        user_id = update.effective_user.id
        user_prompt = update.message.text

        logger.info(
            "Received text message",
            user_id=user_id,
            prompt_length=len(user_prompt),
        )

        # Load session context
        session_context = await self.learning_orchestrator.get_session_context(user_id)
        # context.user_data.update(session_context)  # Removed: using DB session instead

        # Check if user is in practice mode
        lesson_step = session_context.get("lesson_step")

        if lesson_step != "practice":
            # User is not in practice mode, send a helpful message
            logger.debug("User not in practice mode", user_id=user_id, lesson_step=lesson_step)
            await update.message.reply_text(
                "👋 Use /menu to navigate or /start to begin learning!",
                parse_mode="Markdown",
            )
            return

        # Get current lesson
        lesson_id = session_context.get("current_lesson_id")

        if not lesson_id:
            logger.warning("User in practice mode but no lesson_id", user_id=user_id)
            await update.message.reply_text(
                "⚠️ Please start a lesson first using /menu",
                parse_mode="Markdown",
            )
            return

        logger.info(
            "Evaluating user prompt",
            user_id=user_id,
            lesson_id=lesson_id,
        )

        # Show loading message
        loading_msg = await update.message.reply_text(
            "⏳ Analyzing your prompt...",
            parse_mode="Markdown",
        )

        # Send typing indicator during AI processing
        await update.message.chat.send_action(ChatAction.TYPING)

        try:
            # Get AI feedback
            assessment_engine = self.assessment_engine
            feedback = await assessment_engine.evaluate_user_prompt(user_prompt, lesson_id)

            logger.info(
                "Prompt evaluation complete",
                user_id=user_id,
                lesson_id=lesson_id,
                score=feedback.get("score", 0),
            )

            # Update progress using async progress tracker
            await self.progress_tracker.increment_attempts(user_id, lesson_id)

            # Parse score safely - it should be an int, but handle edge cases
            score_value = feedback.get("score", 0)
            if isinstance(score_value, int):
                score = score_value
            elif isinstance(score_value, str) and score_value.isdigit():
                score = int(score_value)
            else:
                score = 0

            # ALWAYS record the score, regardless of value (FIX: scores below 7 were not being saved)
            await self.progress_tracker.record_attempt(user_id, lesson_id, score)
            logger.info("Score recorded", user_id=user_id, lesson_id=lesson_id, score=score)

            # If score is good enough, ALSO mark as completed
            if score >= 7:
                await self.progress_tracker.complete_lesson(user_id, lesson_id, score)
                logger.info(
                    "Lesson completed",
                    user_id=user_id,
                    lesson_id=lesson_id,
                    score=score,
                )

            # Format and send feedback
            feedback_text = "📝 *Your Prompt:*\n"
            feedback_text += f"_{user_prompt}_\n\n"
            feedback_text += f"🔍 *Score:* {score}/10\n\n"

            strengths = feedback.get("strengths", [])
            if strengths and isinstance(strengths, list):
                feedback_text += "✅ *Strengths:*\n"
                for strength in strengths:
                    feedback_text += f"• {strength}\n"
                feedback_text += "\n"

            improvements = feedback.get("improvements", [])
            if improvements and isinstance(improvements, list):
                feedback_text += "💡 *Suggestions for Improvement:*\n"
                for improvement in improvements:
                    feedback_text += f"• {improvement}\n"

            keyboard = []
            if score >= 7:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            "🎉 Lesson Complete!", callback_data=f"lesson_complete_{lesson_id}"
                        )
                    ]
                )
            else:
                keyboard.append(
                    [InlineKeyboardButton("🔄 Try Again", callback_data=f"practice_{lesson_id}")]
                )
            keyboard.append(
                [InlineKeyboardButton("⬅️ Back to Examples", callback_data=f"examples_{lesson_id}")]
            )

            # Edit loading message with feedback
            await loading_msg.edit_text(
                feedback_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(
                "Error evaluating prompt",
                user_id=user_id,
                lesson_id=lesson_id,
                error=str(e),
            )
            await loading_msg.edit_text(
                "❌ Sorry, there was an error evaluating your prompt. Please try again.",
                parse_mode="Markdown",
            )
