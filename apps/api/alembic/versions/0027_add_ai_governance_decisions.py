"""Add append-only AI governance decisions."""

from alembic import op
import sqlalchemy as sa

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tenant-isolated decisions with insert/read-only RLS."""
    op.create_table(
        "ai_governance_decisions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("ai_system_id", sa.Uuid(), sa.ForeignKey("ai_systems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision_type", sa.Text(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("assessment_version_id", sa.Uuid(), sa.ForeignKey("ai_impact_assessment_versions.id"), nullable=True),
        sa.Column("supersedes_id", sa.Uuid(), sa.ForeignKey("ai_governance_decisions.id"), nullable=True),
        sa.Column("decided_by", sa.Text(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"),
        sa.CheckConstraint("decision_type IN ('assessment', 'deployment', 'material_change', 'exception', 'retirement')"),
        sa.CheckConstraint("outcome IN ('approved', 'rejected', 'conditional')"),
        sa.CheckConstraint("expires_at IS NULL OR expires_at > decided_at"),
    )
    op.create_index("ix_ai_governance_decision_history", "ai_governance_decisions", ["ai_system_id", "decision_type", "decided_at"])
    for statement in (
        "ALTER TABLE ai_governance_decisions ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE ai_governance_decisions FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_read ON ai_governance_decisions FOR SELECT USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "CREATE POLICY tenant_insert ON ai_governance_decisions FOR INSERT WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove AI governance decision history."""
    op.drop_table("ai_governance_decisions")
