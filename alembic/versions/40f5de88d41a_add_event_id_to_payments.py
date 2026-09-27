"""add event id to payments

Revision ID: 40f5de88d41a
Revises: 
Create Date: 2026-09-26 22:29:47.434670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40f5de88d41a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add the column temporarily allowing NULL
    op.add_column(
        'payments',
        sa.Column('event_id', sa.String(), nullable=True)
    )

    # Step 2: Give existing payments an event ID
    op.execute(
        "UPDATE payments "
        "SET event_id = 'existing_payment_' || id "
        "WHERE event_id IS NULL"
    )

    # Step 3: Make event_id required
    op.alter_column(
        'payments',
        'event_id',
        existing_type=sa.String(),
        nullable=False
    )

    # Step 4: Make event_id unique
    op.create_unique_constraint(
        'uq_payments_event_id',
        'payments',
        ['event_id']
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_payments_event_id',
        'payments',
        type_='unique'
    )

    op.drop_column(
        'payments',
        'event_id'
    )
