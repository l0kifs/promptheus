# Technical Task: Lesson Cache with Hot Reload

## METADATA

**Task ID:** PRMT-204  
**Name:** Implement in-memory lesson cache with hot reload mechanism  
**Created:** 2025-11-09  
**Priority:** Medium  
**Complexity Estimate:** 7/10  
**Estimated Time:** 6-8 hours

---

## BUSINESS CONTEXT

### Problem Description
Currently, lessons are loaded from JSON files only during application startup. Any content updates require a full application restart to take effect, which disrupts service availability and creates friction for content iteration. Content creators need immediate feedback when updating lessons, and the system needs to minimize database queries for frequently accessed content.

### Business Goals
- Enable live content updates without application restart
- Reduce database load by caching lesson content in memory
- Improve response times for lesson retrieval (cache hit vs DB query)
- Support rapid content iteration during development
- Provide mechanism to invalidate cache on content changes

### Target Audience
- **Primary:** Content creators testing and updating lessons
- **Secondary:** Backend developers reducing database load
- **Tertiary:** End users (transparent performance improvement)

### Business Value
- Eliminate downtime for content updates (continuous availability)
- Reduce time-to-feedback for content changes (seconds vs minutes)
- Improve application performance (memory access vs DB query)
- Enable A/B testing and gradual rollouts (swap content without restart)

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
As a system, I want to cache lessons in memory and automatically reload them when JSON files change, so that content updates take effect without application restart.

#### Detailed Requirements

1. **In-Memory Cache**
   - Description: Store validated lesson objects in memory
   - Structure: Nested dict by skill_level and slug
   - Behavior:
     - Load all lessons into cache on startup
     - Serve lesson requests from cache (O(1) lookup)
     - Fallback to database if cache miss
   - Constraints: Thread-safe, supports async access

2. **File System Watcher**
   - Description: Monitor lesson directory for changes
   - Events to watch:
     - File created (new lesson)
     - File modified (content update)
     - File deleted (lesson removed)
     - File renamed (slug change)
   - Behavior:
     - Detect changes within 1 second
     - Debounce rapid changes (e.g., editor saves)
     - Queue reload operations
   - Constraints: Should not miss changes during reload

3. **Hot Reload Mechanism**
   - Description: Reload lessons when files change
   - Behavior:
     - On file modified: Reload single lesson, validate, update cache
     - On file created: Load new lesson, validate, add to cache and DB
     - On file deleted: Remove from cache, mark as archived in DB
     - On reload error: Log error, keep old cached version
   - Constraints: Atomic cache updates (no partial states visible)

4. **Cache Invalidation**
   - Description: Explicit cache clearing mechanism
   - Triggers:
     - Manual API endpoint (admin only)
     - Configuration change (lessons path)
     - Database schema update
   - Behavior:
     - Clear entire cache
     - Reload all lessons from source
     - Log invalidation event
   - Constraints: Safe to call during active requests

5. **Cache Statistics**
   - Description: Track cache performance metrics
   - Metrics:
     - Cache hit rate (hits / total requests)
     - Cache size (number of lessons, memory usage)
     - Reload events (count, last reload time)
     - Errors (validation failures, reload errors)
   - Behavior: Expose via health check endpoint
   - Constraints: Minimal performance overhead (<1ms per request)

### Non-Functional Requirements

#### Performance
- Cache lookup: O(1), <1ms
- File change detection: <1 second latency
- Hot reload: <100ms for single lesson
- Memory usage: <10MB per 100 lessons
- No performance degradation during reload (serve stale cache)

#### Security
- Admin authentication required for manual invalidation
- File system monitoring restricted to configured directory
- No arbitrary file path access

#### Reliability
- Reload errors don't crash application
- Failed reloads keep old cache intact
- Cache corruption detected and auto-repaired
- Graceful degradation (fall back to DB if cache unavailable)

#### Compatibility
- Works with both local filesystem and mounted volumes (Docker)
- Compatible with existing LessonLoaderService
- Async-safe (supports concurrent requests)

