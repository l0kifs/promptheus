# Alembic script template

"""add lesson version table

Revision ID: 5d377f4167a9
Revises: 9478c669a66c
Create Date: 2025-11-09 17:25:39.845070

"""

import hashlib
import json
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5d377f4167a9"
down_revision: str | None = "9478c669a66c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def hash_content(content_dict: dict) -> str:
    """Generate SHA-256 hash of lesson content."""
    content_json = json.dumps(content_dict, sort_keys=True, default=str)
    return hashlib.sha256(content_json.encode()).hexdigest()


def upgrade() -> None:
    # ### Phase 1: Create lesson_version table ###
    op.create_table(
        "lesson_version",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("content_snapshot", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lesson.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lesson_id", "version", name="uq_lesson_version_lesson_version"),
    )

    # ### Phase 2: Create indexes ###
    op.create_index(
        "ix_lesson_version_lesson_id_is_active",
        "lesson_version",
        ["lesson_id", "is_active"],
        unique=False,
    )
    op.create_index("ix_lesson_version_created_at", "lesson_version", ["created_at"], unique=False)

    # ### Phase 3: Migrate existing lessons to version "1.0.0" ###
    # Get database connection
    conn = op.get_bind()

    # Fetch all existing lessons
    lessons = conn.execute(
        sa.text("""
        SELECT id, title, skill_level, slug, position, tags,
               theory_content, examples, exercises
        FROM lesson
    """)
    ).fetchall()

    # Create version "1.0.0" for each existing lesson
    for lesson in lessons:
        # Build content snapshot
        content_snapshot = {
            "title": lesson.title,
            "skill_level": lesson.skill_level,
            "slug": lesson.slug,
            "position": lesson.position,
            "tags": lesson.tags,
            "theory_content": lesson.theory_content,
            "examples": lesson.examples,
            "exercises": lesson.exercises,
        }

        # Generate content hash
        content_hash = hash_content(content_snapshot)

        # Insert version record
        conn.execute(
            sa.text("""
            INSERT INTO lesson_version
            (lesson_id, version, content_hash, content_snapshot, is_active, created_by)
            VALUES (:lesson_id, :version, :content_hash, :content_snapshot, :is_active, :created_by)
        """),
            {
                "lesson_id": lesson.id,
                "version": "1.0.0",
                "content_hash": content_hash,
                "content_snapshot": json.dumps(content_snapshot),
                "is_active": True,  # Mark as active since it's the current version
                "created_by": "migration",
            },
        )

    # ### Phase 4: Add versions relationship to lesson table (if needed) ###
    # Note: SQLAlchemy relationships don't require database schema changes


def downgrade() -> None:
    # ### Phase 1: Remove all version records ###
    # Delete all version records first (due to foreign key constraint)
    op.execute(sa.text("DELETE FROM lesson_version"))

    # ### Phase 2: Drop indexes ###
    op.drop_index("ix_lesson_version_created_at", table_name="lesson_version")
    op.drop_index("ix_lesson_version_lesson_id_is_active", table_name="lesson_version")

    # ### Phase 3: Drop table ###
    op.drop_table("lesson_version")
