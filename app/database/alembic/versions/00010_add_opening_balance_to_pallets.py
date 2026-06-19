"""Add opening_balance to pallets

Revision ID: 00010
Revises: 00009
Create Date: 2026-06-10 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "00010"
down_revision: Union[str, None] = "00009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pallets",
        sa.Column("opening_balance", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("pallets", "opening_balance")