---

## TECHNICAL CONTEXT

### System Architecture
```
┌─────────────────────┐
│  Lesson Files       │
│  (Filesystem)       │
└──────────┬──────────┘
           │ watch
           ▼
┌─────────────────────┐      ┌────────────────────┐
│  File Watcher       │─────▶│  Reload Queue      │
│  (watchfiles)       │      │  (asyncio.Queue)   │
└─────────────────────┘      └─────────┬──────────┘
                                       │
                                       ▼
                             ┌─────────────────────┐
                             │  Hot Reload Worker  │
                             │  - validate         │
                             │  - update cache     │
                             └─────────┬───────────┘
                                       │
           ┌───────────────────────────┴──────────────┐
           ▼                                          ▼
┌─────────────────────┐                  ┌─────────────────────┐
│  Lesson Cache       │                  │  Database           │
│  {skill: {slug: L}} │                  │  (sync on reload)   │
└──────────┬──────────┘                  └─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Request Handler    │
│  - get_lesson()     │
│  - cache hit/miss   │
└─────────────────────┘
```

### Technology Stack
- **Backend:** Python 3.11+, asyncio
- **File Watching:** watchfiles (async file system monitor)
- **Caching:** Python dict with asyncio.Lock
- **Queue:** asyncio.Queue for reload coordination
- **Logging:** loguru with structured context

### Project Structure
```
src/promptheus/
├── data/
│   ├── lesson_loader.py         ← Modify: add cache layer
│   ├── lesson_cache.py          ← CREATE: LessonCache class
│   └── file_watcher.py          ← CREATE: FileWatcher service
├── api/
│   └── admin.py                 ← CREATE: cache admin endpoints
└── main.py                      ← Modify: start file watcher

tests/
└── data/
    ├── test_lesson_cache.py     ← CREATE: cache tests
    └── test_file_watcher.py     ← CREATE: watcher tests
```

### Files to Modify

1. **`src/promptheus/data/lesson_cache.py`** (CREATE)
   - Purpose: In-memory cache with thread-safe access
   - Class: `LessonCache`
   - Methods:
     - `get(skill_level, slug) -> Lesson | None`
     - `set(skill_level, slug, lesson) -> None`
     - `delete(skill_level, slug) -> None`
     - `clear() -> None`
     - `get_all(skill_level) -> list[Lesson]`
     - `get_stats() -> dict`
   - Notes: Use asyncio.Lock for thread safety

2. **`src/promptheus/data/file_watcher.py`** (CREATE)
   - Purpose: Monitor lesson directory for changes
   - Class: `FileWatcher`
   - Methods:
     - `start() -> None` (background task)
     - `stop() -> None`
     - `on_change(path, event_type) -> None`
   - Dependencies: watchfiles library
   - Notes: Run as background asyncio task

3. **`src/promptheus/data/lesson_loader.py`** (MODIFY)
   - Purpose: Integrate cache layer
   - Add: Cache dependency injection
   - Modify: `load_lesson()` to update cache
   - Add: `reload_lesson(filepath)` for hot reload
   - Notes: Check cache before DB query

4. **`src/promptheus/api/admin.py`** (CREATE)
   - Purpose: Admin endpoints for cache management
   - Endpoints:
     - `POST /admin/cache/invalidate` - Clear and reload cache
     - `GET /admin/cache/stats` - Cache statistics
   - Security: Require admin authentication
   - Notes: Use FastAPI dependency for auth

5. **`src/promptheus/main.py`** (MODIFY)
   - Purpose: Start file watcher on startup
   - Add: Initialize LessonCache
   - Add: Start FileWatcher background task
   - Add: Graceful shutdown for watcher
   - Notes: Use FastAPI lifespan context

