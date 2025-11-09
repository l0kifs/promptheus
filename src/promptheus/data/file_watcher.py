"""File system watcher service for monitoring lesson content changes."""

import asyncio
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

from loguru import logger
from watchfiles import Change, awatch

from promptheus.config import get_settings


class FileWatcher:
    """Monitor lesson directory for file changes and trigger reloads.

    Uses watchfiles library for efficient async file system monitoring.
    Implements debouncing to handle rapid file changes.
    """

    def __init__(
        self,
        settings: Any = None,
        reload_callback: Callable[[set[Path]], Any] | None = None,
        debounce_seconds: float = 0.1,
    ) -> None:
        """Initialize file watcher.

        Args:
            settings: Application settings (uses get_settings() if not provided)
            reload_callback: Function to call when files change
            debounce_seconds: Debounce delay for rapid changes
        """
        self.settings = settings or get_settings()
        self.reload_callback = reload_callback
        self.debounce_seconds = debounce_seconds

        self._watch_task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._debounce_timer: asyncio.Task[None] | None = None

        logger.debug("FileWatcher initialized", debounce_seconds=debounce_seconds)

    async def start(self) -> None:
        """Start watching lesson directory for changes."""
        if self._watch_task is not None:
            logger.warning("FileWatcher already started")
            return

        self._stop_event.clear()
        self._watch_task = asyncio.create_task(self._watch_loop())

        logger.info(
            "FileWatcher started",
            watch_path=self.settings.lessons_content_path,
            debounce_seconds=self.debounce_seconds,
        )

    async def stop(self) -> None:
        """Stop watching and cleanup resources."""
        if self._watch_task is None:
            logger.debug("FileWatcher not running")
            return

        logger.info("Stopping FileWatcher")

        # Signal stop
        self._stop_event.set()

        # Cancel debounce timer if active
        if self._debounce_timer and not self._debounce_timer.done():
            self._debounce_timer.cancel()
            with suppress(asyncio.CancelledError):
                await self._debounce_timer

        # Cancel watch task
        self._watch_task.cancel()
        with suppress(asyncio.CancelledError):
            await self._watch_task

        self._watch_task = None
        self._debounce_timer = None

        logger.info("FileWatcher stopped")

    async def _watch_loop(self) -> None:
        """Main watch loop using watchfiles.awatch."""
        try:
            async for changes in awatch(
                self.settings.lessons_content_path,
                stop_event=self._stop_event,
                watch_filter=self._is_lesson_file,
            ):
                await self._handle_changes(changes)

        except asyncio.CancelledError:
            logger.debug("Watch loop cancelled")
            raise
        except Exception as e:
            logger.error("Error in watch loop", error=str(e), error_type=type(e).__name__)
            raise

    def _is_lesson_file(self, change: Change, path: str) -> bool:
        """Filter to only watch JSON files in lesson directories.

        Args:
            change: Type of file system change
            path: Path to the changed file

        Returns:
            True if this is a lesson JSON file to watch
        """
        try:
            file_path = Path(path)

            # Only watch JSON files
            if file_path.suffix != ".json":
                return False

            # Only watch files in skill level directories
            if file_path.parent.name not in ["beginner", "intermediate", "advanced"]:
                return False

            # Ensure it's directly in a skill level directory
            return file_path.parent.parent == self.settings.lessons_content_path

        except Exception as e:
            logger.debug("Error filtering file change", path=path, error=str(e))
            return False

    async def _handle_changes(self, changes: set[tuple[Change, str]]) -> None:
        """Handle file system changes with debouncing.

        Args:
            changes: Set of (Change, path) tuples from watchfiles
        """
        # Filter changes to only lesson files
        lesson_changes = set()
        for change, path_str in changes:
            if self._is_lesson_file(change, path_str):
                lesson_changes.add((change, path_str))

        if not lesson_changes:
            return

        # Log changes
        change_counts = {}
        changed_paths = set()
        for change, path_str in lesson_changes:
            change_counts[change] = change_counts.get(change, 0) + 1
            changed_paths.add(Path(path_str))

        logger.info(
            "Lesson file changes detected",
            changes=change_counts,
            files=len(changed_paths),
            paths=[str(p) for p in changed_paths],
        )

        # Cancel existing debounce timer
        if self._debounce_timer and not self._debounce_timer.done():
            self._debounce_timer.cancel()

        # Start new debounce timer
        self._debounce_timer = asyncio.create_task(self._debounce_reload(changed_paths))

    async def _debounce_reload(self, changed_paths: set[Path]) -> None:
        """Debounce reload callback to handle rapid changes.

        Args:
            changed_paths: Set of changed file paths
        """
        try:
            await asyncio.sleep(self.debounce_seconds)

            if self.reload_callback:
                logger.debug("Triggering reload callback", files=len(changed_paths))
                result = self.reload_callback(changed_paths)
                # Handle both sync and async callbacks
                if asyncio.iscoroutine(result):
                    await result
            else:
                logger.warning("No reload callback configured")

        except asyncio.CancelledError:
            logger.debug("Debounce reload cancelled")
            raise
        except Exception as e:
            logger.error(
                "Error in debounced reload",
                error=str(e),
                error_type=type(e).__name__,
                files=len(changed_paths),
            )

    def set_reload_callback(self, callback: Callable[[set[Path]], Any]) -> None:
        """Set or update the reload callback function.

        Args:
            callback: Function to call when files change
        """
        self.reload_callback = callback
        logger.debug("Reload callback updated")

    async def is_running(self) -> bool:
        """Check if the file watcher is currently running.

        Returns:
            True if watcher is active
        """
        return self._watch_task is not None and not self._watch_task.done()
