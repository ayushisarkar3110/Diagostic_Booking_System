"""make booking payment unique

Revision ID: 2fb19b69432f
Revises: 571d3f8642b3
Create Date: 2026-09-27 12:36:56.400556

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '2fb19b69432f'
down_revision: Union[str, Sequence[str], None] = '571d3f8642b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        'uq_payments_booking_id',
        'payments',
        ['booking_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'uq_payments_booking_id',
        'payments',
        type_='unique'
    )