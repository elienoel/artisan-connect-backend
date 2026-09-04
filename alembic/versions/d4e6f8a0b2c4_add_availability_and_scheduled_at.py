"""add professional availability and booking scheduled_at

Revision ID: d4e6f8a0b2c4
Revises: c3d5e7f9a1b3
Create Date: 2026-09-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd4e6f8a0b2c4'
down_revision: Union[str, None] = 'c3d5e7f9a1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'availabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'professional_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.UniqueConstraint('professional_id', 'day_of_week', 'start_time', name='uq_availability_professional_slot'),
    )
    op.create_index('ix_availabilities_professional_id', 'availabilities', ['professional_id'])

    op.add_column('bookings', sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('bookings', 'scheduled_at')
    op.drop_index('ix_availabilities_professional_id', table_name='availabilities')
    op.drop_table('availabilities')
