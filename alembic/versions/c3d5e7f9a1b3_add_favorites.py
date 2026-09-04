"""add favorites

Revision ID: c3d5e7f9a1b3
Revises: b2c4d6e8f0a1
Create Date: 2026-09-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3d5e7f9a1b3'
down_revision: Union[str, None] = 'b2c4d6e8f0a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'favorites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column(
            'professional_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('client_id', 'professional_id', name='uq_favorite_client_professional'),
    )
    op.create_index('ix_favorites_client_id', 'favorites', ['client_id'])


def downgrade() -> None:
    op.drop_index('ix_favorites_client_id', table_name='favorites')
    op.drop_table('favorites')
