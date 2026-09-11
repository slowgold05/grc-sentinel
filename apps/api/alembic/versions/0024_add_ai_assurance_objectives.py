"""Add AI-system assurance objectives."""

from alembic import op
import sqlalchemy as sa

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tenant-isolated objectives linked to one AI system."""
    op.create_table(
        "ai_assurance_objectives",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("ai_system_id", sa.Uuid(), sa.ForeignKey("ai_systems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("framework", sa.Text(), nullable=False),
        sa.Column("source_version", sa.Text(), nullable=False),
        sa.Column("objective_type", sa.Text(), nullable=False),
        sa.Column("basis", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("target_date", sa.Date()),
        sa.Column("selected_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"),
        sa.CheckConstraint("framework IN ('nist_ai_rmf', 'iso_42001', 'singapore_model_ai_governance')"),
        sa.CheckConstraint("objective_type IN ('voluntary', 'certifiable')"),
        sa.CheckConstraint("basis IN ('customer_contract', 'company_strategy', 'regulator_request')"),
        sa.UniqueConstraint("ai_system_id", "framework"),
    )
    for statement in (
        "ALTER TABLE ai_assurance_objectives ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE ai_assurance_objectives FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON ai_assurance_objectives USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove AI assurance objectives."""
    op.drop_table("ai_assurance_objectives")
