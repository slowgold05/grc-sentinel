"""Add append-only AI incident records."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_incidents",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column(
            "org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column(
            "ai_system_id",
            sa.Uuid(),
            sa.ForeignKey("ai_systems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id", "org_id"],
            ["engagements.id", "engagements.org_id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("id", "org_id"),
    )
    op.create_table(
        "ai_incident_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column(
            "org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("incident_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("impact", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("owner", sa.Text(), nullable=False),
        sa.Column("regulatory_review_required", sa.Boolean(), nullable=False),
        sa.Column("risk_ids", postgresql.ARRAY(sa.Uuid()), nullable=False, server_default="{}"),
        sa.Column(
            "evaluation_run_ids", postgresql.ARRAY(sa.Uuid()), nullable=False, server_default="{}"
        ),
        sa.Column("evidence_ids", postgresql.ARRAY(sa.Uuid()), nullable=False, server_default="{}"),
        sa.Column("recorded_by", sa.Text(), nullable=False),
        sa.Column(
            "recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["incident_id", "org_id"],
            ["ai_incidents.id", "ai_incidents.org_id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("state IN ('created', 'triaged', 'contained', 'resolved')"),
        sa.CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')"),
    )
    op.create_index("ix_ai_incident_history", "ai_incident_events", ["incident_id", "recorded_at"])
    for table in ("ai_incidents", "ai_incident_events"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_read ON {table} FOR SELECT USING "
            "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)"
        )
        op.execute(
            f"CREATE POLICY tenant_insert ON {table} FOR INSERT WITH CHECK "
            "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)"
        )


def downgrade() -> None:
    op.drop_table("ai_incident_events")
    op.drop_table("ai_incidents")
