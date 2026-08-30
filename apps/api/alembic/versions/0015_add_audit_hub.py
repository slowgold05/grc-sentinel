"""Add expiring audit-share links and append-only access events."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_share_links",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["engagement_id", "org_id"],
            ["engagements.id", "engagements.org_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["engagement_id", "org_id"],
            ["engagements.id", "engagements.org_id"],
            ondelete="CASCADE",
        ),
    )
    for statement in (
        "ALTER TABLE audit_share_links ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE audit_share_links FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON audit_share_links USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE audit_events FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_read ON audit_events FOR SELECT USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "CREATE POLICY tenant_append ON audit_events FOR INSERT WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)
    op.execute(
        "CREATE FUNCTION resolve_audit_share(p_token_hash bytea) "
        "RETURNS TABLE(org_id uuid, engagement_id uuid, share_id uuid) "
        "LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, public AS $$ "
        "SELECT links.org_id, links.engagement_id, links.id FROM public.audit_share_links AS links "
        "WHERE links.token_hash = p_token_hash AND links.revoked_at IS NULL "
        "AND links.expires_at > now() $$"
    )
    op.execute("REVOKE ALL ON FUNCTION resolve_audit_share(bytea) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION resolve_audit_share(bytea) TO ruleset_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION resolve_audit_share(bytea)")
    op.drop_table("audit_events")
    op.drop_table("audit_share_links")