6. **`pyproject.toml`** (MODIFY)
   - Purpose: Add watchfiles dependency
   - Add: `watchfiles>=0.21` to dependencies

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: LessonCache implementation
```python
import asyncio
from typing import Dict, Optional
from loguru import logger
from promptheus.data.models import Lesson, SkillLevel

class LessonCache:
    """Thread-safe in-memory cache for lessons."""
    
    def __init__(self):
        """Initialize cache with nested dict structure."""
        self._cache: Dict[SkillLevel, Dict[str, Lesson]] = {
            SkillLevel.BEGINNER: {},
            SkillLevel.INTERMEDIATE: {},
            SkillLevel.ADVANCED: {},
        }
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "reload_count": 0,
            "last_reload": None,
        }
    
    async def get(
        self, skill_level: SkillLevel, slug: str
    ) -> Optional[Lesson]:
        """Get lesson from cache.
        
        Args:
            skill_level: Skill level
            slug: Lesson slug
            
        Returns:
            Lesson if found, None otherwise
        """
        async with self._lock:
            lesson = self._cache[skill_level].get(slug)
            if lesson:
                self._stats["hits"] += 1
                logger.debug("Cache hit", skill_level=skill_level, slug=slug)
            else:
                self._stats["misses"] += 1
                logger.debug("Cache miss", skill_level=skill_level, slug=slug)
            return lesson
    
    async def set(
        self, skill_level: SkillLevel, slug: str, lesson: Lesson
    ) -> None:
        """Set lesson in cache.
        
        Args:
            skill_level: Skill level
            slug: Lesson slug
            lesson: Lesson object
        """
        async with self._lock:
            self._cache[skill_level][slug] = lesson
            logger.debug("Cache set", skill_level=skill_level, slug=slug)
    
    async def delete(self, skill_level: SkillLevel, slug: str) -> None:
        """Remove lesson from cache."""
        async with self._lock:
            self._cache[skill_level].pop(slug, None)
            logger.info("Cache delete", skill_level=skill_level, slug=slug)
    
    async def clear(self) -> None:
        """Clear entire cache."""
        async with self._lock:
            for level in self._cache:
                self._cache[level].clear()
            logger.info("Cache cleared")
    
    async def get_all(self, skill_level: SkillLevel) -> list[Lesson]:
        """Get all lessons for skill level."""
        async with self._lock:
            return list(self._cache[skill_level].values())
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        async with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total if total > 0 else 0
            )
            return {
                **self._stats,
                "hit_rate": hit_rate,
                "size": sum(len(lessons) for lessons in self._cache.values()),
            }
```

#### Example 2: File watcher with watchfiles
```python
import asyncio
from pathlib import Path
from watchfiles import awatch
from loguru import logger

class FileWatcher:
    """Monitor lesson directory for changes."""
    
    def __init__(
        self,
        lessons_path: Path,
        reload_callback,
    ):
        """Initialize file watcher.
        
        Args:
            lessons_path: Path to lessons directory
            reload_callback: Async function to call on file change
        """
        self.lessons_path = lessons_path
        self.reload_callback = reload_callback
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
    
    async def start(self) -> None:
        """Start watching for file changes."""
        logger.info("Starting file watcher", path=self.lessons_path)
        self._task = asyncio.create_task(self._watch_loop())
    
    async def stop(self) -> None:
        """Stop file watcher gracefully."""
        logger.info("Stopping file watcher")
        self._stop_event.set()
        if self._task:
            await self._task
    
    async def _watch_loop(self) -> None:
        """Main watch loop."""
        try:
            async for changes in awatch(
                self.lessons_path,
                stop_event=self._stop_event,
            ):
                for change_type, path_str in changes:
                    await self._handle_change(change_type, Path(path_str))
        except asyncio.CancelledError:
            logger.info("File watcher cancelled")
        except Exception as e:
            logger.error("File watcher error", error=str(e))
    
    async def _handle_change(
        self, change_type, path: Path
    ) -> None:
        """Handle file system change.
        
        Args:
            change_type: Type of change (added, modified, deleted)
            path: Path to changed file
        """
        # Only watch .json files
        if path.suffix != ".json":
            return
        
        # Extract skill level from parent directory
        skill_level = path.parent.name
        if skill_level not in ["beginner", "intermediate", "advanced"]:
            return
        
        logger.info(
            "File change detected",
            change_type=change_type,
            path=str(path),
            skill_level=skill_level,
        )
        
        # Debounce: wait a bit for editor to finish saving
        await asyncio.sleep(0.1)
        
        # Call reload callback
        try:
            await self.reload_callback(path, change_type, skill_level)
        except Exception as e:
            logger.error(
                "Reload callback failed",
                path=str(path),
                error=str(e),
            )
```

