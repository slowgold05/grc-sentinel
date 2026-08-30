"""Add the tenant risk register."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risks",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("likelihood", sa.SmallInteger(), nullable=False),
        sa.Column("impact", sa.SmallInteger(), nullable=False),
        sa.Column(
            "score",
            sa.SmallInteger(),
            sa.Computed("likelihood * impact", persisted=True),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), server_default="open", nullable=False),
        sa.Column("treatment", sa.Text(), nullable=False, server_default=""),
        sa.Column("control_ids", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("likelihood BETWEEN 1 AND 5"),
        sa.CheckConstraint("impact BETWEEN 1 AND 5"),
        sa.CheckConstraint("status IN ('open', 'mitigating', 'accepted', 'closed')"),
    )
    for statement in (
        "ALTER TABLE risks ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE risks FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON risks USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    op.drop_table("risks")
