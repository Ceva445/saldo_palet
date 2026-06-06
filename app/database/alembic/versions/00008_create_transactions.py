"""Create transactions table

Revision ID: 00008
Revises: 00007
Create Date: 2026-06-06 01:36:24.055268
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "00008"
down_revision: Union[str, None] = "00007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column('type', sa.Enum('RECEIPT', 'ISSUE', 'CORRECTION', name='transactiontype'), nullable=False),
        sa.Column("supplier_uuid", sa.UUID(), nullable=False),
        sa.Column("area_uuid", sa.UUID(), nullable=False),
        sa.Column("unit_uuid", sa.UUID(), nullable=False),
        sa.Column("user_uuid", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("uuid", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["supplier_uuid"], ["suppliers.uuid"]),
        sa.ForeignKeyConstraint(["area_uuid"], ["areas.uuid"]),
        sa.ForeignKeyConstraint(["unit_uuid"], ["units.uuid"]),
        sa.ForeignKeyConstraint(["user_uuid"], ["users.uuid"]),
        sa.PrimaryKeyConstraint("uuid"),
    )

    op.create_index("ix_transactions_uuid", "transactions", ["uuid"])
    op.create_index("ix_transactions_created_at", "transactions", ["created_at"])
    op.create_index("ix_transactions_supplier_uuid", "transactions", ["supplier_uuid"])
    op.create_index("ix_transactions_area_uuid", "transactions", ["area_uuid"])
    op.create_index("ix_transactions_unit_uuid", "transactions", ["unit_uuid"])
    op.create_index("ix_transactions_user_uuid", "transactions", ["user_uuid"])


def downgrade() -> None:
    op.drop_index("ix_transactions_user_uuid", table_name="transactions")
    op.drop_index("ix_transactions_unit_uuid", table_name="transactions")
    op.drop_index("ix_transactions_area_uuid", table_name="transactions")
    op.drop_index("ix_transactions_supplier_uuid", table_name="transactions")
    op.drop_index("ix_transactions_created_at", table_name="transactions")
    op.drop_index("ix_transactions_uuid", table_name="transactions")
    op.drop_table("transactions")