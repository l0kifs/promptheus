"""Version manager service for lesson content versioning."""

import hashlib
import json
import re
from typing import Any

from loguru import logger

from promptheus.data.models import LessonVersion


class VersionManager:
    """Service for lesson version management."""

    @staticmethod
    def hash_content(content_dict: dict[str, Any]) -> str:
        """Generate SHA-256 hash of lesson content.

        Args:
            content_dict: Dictionary containing lesson content

        Returns:
            SHA-256 hash as hex string
        """
        # Sort keys for deterministic hashing
        content_json = json.dumps(content_dict, sort_keys=True, default=str)
        return hashlib.sha256(content_json.encode()).hexdigest()

    @staticmethod
    def validate_version(version: str) -> bool:
        """Validate that version string follows semver format (X.Y.Z).

        Args:
            version: Version string to validate

        Returns:
            True if valid semver, False otherwise
        """
        # Simple semver validation: X.Y.Z where X,Y,Z are numbers
        pattern = r"^\d+\.\d+\.\d+$"
        return bool(re.match(pattern, version))

    @staticmethod
    def increment_version(current_version: str, bump_type: str = "patch") -> str:
        """Increment version number according to semver.

        Args:
            current_version: Current version string (X.Y.Z)
            bump_type: Type of version bump ('major', 'minor', 'patch')

        Returns:
            New version string

        Raises:
            ValueError: If current_version is invalid or bump_type is unknown
        """
        if not VersionManager.validate_version(current_version):
            raise ValueError(f"Invalid current version: {current_version}")

        parts = current_version.split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(
                f"Unknown bump type: {bump_type}. Must be 'major', 'minor', or 'patch'"
            )

        return f"{major}.{minor}.{patch}"

    def detect_changes(
        self, lesson_id: int, new_content: dict[str, Any], current_hash: str | None = None
    ) -> dict[str, Any] | None:
        """Detect if lesson content has changed.

        Args:
            lesson_id: ID of the lesson
            new_content: New lesson content dictionary
            current_hash: Current content hash (optional, will be looked up if not provided)

        Returns:
            Change info dict if changed, None if no changes
        """
        new_hash = self.hash_content(new_content)

        if current_hash and current_hash == new_hash:
            logger.debug("No content changes detected", lesson_id=lesson_id)
            return None

        logger.info("Content changes detected", lesson_id=lesson_id, new_hash=new_hash[:16])
        return {
            "new_hash": new_hash,
            "content": new_content,
        }

    def compare_versions(self, version1: LessonVersion, version2: LessonVersion) -> dict[str, Any]:
        """Compare two lesson versions and identify differences.

        Args:
            version1: First version to compare
            version2: Second version to compare

        Returns:
            Dictionary containing comparison results
        """
        if version1.lesson_id != version2.lesson_id:
            raise ValueError("Cannot compare versions from different lessons")

        # Parse content snapshots
        content1 = version1.content_snapshot
        content2 = version2.content_snapshot

        # Find changed fields
        changed_fields = []
        for field in ["title", "skill_level", "tags", "theory_content", "examples", "exercises"]:
            if content1.get(field) != content2.get(field):
                changed_fields.append(field)

        # Compare versions semantically
        try:
            version_diff = self._compare_version_strings(version1.version, version2.version)
        except ValueError:
            version_diff = {
                "v1": version1.version,
                "v2": version2.version,
                "is_newer": None,  # Cannot determine
                "bump_type": None,
            }

        return {
            "lesson_id": version1.lesson_id,
            "changed_fields": changed_fields,
            "version_comparison": version_diff,
            "hash_changed": version1.content_hash != version2.content_hash,
            "created_at_diff": {
                "v1": version1.created_at.isoformat() if version1.created_at else None,
                "v2": version2.created_at.isoformat() if version2.created_at else None,
            },
        }

    def _compare_version_strings(self, v1_str: str, v2_str: str) -> dict[str, Any]:
        """Compare two version strings and determine differences."""
        if not (self.validate_version(v1_str) and self.validate_version(v2_str)):
            raise ValueError("Invalid version format")

        v1_parts = [int(x) for x in v1_str.split(".")]
        v2_parts = [int(x) for x in v2_str.split(".")]

        # Determine which is newer
        is_newer = v2_parts > v1_parts

        # Determine bump type
        bump_type = None
        if v2_parts[0] > v1_parts[0]:
            bump_type = "major"
        elif v2_parts[1] > v1_parts[1]:
            bump_type = "minor"
        elif v2_parts[2] > v1_parts[2]:
            bump_type = "patch"

        return {
            "v1": v1_str,
            "v2": v2_str,
            "is_newer": is_newer,
            "bump_type": bump_type,
        }
