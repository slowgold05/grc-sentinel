"""Persist tenant-scoped gap-analysis coverage results."""

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create append-only coverage results behind forced RLS."""
    op.create_table(
        "coverage_results",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("upload_id", sa.Uuid(), nullable=False),
        sa.Column("control_id", sa.Uuid(), sa.ForeignKey("controls.id"), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), sa.ForeignKey("upload_chunks.id", ondelete="CASCADE")),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("evidence_quote", sa.Text(), nullable=False, server_default=""),
        sa.Column("gap", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["engagement_id", "org_id"], ["engagements.id", "engagements.org_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["upload_id", "org_id"], ["uploads.id", "uploads.org_id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint("status IN ('covered', 'partial', 'missing')"),
        sa.CheckConstraint("status = 'missing' OR chunk_id IS NOT NULL"),
    )
    for statement in (
        "ALTER TABLE coverage_results ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE coverage_results FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON coverage_results USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove persisted coverage results."""
    op.drop_table("coverage_results")