#### Example 3: Hot reload in lesson loader
```python
class LessonLoaderService:
    """Service with cache and hot reload support."""
    
    def __init__(
        self,
        settings,
        lesson_repo,
        cache: LessonCache,
    ):
        """Initialize with cache dependency."""
        self.settings = settings
        self.lesson_repo = lesson_repo
        self.cache = cache
    
    async def get_lesson(
        self, skill_level: SkillLevel, slug: str
    ) -> Lesson | None:
        """Get lesson with cache layer.
        
        Checks cache first, falls back to database.
        """
        # Try cache first
        lesson = await self.cache.get(skill_level, slug)
        if lesson:
            return lesson
        
        # Cache miss - query database
        logger.debug("Cache miss, querying DB", slug=slug)
        lesson = await self.lesson_repo.find_by_slug(skill_level, slug)
        
        # Populate cache for next time
        if lesson:
            await self.cache.set(skill_level, slug, lesson)
        
        return lesson
    
    async def reload_lesson(
        self, filepath: Path, change_type: str, skill_level_str: str
    ) -> None:
        """Hot reload single lesson.
        
        Args:
            filepath: Path to changed JSON file
            change_type: Type of change (added, modified, deleted)
            skill_level_str: Skill level directory name
        """
        logger.info("Reloading lesson", filepath=str(filepath), change_type=change_type)
        
        skill_level = SkillLevel(skill_level_str)
        
        if change_type == "deleted":
            # Remove from cache
            slug = self._filepath_to_slug(filepath)
            await self.cache.delete(skill_level, slug)
            logger.info("Lesson removed from cache", slug=slug)
            return
        
        # Load and validate lesson
        try:
            data = await self.load_lesson_file(filepath)
            lesson_schema = self.validate_lesson(data, filepath)
            slug = lesson_schema.slug
            
            # Upsert to database
            lesson = await self.lesson_repo.upsert_lesson(
                title=lesson_schema.title,
                slug=slug,
                skill_level=skill_level,
                # ... other fields
            )
            
            # Update cache
            await self.cache.set(skill_level, slug, lesson)
            logger.success("Lesson reloaded", slug=slug)
            
        except Exception as e:
            logger.error(
                "Reload failed, keeping old cache",
                filepath=str(filepath),
                error=str(e),
            )
```

#### Example 4: FastAPI integration
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing lesson cache and file watcher")
    
    # Create cache
    cache = LessonCache()
    app.state.lesson_cache = cache
    
    # Load lessons into cache
    loader = LessonLoaderService(settings, lesson_repo, cache)
    await loader.batch_load_all()
    
    # Start file watcher
    watcher = FileWatcher(
        lessons_path=settings.lessons_content_path,
        reload_callback=loader.reload_lesson,
    )
    await watcher.start()
    app.state.file_watcher = watcher
    
    logger.info("Lesson cache and file watcher ready")
    
    yield
    
    # Shutdown
    logger.info("Stopping file watcher")
    await watcher.stop()

