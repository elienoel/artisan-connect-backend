"""add booking_id to reviews

Revision ID: a1b2c3d4e5f6
Revises: 8d7512570390
Create Date: 2026-09-02 06:20:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "8d7512570390"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add booking_id column (nullable so existing reviews are not broken)
    op.add_column(
        "reviews",
        sa.Column(
            "booking_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_review_booking_id",
        "reviews",
        "bookings",
        ["booking_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Unique constraint: one review per booking
    op.create_unique_constraint("uq_review_booking", "reviews", ["booking_id"])


def downgrade() -> None:
    op.drop_constraint("uq_review_booking", "reviews", type_="unique")
    op.drop_constraint("fk_review_booking_id", "reviews", type_="foreignkey")
    op.drop_column("reviews", "booking_id")

