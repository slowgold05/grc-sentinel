"""Add tenant identity, engagements, determinations, and forced RLS."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the minimum tenant data path and enforce isolation in PostgreSQL."""
    op.create_table(
        "orgs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("auth_provider_id", sa.Text(), nullable=False, unique=True),
        sa.Column("role", sa.Text(), nullable=False),
        sa.CheckConstraint("role IN ('owner', 'member')"),
    )
    op.create_table(
        "engagements",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "determinations",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), sa.ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("regulation_id", sa.Uuid(), sa.ForeignKey("regulations.id"), nullable=False),
        sa.Column("rule_id", sa.Text(), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("facts", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rule_version >= 1"),
        sa.UniqueConstraint("engagement_id", "rule_id", "rule_version"),
    )
    for statement in (
        "ALTER TABLE orgs ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE orgs FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON orgs USING "
        "(id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "ALTER TABLE users ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE users FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON users USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "ALTER TABLE engagements ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE engagements FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON engagements USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "ALTER TABLE determinations ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE determinations FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON determinations USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove the minimum tenant data path."""
    for table in ("determinations", "engagements", "users", "orgs"):
        op.drop_table(table)