app = FastAPI(lifespan=lifespan)
```

### Documentation
- [watchfiles Documentation](https://watchfiles.helpmanual.io/)
- [asyncio Locks](https://docs.python.org/3/library/asyncio-sync.html)
- [FastAPI Lifespan](https://fastapi.tiangulo.com/advanced/events/)
- [Python dict thread safety](https://docs.python.org/3/faq/library.html#what-kinds-of-global-value-mutation-are-thread-safe)

### Existing Patterns
- **Dependency Injection:** Add cache to DependencyContainer
- **Async Patterns:** Use asyncio.Lock, asyncio.Queue
- **Background Tasks:** Follow FastAPI lifespan pattern
- **Logging:** Use loguru with structured context

### Known Pitfalls
⚠️ **Important:**
- **Race conditions:** Use asyncio.Lock for all cache mutations
- **File editor behavior:** Multiple save events in quick succession - use debounce
- **Cache staleness:** Ensure atomic cache updates (no partial state)
- **Memory leaks:** Monitor cache size, implement max size limit if needed
- **Docker volumes:** File watching may not work with some volume types (test thoroughly)

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Cache hit returns lesson without DB query
```gherkin
Given lesson is loaded into cache
And user requests lesson by slug
When get_lesson() is called
Then lesson is returned from cache
And no database query is executed
And cache hit counter is incremented
```

#### Scenario 2: Cache miss falls back to database
```gherkin
Given lesson is not in cache
And lesson exists in database
When get_lesson() is called
Then database is queried
And lesson is added to cache
And cache miss counter is incremented
And subsequent requests hit cache
```

#### Scenario 3: File modification triggers hot reload
```gherkin
Given file watcher is running
And lesson JSON file is modified
When file change is detected (within 1 second)
Then lesson is reloaded and validated
And cache is updated with new content
And database is synced
And reload count is incremented
```

#### Scenario 4: Invalid reload keeps old cache
```gherkin
Given lesson is cached
And lesson JSON file is modified with invalid content
When hot reload is triggered
Then validation fails
And error is logged
And old cached version is retained
And application continues serving stale content
```

#### Scenario 5: Cache invalidation clears all lessons
```gherkin
Given cache contains multiple lessons
When manual cache invalidation is triggered via API
Then cache is cleared
And all lessons are reloaded from filesystem
And cache statistics are reset
And success response is returned
```

#### Scenario 6: File deletion removes from cache
```gherkin
Given lesson is cached
And lesson JSON file is deleted
When file deletion is detected
Then lesson is removed from cache
And deletion is logged
And subsequent requests return None
```

### Rules and Constraints
- [ ] Cache operations are thread-safe (use asyncio.Lock)
- [ ] File changes detected within 1 second
- [ ] Hot reload completes in <100ms for single lesson
- [ ] Failed reloads don't crash application or corrupt cache
- [ ] Cache statistics accessible via health endpoint
- [ ] Memory usage monitored and stays under limit

### Testing
- [ ] All unit tests pass successfully
- [ ] Integration test with file watcher
- [ ] Test coverage >= 85% for cache and watcher
- [ ] Edge cases tested (concurrent access, rapid changes)

### Code Review
- [ ] Code conforms to project style guide (Ruff passes)
- [ ] Type hints on all functions (mypy passes)
- [ ] Docstrings on all public methods
- [ ] Thread safety verified
- [ ] Error handling comprehensive

### Performance
- [ ] Cache lookup <1ms (O(1))
- [ ] Hot reload <100ms per lesson
- [ ] No performance degradation during reload
- [ ] Memory usage <10MB per 100 lessons

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Implement LessonCache class
**Description:** Create thread-safe in-memory cache
**Tasks:**
- [ ] Create `src/promptheus/data/lesson_cache.py`
- [ ] Define `LessonCache` class with nested dict
- [ ] Implement `get()`, `set()`, `delete()`, `clear()` methods
- [ ] Add asyncio.Lock for thread safety
- [ ] Implement cache statistics tracking
- [ ] Add `get_stats()` method
- [ ] Write unit tests for all methods
- [ ] Test concurrent access

**Validation:**
- All cache operations work correctly
- Thread safety verified with concurrent tests

#### Stage 2: Implement FileWatcher service
**Description:** Monitor filesystem for changes
**Tasks:**
- [ ] Add `watchfiles>=0.21` to pyproject.toml
- [ ] Create `src/promptheus/data/file_watcher.py`
- [ ] Define `FileWatcher` class
- [ ] Implement `start()` and `stop()` methods
- [ ] Implement `_watch_loop()` with watchfiles.awatch()
- [ ] Add change type filtering (.json files only)
- [ ] Add debouncing (100ms delay)
- [ ] Add callback mechanism for reload
- [ ] Write unit tests with temporary files

**Validation:**
- File changes detected within 1 second
- Only .json files trigger callbacks
- Debouncing works correctly

#### Stage 3: Integrate cache into LessonLoaderService
**Description:** Add cache layer to loader
**Tasks:**
- [ ] Open `src/promptheus/data/lesson_loader.py`
- [ ] Add `cache: LessonCache` to constructor
- [ ] Implement `get_lesson()` method with cache check
- [ ] Update `batch_load_all()` to populate cache
- [ ] Implement `reload_lesson()` for hot reload
- [ ] Add error handling (keep old cache on failure)
- [ ] Update tests

**Validation:**
- Cache is checked before DB
- Cache is populated after DB query
- Hot reload works correctly

#### Stage 4: Implement hot reload callback
**Description:** Connect file watcher to loader
**Tasks:**
- [ ] Define reload callback in `LessonLoaderService`
- [ ] Handle file added (load new lesson)
- [ ] Handle file modified (reload existing lesson)
- [ ] Handle file deleted (remove from cache)
- [ ] Add atomic cache updates
- [ ] Add comprehensive error logging
- [ ] Test with real file changes

**Validation:**
- All file change types handled
- Errors don't corrupt cache

#### Stage 5: Create admin API endpoints
**Description:** Manual cache management
**Tasks:**
- [ ] Create `src/promptheus/api/admin.py`
- [ ] Define `POST /admin/cache/invalidate` endpoint
- [ ] Define `GET /admin/cache/stats` endpoint
- [ ] Add authentication dependency (admin only)
- [ ] Implement cache clearing logic
- [ ] Return detailed statistics
- [ ] Add to API router in `main.py`
- [ ] Write API tests

**Validation:**
- Endpoints require authentication
- Cache invalidation works
- Statistics are accurate

#### Stage 6: Integrate with application lifecycle
**Description:** Start cache and watcher on startup
**Tasks:**
- [ ] Open `src/promptheus/main.py`
- [ ] Update lifespan context manager
- [ ] Initialize `LessonCache`
- [ ] Initialize `LessonLoaderService` with cache
- [ ] Load all lessons into cache on startup
- [ ] Create and start `FileWatcher`
- [ ] Add graceful shutdown (stop watcher)
- [ ] Add cache to app.state for access
- [ ] Test startup and shutdown

**Validation:**
- Application starts with cache loaded
- File watcher runs in background
- Graceful shutdown works

#### Stage 7: Add cache to DependencyContainer
**Description:** Integrate with DI system
**Tasks:**
- [ ] Open `src/promptheus/core/dependency_container.py`
- [ ] Add `lesson_cache` component
- [ ] Update `LessonLoaderService` instantiation
- [ ] Ensure cache is singleton
- [ ] Update container tests

**Validation:**
- Cache accessible via container
- Singleton pattern maintained

#### Stage 8: Update health check
**Description:** Expose cache stats in health endpoint
**Tasks:**
- [ ] Open `src/promptheus/api/health.py`
- [ ] Add cache statistics to health check
- [ ] Include hit rate, size, reload count
- [ ] Test health endpoint

**Validation:**
- Health check shows cache stats
- Stats are accurate

#### Stage 9: Comprehensive testing
**Description:** Integration and performance tests
**Tasks:**
- [ ] Test cache with real lesson files
- [ ] Test hot reload end-to-end
- [ ] Test concurrent cache access
- [ ] Measure cache performance (lookup time)
- [ ] Measure memory usage
- [ ] Test file watcher in Docker
- [ ] Run full test suite

**Validation:**
- All tests pass
- Performance meets requirements

### Action Order
1. Implement cache (Stage 1)
2. Implement file watcher (Stage 2)
3. Integrate cache into loader (Stage 3)
4. Implement hot reload (Stage 4)
5. Create admin endpoints (Stage 5)
6. Integrate with lifecycle (Stage 6)
7. Add to DI container (Stage 7)
8. Update health check (Stage 8)
9. Comprehensive testing (Stage 9)

### Dependencies
- **Blocks on:** Task PRMT-202 (lesson loader must exist)
- **Optional:** Task PRMT-203 (slug-based lookup simplifies cache keys)
- **Requires:** watchfiles library

---

## TESTING AND VALIDATION

### Unit Tests
```python
import pytest
import asyncio
from promptheus.data.lesson_cache import LessonCache
from promptheus.data.models import SkillLevel, Lesson

