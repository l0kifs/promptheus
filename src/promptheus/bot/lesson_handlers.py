"""Lesson handlers for Telegram bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from promptheus.data.models import SkillLevel


class LessonHandlersMixin:
    """Mixin for lesson navigation and content."""

    async def lesson_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle lesson selection."""
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

        # Start lesson using progress tracker
        await self.progress_tracker.start_lesson(user_id, lesson_id)

        # Store lesson in session context
        session_context["current_lesson_id"] = lesson_id
        session_context["lesson_step"] = "start"

        # Save session context
        await self.learning_orchestrator.save_session_context(user_id, session_context)

        keyboard = [
            [InlineKeyboardButton("▶️ Start", callback_data=f"lesson_start_{lesson_id}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="lesson_list")],
        ]

        await update.callback_query.edit_message_text(
            self.formatter.format_lesson_start(
                str(lesson.title),
                lesson.order_index,  # type: ignore
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def lesson_list_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle lesson list display."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        user_id = update.effective_user.id

        user = await self.learning_orchestrator.user_repo.find_by_telegram_id(user_id)

        if not user:
            await update.callback_query.edit_message_text(
                self.formatter.format_error("User not found. Please /start again.")
            )
            return

        # Get lessons for user's skill level
        lessons = await self.learning_orchestrator.lesson_repo.find_by_skill_level(user.skill_level)  # type: ignore

        if not lessons:
            # Fallback to beginner lessons
            lessons = await self.learning_orchestrator.lesson_repo.find_by_skill_level(
                SkillLevel.BEGINNER
            )

        if not lessons:
            await update.callback_query.edit_message_text(
                self.formatter.format_error("No lessons available yet."),
                parse_mode="Markdown",
            )
            return

        # Format lesson list
        lesson_list = "\n".join(
            [f"{i + 1}. {str(lesson.title)}" for i, lesson in enumerate(lessons)]
        )

        keyboard = [
            [InlineKeyboardButton(f"▶️ Lesson {i + 1}", callback_data=f"lesson_{lesson.id}")]
            for i, lesson in enumerate(lessons[:5])  # Show first 5
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")])

        await update.callback_query.edit_message_text(
            f"📋 *Available Lessons*\n\n{lesson_list}\n\nChoose a lesson to begin:",
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

        # Get theory content
        theory_content = lesson.theory_content  # type: ignore
        sections = theory_content.get("sections", [])

        if not sections:
            await update.callback_query.edit_message_text(
                self.formatter.format_error("No theory content available")
            )
            return

        # Store current position in session context
        session_context["current_lesson_id"] = lesson_id
        session_context["theory_section"] = 0
        session_context["lesson_step"] = "theory"

        # Save session context
        await self.learning_orchestrator.save_session_context(user_id, session_context)

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

        user_id = update.effective_user.id

        # Load session context
        session_context = await self.learning_orchestrator.get_session_context(user_id)
        # context.user_data.update(session_context)  # Removed: using DB session instead

        # Get current section from session context
        current_section = session_context.get("theory_section", 0)
        next_section = current_section + 1

        lesson = await self.learning_orchestrator.lesson_repo.find_by_id(lesson_id)

        if not lesson:
            await update.callback_query.edit_message_text(
                self.formatter.format_error("Lesson not found")
            )
            return

        theory_content = lesson.theory_content  # type: ignore
        sections = theory_content.get("sections", [])

        if next_section >= len(sections):
            # Move to examples
            session_context["lesson_step"] = "examples"
            # Save session context
            await self.learning_orchestrator.save_session_context(user_id, session_context)
            await self.examples_callback(update, context)
            return

        # Update session context
        session_context["theory_section"] = next_section

        # Save session context
        await self.learning_orchestrator.save_session_context(user_id, session_context)

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
                [
                    InlineKeyboardButton(
                        "Continue to Examples ➡️", callback_data=f"examples_{lesson_id}"
                    )
                ]
            )
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"theory_prev_{lesson_id}")])

        await update.callback_query.edit_message_text(
            f"💡 *Theory* ({next_section + 1}/{total_sections})\n\n{section['content']}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def theory_prev_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle previous theory section button."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        # Extract lesson ID
        lesson_id = int(update.callback_query.data.split("_")[2])  # type: ignore

        user_id = update.effective_user.id

        # Load session context
        session_context = await self.learning_orchestrator.get_session_context(user_id)
        # context.user_data.update(session_context)  # Removed: using DB session instead

        # Get current section from session context
        current_section = session_context.get("theory_section", 0)
        prev_section = current_section - 1

        # Can't go back from first section
        if prev_section < 0:
            # Go back to lesson start
            keyboard = [
                [InlineKeyboardButton("▶️ Start", callback_data=f"lesson_start_{lesson_id}")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")],
            ]

            lesson = await self.learning_orchestrator.lesson_repo.find_by_id(lesson_id)

            if lesson:
                await update.callback_query.edit_message_text(
                    self.formatter.format_lesson_start(
                        str(lesson.title),
                        lesson.order_index,  # type: ignore
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
            return

        lesson = await self.learning_orchestrator.lesson_repo.find_by_id(lesson_id)

        if not lesson:
            await update.callback_query.edit_message_text(
                self.formatter.format_error("Lesson not found")
            )
            return

        theory_content = lesson.theory_content  # type: ignore
        sections = theory_content.get("sections", [])

        if prev_section >= len(sections):
            await update.callback_query.edit_message_text(
                self.formatter.format_error("Invalid section")
            )
            return

        # Update session context
        session_context["theory_section"] = prev_section

        # Save session context
        await self.learning_orchestrator.save_session_context(user_id, session_context)

        # Show previous section
        section = sections[prev_section]
        total_sections = len(sections)

        keyboard = []
        if prev_section < total_sections - 1:
            keyboard.append(
                [InlineKeyboardButton("Next ➡️", callback_data=f"theory_next_{lesson_id}")]
            )
        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "Continue to Examples ➡️", callback_data=f"examples_{lesson_id}"
                    )
                ]
            )

        # Only show back button if not on first section
        if prev_section > 0:
            keyboard.append(
                [InlineKeyboardButton("⬅️ Back", callback_data=f"theory_prev_{lesson_id}")]
            )
        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Lesson Start", callback_data=f"lesson_{lesson_id}"
                    )
                ]
            )

        await update.callback_query.edit_message_text(
            f"💡 *Theory* ({prev_section + 1}/{total_sections})\n\n{section['content']}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def examples_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle examples section."""
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

        await self._show_examples(update, context, lesson_id, lesson)

    async def _show_examples(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        lesson_id: int,
        lesson: object,
    ) -> None:
        """Show examples section."""
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

    async def lesson_complete_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle lesson completion confirmation."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        user_id = update.effective_user.id
        lesson_id = int(update.callback_query.data.split("_")[2])  # type: ignore

        user = await self.learning_orchestrator.user_repo.find_by_telegram_id(user_id)

        if not user:
            await update.callback_query.edit_message_text(
                self.formatter.format_error("User not found")
            )
            return

        current_lesson = await self.learning_orchestrator.lesson_repo.find_by_id(lesson_id)

        if not current_lesson:
            await update.callback_query.edit_message_text(
                self.formatter.format_error("Lesson not found")
            )
            return

        # Get next lesson
        next_lesson = await self.learning_orchestrator.lesson_repo.find_next_lesson(
            current_lesson.skill_level,  # type: ignore
            current_lesson.order_index,  # type: ignore
        )

        if next_lesson:
            keyboard = [
                [InlineKeyboardButton("➡️ Next Lesson", callback_data=f"lesson_{next_lesson.id}")],
                [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
                [InlineKeyboardButton("📊 My Progress", callback_data="progress")],
                [InlineKeyboardButton("📚 Menu", callback_data="menu")],
            ]

            completion_text = "🎉 *Lesson Complete!*\n\n"
            completion_text += f"Great work on completing:\n_{current_lesson.title}_\n\n"
            completion_text += f"*Next up:* {next_lesson.title}"

            await update.callback_query.edit_message_text(
                completion_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        else:
            # No more lessons at this level
            keyboard = [
                [InlineKeyboardButton("📊 View Progress", callback_data="progress")],
                [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
                [InlineKeyboardButton("📚 Menu", callback_data="menu")],
            ]

            completion_text = "🎉 *Congratulations!*\n\n"
            completion_text += f"You've completed:\n_{current_lesson.title}_\n\n"
            completion_text += "🏆 You've finished all lessons in this level!\n"
            completion_text += "Check your progress to see your achievements!"

            await update.callback_query.edit_message_text(
                completion_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
