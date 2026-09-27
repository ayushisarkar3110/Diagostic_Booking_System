"""add foreign key to diagnostic tests

Revision ID: 571d3f8642b3
Revises: 40f5de88d41a
Create Date: 2026-09-27 12:28:55.823869

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '571d3f8642b3'
down_revision: Union[str, Sequence[str], None] = '40f5de88d41a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_foreign_key(
        'fk_diagnostic_tests_centre_id',
        'diagnostic_tests',
        'diagnostic_centres',
        ['centre_id'],
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'fk_diagnostic_tests_centre_id',
        'diagnostic_tests',
        type_='foreignkey'
    )