"""Add immutable tenant-scoped control evidence."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "control_evidence",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("observed", postgresql.JSONB(), nullable=False),
        sa.Column("raw_response", postgresql.JSONB(), nullable=False),
        sa.Column("control_ids", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("tested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pass', 'fail', 'error')"),
    )
    for statement in (
        "ALTER TABLE control_evidence ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE control_evidence FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_read ON control_evidence FOR SELECT USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "CREATE POLICY tenant_append ON control_evidence FOR INSERT WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    op.drop_table("control_evidence")
