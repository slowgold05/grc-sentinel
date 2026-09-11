"""Optionally link existing risks to AI systems."""

from alembic import op
import sqlalchemy as sa

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add a nullable, history-preserving AI-system link."""
    op.add_column("risks", sa.Column("ai_system_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_risks_ai_system", "risks", "ai_systems", ["ai_system_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    """Remove the optional AI-system link."""
    op.drop_constraint("fk_risks_ai_system", "risks", type_="foreignkey")
    op.drop_column("risks", "ai_system_id")
