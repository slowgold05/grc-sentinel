"""Add mutable AI impact drafts and immutable submitted versions."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tenant-isolated impact assessment storage."""
    op.create_table(
        "ai_impact_assessment_drafts",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("ai_system_id", sa.Uuid(), sa.ForeignKey("ai_systems.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"),
    )
    op.create_table(
        "ai_impact_assessment_versions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("ai_system_id", sa.Uuid(), sa.ForeignKey("ai_systems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("missing_facts", postgresql.JSONB(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("reviewer", sa.Text()),
        sa.Column("source_versions", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("ai_system_id", "version"),
        sa.CheckConstraint("status IN ('complete', 'needs_review')"),
    )
    for statement in (
        "ALTER TABLE ai_impact_assessment_drafts ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE ai_impact_assessment_drafts FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON ai_impact_assessment_drafts USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "ALTER TABLE ai_impact_assessment_versions ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE ai_impact_assessment_versions FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON ai_impact_assessment_versions USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove impact assessment versions and drafts."""
    op.drop_table("ai_impact_assessment_versions")
    op.drop_table("ai_impact_assessment_drafts")