@pytest.mark.asyncio
async def test_cache_get_set():
    # Given
    cache = LessonCache()
    lesson = Lesson(id=1, title="Test", slug="test", skill_level=SkillLevel.BEGINNER)
    
    # When
    await cache.set(SkillLevel.BEGINNER, "test", lesson)
    result = await cache.get(SkillLevel.BEGINNER, "test")
    
    # Then
    assert result == lesson

@pytest.mark.asyncio
async def test_cache_miss_returns_none():
    # Given
    cache = LessonCache()
    
    # When
    result = await cache.get(SkillLevel.BEGINNER, "nonexistent")
    
    # Then
    assert result is None

@pytest.mark.asyncio
async def test_cache_delete_removes_lesson():
    # Given
    cache = LessonCache()
    lesson = Lesson(id=1, title="Test", slug="test", skill_level=SkillLevel.BEGINNER)
    await cache.set(SkillLevel.BEGINNER, "test", lesson)
    
    # When
    await cache.delete(SkillLevel.BEGINNER, "test")
    result = await cache.get(SkillLevel.BEGINNER, "test")
    
    # Then
    assert result is None

@pytest.mark.asyncio
async def test_cache_concurrent_access():
    # Given
    cache = LessonCache()
    lesson = Lesson(id=1, title="Test", slug="test", skill_level=SkillLevel.BEGINNER)
    
    # When: Multiple concurrent writes
    await asyncio.gather(*[
        cache.set(SkillLevel.BEGINNER, f"test{i}", lesson)
        for i in range(100)
    ])
    
    # Then: All lessons cached
    stats = await cache.get_stats()
    assert stats["size"] >= 100

