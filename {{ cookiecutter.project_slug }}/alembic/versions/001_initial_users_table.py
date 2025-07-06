"""Initial users table

Revision ID: 001
Revises:
Create Date: 2025-02-06 01:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial users table."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="Telegram user ID"),
        sa.Column("username", sa.String(length=255), nullable=True, comment="Telegram username"),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="en", comment="User's preferred language"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="User registration timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="Last update timestamp",
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_users"),
        comment="User information table",
    )

    # Create index for language-based queries
    op.create_index("idx_users_language", "users", ["language"], unique=False)


def downgrade() -> None:
    """Drop the users table."""
    # Drop index first
    op.drop_index("idx_users_language", table_name="users")

    # Drop table
    op.drop_table("users")
