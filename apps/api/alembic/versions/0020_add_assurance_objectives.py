"""Store contractual and voluntary assurance objectives separately from regulations."""

from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assurance_objectives",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("framework_id", sa.Uuid(), sa.ForeignKey("frameworks.id"), nullable=False),
        sa.Column("basis", sa.String(32), nullable=False),
        sa.Column("target_date", sa.Date()),
        sa.Column("scope", sa.Text(), nullable=False, server_default=""),
        sa.Column("selected_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint("basis IN ('customer_contract', 'company_strategy', 'regulator_request')"),
        sa.UniqueConstraint("engagement_id", "framework_id"),
    )
    for statement in (
        "ALTER TABLE assurance_objectives ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE assurance_objectives FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON assurance_objectives USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    op.drop_table("assurance_objectives")
