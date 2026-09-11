"""Track AI configuration and evaluation drift."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add immutable configuration versions and drift metadata."""
    op.add_column("ai_evaluation_runs", sa.Column("drift", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("ai_governance_decisions", sa.Column("approval_scope", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{model,prompt,corpus,tool_permissions,purpose,vendor_terms,measured_performance}"))
    op.create_table(
        "ai_system_versions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("ai_system_id", sa.Uuid(), sa.ForeignKey("ai_systems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("corpus_version", sa.Text(), nullable=False),
        sa.Column("tool_permissions_version", sa.Text(), nullable=False),
        sa.Column("purpose_version", sa.Text(), nullable=False),
        sa.Column("vendor_terms_version", sa.Text(), nullable=False),
        sa.Column("material_changes", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("ai_system_id", "version"),
    )
    for statement in (
        "ALTER TABLE ai_system_versions ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE ai_system_versions FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_read ON ai_system_versions FOR SELECT USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "CREATE POLICY tenant_insert ON ai_system_versions FOR INSERT WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove configuration and evaluation drift metadata."""
    op.drop_table("ai_system_versions")
    op.drop_column("ai_governance_decisions", "approval_scope")
    op.drop_column("ai_evaluation_runs", "drift")
