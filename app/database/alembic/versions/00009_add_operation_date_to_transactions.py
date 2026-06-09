"""Add operation_date to transactions

Revision ID: 00009
Revises: 00008
Create Date: 2026-06-09 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "00009"
down_revision: Union[str, None] = "00008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User-selected operation date. Existing rows backfilled with CURRENT_DATE.
    op.add_column(
        "transactions",
        sa.Column(
            "operation_date",
            sa.Date(),
            server_default=sa.text("CURRENT_DATE"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("transactions", "operation_date")
