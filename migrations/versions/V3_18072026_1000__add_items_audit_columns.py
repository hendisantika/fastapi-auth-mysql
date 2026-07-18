"""add items audit columns

Revision ID: 3
Revises: 2
Create Date: 2026-07-18 10:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3"
down_revision: Union[str, None] = "2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "items",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "items",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "items",
        sa.Column("created_by", sa.String(length=50), nullable=False),
    )
    op.add_column(
        "items",
        sa.Column("updated_by", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("items", "updated_by")
    op.drop_column("items", "created_by")
    op.drop_column("items", "updated_at")
    op.drop_column("items", "created_at")
