"""Add tenant-owned AI system inventory."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create AI inventory with forced tenant isolation."""
    op.create_table(
        "ai_systems",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner_name", sa.Text(), nullable=False),
        sa.Column("business_purpose", sa.Text(), nullable=False),
        sa.Column("profile", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("deployment_date", sa.Date()),
        sa.Column("next_review_date", sa.Date()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["engagement_id", "org_id"],
            ["engagements.id", "engagements.org_id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'in_review', 'approved', 'deployed', 'suspended', 'retired')"
        ),
        sa.CheckConstraint(
            "deployment_date IS NULL OR next_review_date IS NULL "
            "OR next_review_date >= deployment_date"
        ),
    )
    for statement in (
        "ALTER TABLE ai_systems ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE ai_systems FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON ai_systems USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove the AI system inventory."""
    op.drop_table("ai_systems")