@pytest.mark.asyncio
async def test_file_watcher_detects_changes(tmp_path):
    # Given
    changes_detected = []
    
    async def callback(path, change_type, skill_level):
        changes_detected.append((str(path), change_type))
    
    watcher = FileWatcher(tmp_path, callback)
    await watcher.start()
    
    # When: Create and modify file
    test_file = tmp_path / "beginner" / "test.json"
    test_file.parent.mkdir()
    test_file.write_text('{"test": true}')
    await asyncio.sleep(0.5)  # Wait for detection
    
    test_file.write_text('{"test": false}')
    await asyncio.sleep(0.5)
    
    await watcher.stop()
    
    # Then: Changes detected
    assert len(changes_detected) >= 2
```

### Commands to Run
```bash
# Run cache tests
uv run pytest tests/data/test_lesson_cache.py -v

# Run file watcher tests
uv run pytest tests/data/test_file_watcher.py -v

# Run integration tests
uv run pytest tests/integration/test_hot_reload.py -v

# Check coverage
uv run pytest --cov=src/promptheus --cov-report=term

# Test admin endpoints
uv run pytest tests/api/test_admin.py -v

# Start app and test manually
uv run uvicorn promptheus.main:app --reload
```

### Manual Testing Scenarios
1. **Scenario 1: Hot reload during runtime**
   - Steps:
     1. Start application
     2. Request lesson via API, note response time
     3. Modify lesson JSON file
     4. Wait 1-2 seconds
     5. Request same lesson again
   - Expected result: Updated content returned, response time <50ms (cache)

2. **Scenario 2: Cache statistics**
   - Steps:
     1. Start application
     2. Make several lesson requests
     3. Call `GET /health` endpoint
     4. Check cache statistics in response
   - Expected result: Hit rate, size, reload count displayed

3. **Scenario 3: Manual cache invalidation**
   - Steps:
     1. Request lesson (cache hit)
     2. Call `POST /admin/cache/invalidate`
     3. Request lesson again
     4. Check logs for reload
   - Expected result: Cache cleared and reloaded, lesson still accessible

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk 1:** File watcher doesn't work in Docker volumes
  - **Mitigation:** Test with different volume mount types
  - **Mitigation:** Fallback to polling if watching fails
  
- **Risk 2:** Memory usage grows unbounded with many lessons
  - **Mitigation:** Monitor cache size in stats
  - **Mitigation:** Implement max size limit (future enhancement)
  
- **Risk 3:** Concurrent reloads cause race conditions
  - **Mitigation:** Use asyncio.Lock for atomic updates
  - **Mitigation:** Queue reload operations

### Assumptions
- Lesson files are relatively small (<1MB)
- Number of lessons is manageable (<1000)
- File system supports change notifications (not all NFS do)
- Application has sufficient memory for caching

### Limitations
- Cache is per-instance (not shared across multiple app instances)
- File watching may not work with all volume types
- No distributed cache support (Redis) in this task
- No cache expiration policy (assumes content changes are manual)

### Future Improvements
- Distributed cache with Redis for multi-instance deployments
- Cache eviction policy (LRU) for memory management
- Partial cache updates (only changed fields)
- Cache warming on startup (parallel loading)
- Metrics export to Prometheus

### Questions and Unresolved Issues
- [ ] Should cache be shared across multiple app instances?
  - **Decision:** Not in this task, single-instance cache sufficient for MVP
- [ ] What if file watcher fails silently?
  - **Decision:** Log errors, expose watcher status in health check
- [ ] Should we cache lesson content or just metadata?
  - **Decision:** Cache full lesson objects for maximum performance

---

## COMPLETION CHECKLIST

### Development
- [ ] LessonCache implemented with thread safety
- [ ] FileWatcher implemented with watchfiles
- [ ] Hot reload integrated into LessonLoaderService
- [ ] Admin API endpoints created
- [ ] Cache integrated with application lifecycle
- [ ] Cache added to DependencyContainer
- [ ] Health check includes cache statistics
- [ ] watchfiles added to dependencies

### Testing
- [ ] Unit tests for cache operations
- [ ] Unit tests for file watcher
- [ ] Integration test for hot reload
- [ ] Concurrent access tests
- [ ] Performance tests (lookup time, memory)
- [ ] All tests pass
- [ ] Code coverage >= 85%

### Documentation
- [ ] Docstrings on all classes and methods
- [ ] README updated with cache information
- [ ] Admin API documented
- [ ] Cache statistics explained

### Code Quality
- [ ] Ruff reports no errors
- [ ] Mypy reports no errors
- [ ] Thread safety verified
- [ ] Error handling comprehensive
- [ ] Logging provides visibility

### Performance
- [ ] Cache lookup <1ms
- [ ] Hot reload <100ms
- [ ] Memory usage acceptable (<10MB per 100 lessons)
- [ ] No performance degradation during reload

### Finalization
- [ ] Changes committed: `feat(data): add lesson cache with hot reload mechanism`
- [ ] Tested with file modifications in development
- [ ] Docker volume compatibility verified
- [ ] Task marked as "Ready for Review"

---

**Notes:**
- This task significantly improves developer experience during content iteration
- Cache is critical for production performance at scale
- File watching in Docker requires careful testing with different volume types
- Consider distributed cache (Redis) for multi-instance deployments in future
