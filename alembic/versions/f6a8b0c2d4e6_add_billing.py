"""add subscription/boost fields and payments table

Revision ID: f6a8b0c2d4e6
Revises: e5f7a9b1c3d5
Create Date: 2026-09-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f6a8b0c2d4e6'
down_revision: Union[str, None] = 'e5f7a9b1c3d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

subscription_plan = sa.Enum('free', 'premium', name='subscription_plan')
payment_purpose = sa.Enum('subscription', 'boost', name='payment_purpose')
payment_status = sa.Enum('pending', 'succeeded', 'failed', name='payment_status')


def upgrade() -> None:
    subscription_plan.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'professional_profiles',
        sa.Column('subscription_plan', subscription_plan, nullable=False, server_default='free'),
    )
    op.alter_column('professional_profiles', 'subscription_plan', server_default=None)
    op.add_column(
        'professional_profiles', sa.Column('subscription_expires_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'professional_profiles', sa.Column('is_boosted', sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.alter_column('professional_profiles', 'is_boosted', server_default=None)
    op.add_column('professional_profiles', sa.Column('boosted_until', sa.DateTime(timezone=True), nullable=True))

    # payment_purpose/payment_status are intentionally NOT pre-created here:
    # op.create_table() below auto-issues CREATE TYPE for enum columns it
    # contains, so doing it again first would raise DuplicateObject in the
    # same transaction (see e5f7a9b1c3d5 for the same gotcha). subscription_plan
    # above is different: it's used with op.add_column(), which does not
    # auto-create the type, so it still needs the explicit .create() call.
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'professional_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('purpose', payment_purpose, nullable=False),
        sa.Column('status', payment_status, nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='FCFA'),
        sa.Column('provider', sa.String(length=50), server_default='simulated'),
        sa.Column('provider_reference', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_payments_professional_id', 'payments', ['professional_id'])


def downgrade() -> None:
    op.drop_index('ix_payments_professional_id', table_name='payments')
    op.drop_table('payments')
    payment_status.drop(op.get_bind(), checkfirst=True)
    payment_purpose.drop(op.get_bind(), checkfirst=True)

    op.drop_column('professional_profiles', 'boosted_until')
    op.drop_column('professional_profiles', 'is_boosted')
    op.drop_column('professional_profiles', 'subscription_expires_at')
    op.drop_column('professional_profiles', 'subscription_plan')
    subscription_plan.drop(op.get_bind(), checkfirst=True)
