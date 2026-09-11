"""Add AI policy source traceability and human approvals."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("policies", sa.Column("ai_system_id", sa.Uuid(), nullable=True))
    op.add_column(
        "policies",
        sa.Column("source_versions", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "policies",
        sa.Column("gaps", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
    )
    op.create_foreign_key(
        "fk_policies_ai_system", "policies", "ai_systems", ["ai_system_id"], ["id"], ondelete="CASCADE"
    )
    op.create_table(
        "policy_approvals",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_id", sa.Uuid(), nullable=False),
        sa.Column("approved_by", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["policy_id", "org_id"], ["policies.id", "policies.org_id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("policy_id"),
    )
    for statement in (
        "ALTER TABLE policy_approvals ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE policy_approvals FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_read ON policy_approvals FOR SELECT USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "CREATE POLICY tenant_insert ON policy_approvals FOR INSERT WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    op.drop_table("policy_approvals")
    op.drop_constraint("fk_policies_ai_system", "policies", type_="foreignkey")
    op.drop_column("policies", "gaps")
    op.drop_column("policies", "source_versions")
    op.drop_column("policies", "ai_system_id")
