"""Add sentiment column to Call"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_sentiment"
down_revision = "0001_add_call_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("calls", sa.Column("sentiment", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("calls", "sentiment")
