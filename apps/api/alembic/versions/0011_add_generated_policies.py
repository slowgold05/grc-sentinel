"""Persist generated policies, statements, and model usage."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the tenant-scoped generation audit trail."""
    op.create_table(
        "policies",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("policy_type", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("id", "org_id"),
        sa.CheckConstraint("version >= 1"),
    )
    op.create_table(
        "statements",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_id", sa.Uuid(), nullable=False),
        sa.Column("section", sa.Text(), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("control_ids", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("parameters_used", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("faithful", sa.Boolean(), nullable=False),
        sa.Column("verification_issue", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["policy_id", "org_id"], ["policies.id", "policies.org_id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("policy_id", "seq"),
        sa.CheckConstraint("seq >= 1"),
    )
    op.create_table(
        "model_usage",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_microusd", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint("input_tokens >= 0 AND output_tokens >= 0 AND cost_microusd >= 0"),
    )
    for statement in (
        "ALTER TABLE policies ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE policies FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON policies USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "ALTER TABLE statements ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE statements FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON statements USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "ALTER TABLE model_usage ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE model_usage FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON model_usage USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove the generation audit trail."""
    for table in ("model_usage", "statements", "policies"):
        op.drop_table(table)
