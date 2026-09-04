"""professional identity verification workflow

Revision ID: b2c4d6e8f0a1
Revises: 9f1a2b3c4d5e
Create Date: 2026-09-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c4d6e8f0a1'
down_revision: Union[str, None] = '9f1a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

verification_status = sa.Enum(
    'unsubmitted', 'pending', 'verified', 'rejected', name='verification_status'
)


def upgrade() -> None:
    verification_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'professional_profiles',
        sa.Column(
            'verification_status', verification_status, nullable=False, server_default='unsubmitted'
        ),
    )
    op.add_column('professional_profiles', sa.Column('verification_document_url', sa.String(length=1000), nullable=True))
    op.add_column(
        'professional_profiles', sa.Column('verification_document_object_key', sa.String(length=500), nullable=True)
    )
    op.add_column(
        'professional_profiles', sa.Column('verification_submitted_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'professional_profiles', sa.Column('verification_reviewed_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column('professional_profiles', sa.Column('verification_rejection_reason', sa.Text(), nullable=True))
    op.alter_column('professional_profiles', 'verification_status', server_default=None)

    # Backfill: profiles already flagged is_verified predate this workflow
    # (e.g. seeded data) — reflect that in the new status instead of forcing
    # a resubmission.
    op.execute("UPDATE professional_profiles SET verification_status = 'verified' WHERE is_verified = true")


def downgrade() -> None:
    op.drop_column('professional_profiles', 'verification_rejection_reason')
    op.drop_column('professional_profiles', 'verification_reviewed_at')
    op.drop_column('professional_profiles', 'verification_submitted_at')
    op.drop_column('professional_profiles', 'verification_document_object_key')
    op.drop_column('professional_profiles', 'verification_document_url')
    op.drop_column('professional_profiles', 'verification_status')
    verification_status.drop(op.get_bind(), checkfirst=True)
