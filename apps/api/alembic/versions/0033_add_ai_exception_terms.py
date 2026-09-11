"""Add explicit ownership and compensating controls to AI exceptions."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_governance_decisions", sa.Column("exception_owner", sa.Text()))
    op.add_column(
        "ai_governance_decisions",
        sa.Column(
            "compensating_controls",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("ai_governance_decisions", "compensating_controls")
    op.drop_column("ai_governance_decisions", "exception_owner")
