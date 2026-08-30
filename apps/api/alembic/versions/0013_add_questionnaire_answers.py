"""Persist grounded questionnaire answers for human review."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "questionnaire_answers",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("upload_id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("statement_ids", postgresql.ARRAY(sa.Uuid()), nullable=False),
        sa.Column("review_status", sa.Text(), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["engagement_id", "org_id"],
            ["engagements.id", "engagements.org_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["upload_id", "org_id"], ["uploads.id", "uploads.org_id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint("review_status IN ('pending', 'approved', 'rejected')"),
    )
    for statement in (
        "ALTER TABLE questionnaire_answers ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE questionnaire_answers FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON questionnaire_answers USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    op.drop_table("questionnaire_answers")
