"""Add versioned AI evaluation definitions, approvals, and runs."""

from alembic import op
import sqlalchemy as sa

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create append-only tenant evaluation registry tables."""
    op.create_table(
        "ai_evaluation_definitions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("ai_system_id", sa.Uuid(), sa.ForeignKey("ai_systems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evaluation_type", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("dataset_name", sa.Text(), nullable=False),
        sa.Column("dataset_version", sa.Text(), nullable=False),
        sa.Column("population_context", sa.Text(), nullable=False),
        sa.Column("metric_name", sa.Text(), nullable=False),
        sa.Column("metric_direction", sa.Text(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("owner_name", sa.Text(), nullable=False),
        sa.Column("cadence", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("ai_system_id", "name", "version"),
        sa.CheckConstraint("evaluation_type IN ('task_performance', 'robustness', 'prompt_injection', 'privacy_leakage', 'groundedness', 'harmful_output', 'contextual_fairness', 'oversight_effectiveness', 'reliability')"),
        sa.CheckConstraint("metric_direction IN ('higher_is_better', 'lower_is_better')"),
    )
    op.create_table(
        "ai_evaluation_threshold_approvals",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("definition_id", sa.Uuid(), sa.ForeignKey("ai_evaluation_definitions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("approved_by", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"),
    )
    op.create_table(
        "ai_evaluation_runs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("ai_system_id", sa.Uuid(), sa.ForeignKey("ai_systems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("definition_id", sa.Uuid(), sa.ForeignKey("ai_evaluation_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("definition_version", sa.Integer(), nullable=False),
        sa.Column("dataset_version", sa.Text(), nullable=False),
        sa.Column("model_version", sa.Text(), nullable=False),
        sa.Column("configuration_version", sa.Text(), nullable=False),
        sa.Column("measured_value", sa.Float(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("run_by", sa.Text(), nullable=False),
        sa.Column("tested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"),
        sa.CheckConstraint("result IN ('pass', 'fail')"),
    )
    for statement in (
        "ALTER TABLE ai_evaluation_definitions ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE ai_evaluation_definitions FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_read ON ai_evaluation_definitions FOR SELECT USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "CREATE POLICY tenant_insert ON ai_evaluation_definitions FOR INSERT WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "ALTER TABLE ai_evaluation_threshold_approvals ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE ai_evaluation_threshold_approvals FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_read ON ai_evaluation_threshold_approvals FOR SELECT USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "CREATE POLICY tenant_insert ON ai_evaluation_threshold_approvals FOR INSERT WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "ALTER TABLE ai_evaluation_runs ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE ai_evaluation_runs FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_read ON ai_evaluation_runs FOR SELECT USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "CREATE POLICY tenant_insert ON ai_evaluation_runs FOR INSERT WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove evaluation runs, approvals, and definitions."""
    op.drop_table("ai_evaluation_runs")
    op.drop_table("ai_evaluation_threshold_approvals")
    op.drop_table("ai_evaluation_definitions")
