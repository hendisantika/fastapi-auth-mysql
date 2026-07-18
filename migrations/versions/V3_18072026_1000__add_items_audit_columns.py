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
        sa.Column("created_by", sa.Integer(), nullable=False),
    )
    op.add_column(
        "items",
        sa.Column("updated_by", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_items_created_by_users",
        "items",
        "users",
        ["created_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_items_updated_by_users",
        "items",
        "users",
        ["updated_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_items_updated_by_users", "items", type_="foreignkey")
    op.drop_constraint("fk_items_created_by_users", "items", type_="foreignkey")
    op.drop_column("items", "updated_by")
    op.drop_column("items", "created_by")
    op.drop_column("items", "updated_at")
    op.drop_column("items", "created_at")
