"""Add indexes on Call.created_at and Call.from_number

Revision ID: 0001_add_call_indexes
Revises:
Create Date: 2025-07-07
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_add_call_indexes"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_calls_created_at", "calls", ["created_at"])
    op.create_index("ix_calls_from_number", "calls", ["from_number"])


def downgrade() -> None:
    op.drop_index("ix_calls_from_number", table_name="calls")
    op.drop_index("ix_calls_created_at", table_name="calls")
