"""replace order_index with slug and position

Revision ID: 9478c669a66c
Revises: 1a1f52d26e03
Create Date: 2025-11-09 16:55:20.101004

"""

import re
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9478c669a66c"
down_revision: str = "1a1f52d26e03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def generate_slug(title: str, max_length: int = 100) -> str:
    """Generate URL-safe slug from title."""
    if not title:
        return ""

    # Convert to lowercase
    slug = title.lower()

    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[_\s]+", "-", slug)

    # Remove special characters, keeping only alphanumeric and hyphens
    slug = re.sub(r"[^a-z0-9-]", "", slug)

    # Remove consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")

    return slug


def upgrade() -> None:
    # ### Phase 1: Add new columns (nullable for now) ###
    with op.batch_alter_table("lesson", schema=None) as batch_op:
        batch_op.add_column(sa.Column("slug", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("position", sa.Integer(), nullable=True))

    # ### Phase 2: Migrate data ###
    # Get database connection
    conn = op.get_bind()

    # Fetch all lessons
    lessons = conn.execute(sa.text("SELECT id, title, order_index FROM lesson")).fetchall()

    # Generate slugs and positions
    for lesson in lessons:
        slug = generate_slug(lesson.title)
        position = lesson.order_index * 10  # Convert order_index to position

        # Update the lesson with slug and position
        conn.execute(
            sa.text("UPDATE lesson SET slug = :slug, position = :position WHERE id = :id"),
            {"slug": slug, "position": position, "id": lesson.id},
        )

    # ### Phase 3: Make columns non-nullable and add constraints ###
    with op.batch_alter_table("lesson", schema=None) as batch_op:
        batch_op.alter_column("slug", nullable=False)
        batch_op.alter_column("position", nullable=False)
        batch_op.create_unique_constraint("uq_lesson_skill_level_slug", ["skill_level", "slug"])
        batch_op.create_index("ix_lesson_skill_level_slug", ["skill_level", "slug"], unique=False)

    # ### Phase 4: Remove old column and its constraints ###
    with op.batch_alter_table("lesson", schema=None) as batch_op:
        batch_op.drop_constraint("uq_lesson_skill_level_order_index", type_="unique")
        batch_op.drop_index("ix_lesson_skill_level_order_index")
        batch_op.drop_column("order_index")


def downgrade() -> None:
    # ### Phase 1: Add back order_index column (nullable for now) ###
    with op.batch_alter_table("lesson", schema=None) as batch_op:
        batch_op.add_column(sa.Column("order_index", sa.Integer(), nullable=True))

    # ### Phase 2: Migrate data back ###
    # Get database connection
    conn = op.get_bind()

    # Fetch all lessons
    lessons = conn.execute(sa.text("SELECT id, position FROM lesson")).fetchall()

    # Convert position back to order_index
    for lesson in lessons:
        order_index = lesson.position // 10  # Convert position back to order_index

        # Update the lesson with order_index
        conn.execute(
            sa.text("UPDATE lesson SET order_index = :order_index WHERE id = :id"),
            {"order_index": order_index, "id": lesson.id},
        )

    # ### Phase 3: Make order_index non-nullable and add constraints ###
    with op.batch_alter_table("lesson", schema=None) as batch_op:
        batch_op.alter_column("order_index", nullable=False)
        batch_op.create_unique_constraint(
            "uq_lesson_skill_level_order_index", ["skill_level", "order_index"]
        )
        batch_op.create_index(
            "ix_lesson_skill_level_order_index", ["skill_level", "order_index"], unique=False
        )

    # ### Phase 4: Remove new columns ###
    with op.batch_alter_table("lesson", schema=None) as batch_op:
        batch_op.drop_constraint("uq_lesson_skill_level_slug", type_="unique")
        batch_op.drop_index("ix_lesson_skill_level_slug")
        batch_op.drop_column("slug")
        batch_op.drop_column("position")
