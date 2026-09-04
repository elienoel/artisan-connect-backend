"""add media_object_key to messages

Revision ID: 9f1a2b3c4d5e
Revises: 238f1832cf71
Create Date: 2026-09-03 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f1a2b3c4d5e'
down_revision: Union[str, None] = '238f1832cf71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Object key in MinIO for chat media, needed to delete the file once it
    # expires (media_url alone is a full public URL, not enough to address
    # the object for deletion without reparsing it).
    op.add_column('messages', sa.Column('media_object_key', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('messages', 'media_object_key')
