"""chat media messages

Revision ID: 238f1832cf71
Revises: fd25e3deabd2
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '238f1832cf71'
down_revision: Union[str, None] = 'fd25e3deabd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'IMAGE'")
    op.execute("ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'VIDEO'")
    op.execute("ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'AUDIO'")
    op.add_column('messages', sa.Column('media_url', sa.String(length=1000), nullable=True))
    op.add_column('messages', sa.Column('media_mime_type', sa.String(length=100), nullable=True))
    op.add_column('messages', sa.Column('media_duration_seconds', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('messages', 'media_duration_seconds')
    op.drop_column('messages', 'media_mime_type')
    op.drop_column('messages', 'media_url')
    # Postgres does not support removing enum values; downgrade leaves them in place.
