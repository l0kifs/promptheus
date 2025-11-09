"""Progress handlers for Telegram bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from promptheus.data.models import LessonStatus, SkillLevel


class ProgressHandlersMixin:
    """Mixin for progress tracking and statistics."""

    async def continue_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle continue learning callback."""
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

        # Load session context for detailed resume
        session_context = await self.learning_orchestrator.get_session_context(user_id)
        current_lesson_id = session_context.get("current_lesson_id")
        lesson_step = session_context.get("lesson_step")

        if current_lesson_id and lesson_step:
            # Resume based on session context
            lesson = await self.learning_orchestrator.lesson_repo.find_by_id(current_lesson_id)

            if lesson:
                resume_text = f"📖 *Resume Learning*\n\nContinue with:\n**{lesson.title}**\n\n"
                resume_text += f"Current step: {lesson_step.title()}"

                if lesson_step == "theory":
                    theory_chunk = session_context.get("theory_chunk", 0)
                    resume_text += f" (Chunk {theory_chunk + 1})"
                    callback_data = f"lesson_start_{lesson.id}"
                elif lesson_step == "examples":
                    callback_data = f"examples_{lesson.id}"
                elif lesson_step == "practice":
                    callback_data = f"practice_{lesson.id}"
                else:
                    callback_data = f"lesson_{lesson.id}"

                keyboard = [
                    [InlineKeyboardButton("▶️ Resume", callback_data=callback_data)],
                    [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")],
                ]

                await update.callback_query.edit_message_text(
                    resume_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
                return

        # No active session, determine next lesson based on progress
        progress_records = await self.progress_tracker.progress_repo.find_by_user(user_id)

        # Find lesson with IN_PROGRESS status
        in_progress_lesson = None
        for progress in progress_records:
            if progress.status == LessonStatus.IN_PROGRESS:
                in_progress_lesson = await self.learning_orchestrator.lesson_repo.find_by_id(
                    progress.lesson_id
                )
                break

        if in_progress_lesson:
            # Resume in-progress lesson
            keyboard = [
                [InlineKeyboardButton("▶️ Resume", callback_data=f"lesson_{in_progress_lesson.id}")],
                [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")],
            ]

            await update.callback_query.edit_message_text(
                f"📖 *Continue Learning*\n\nResume with:\n{in_progress_lesson.title}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
            return

        # No in-progress lesson, find next NOT_STARTED lesson
        all_lessons = await self.learning_orchestrator.lesson_repo.find_by_skill_level(
            user.skill_level
        )
        completed_or_started_lesson_ids = {p.lesson_id for p in progress_records}

        next_lesson = None
        for lesson in all_lessons:
            if lesson.id not in completed_or_started_lesson_ids:
                next_lesson = lesson
                break

        if next_lesson:
            # Start next available lesson
            keyboard = [
                [InlineKeyboardButton("▶️ Start", callback_data=f"lesson_{next_lesson.id}")],
                [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")],
            ]

            await update.callback_query.edit_message_text(
                f"📖 *Continue Learning*\n\nNext lesson:\n{next_lesson.title}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
            return

        # All lessons completed, show last completed lesson
        completed_lessons = [p for p in progress_records if p.status == LessonStatus.COMPLETED]

        if completed_lessons:
            # Sort by completion date (most recent first) or by lesson position
            completed_lessons.sort(key=lambda p: p.completed_at or p.lesson.position, reverse=True)
            last_completed_progress = completed_lessons[0]
            last_lesson = await self.learning_orchestrator.lesson_repo.find_by_id(
                last_completed_progress.lesson_id
            )

            if last_lesson:
                keyboard = [
                    [InlineKeyboardButton("🔄 Review", callback_data=f"lesson_{last_lesson.id}")],
                    [InlineKeyboardButton("📊 Progress", callback_data="progress")],
                    [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")],
                ]

                await update.callback_query.edit_message_text(
                    f"🎉 *All Lessons Completed!*\n\nLast completed:\n{last_lesson.title}\n\nWant to review or check your progress?",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
                return

        # Fallback: show lesson list
        lessons = await self.learning_orchestrator.lesson_repo.find_by_skill_level(user.skill_level)
        if not lessons:
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
        lesson_list = "\n".join([f"{i + 1}. {lesson.title}" for i, lesson in enumerate(lessons)])

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

    async def progress_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle progress view request."""
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

        # Get progress summary
        summary = await self.progress_tracker.get_progress_summary(user_id)

        # Get detailed progress
        progress_records = await self.progress_tracker.progress_repo.find_by_user(user_id)

        # Format progress text
        progress_text = "📊 *Your Progress*\n\n"
        progress_text += f"🎯 *Skill Level:* {user.skill_level.value.title()}\n"  # type: ignore
        progress_text += f"🎓 *Learning Goal:* {user.learning_goal.value.title()}\n\n"  # type: ignore
        progress_text += f"✅ *Completed Lessons:* {summary['completed']}/{summary['total']}\n"
        progress_text += f"📈 *Average Score:* {summary['average_score']}/10\n\n"

        if progress_records:
            progress_text += "*Recent Activity:*\n"
            # Show last 5 lessons
            for progress in progress_records[-5:]:
                lesson = await self.learning_orchestrator.lesson_repo.find_by_id(progress.lesson_id)  # type: ignore
                if lesson:
                    status_emoji = "✅" if progress.status == LessonStatus.COMPLETED else "📖"  # type: ignore
                    score_text = f" ({progress.last_score}/10)" if progress.last_score else ""  # type: ignore
                    progress_text += f"{status_emoji} {lesson.title}{score_text}\n"

        keyboard = [
            [InlineKeyboardButton("📖 Continue Learning", callback_data="continue")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")],
        ]

        await update.callback_query.edit_message_text(
            progress_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
