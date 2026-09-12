"""Allow audit shares to be scoped to one AI system."""

from alembic import op
import sqlalchemy as sa

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP FUNCTION resolve_audit_share(bytea)")
    op.add_column("audit_share_links", sa.Column("ai_system_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_audit_share_ai_system",
        "audit_share_links",
        "ai_systems",
        ["ai_system_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.execute(
        "CREATE FUNCTION resolve_audit_share(p_token_hash bytea) "
        "RETURNS TABLE(org_id uuid, engagement_id uuid, share_id uuid, ai_system_id uuid) "
        "LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, public AS $$ "
        "SELECT links.org_id, links.engagement_id, links.id, links.ai_system_id "
        "FROM public.audit_share_links AS links WHERE links.token_hash = p_token_hash "
        "AND links.revoked_at IS NULL AND links.expires_at > now() $$"
    )
    op.execute("REVOKE ALL ON FUNCTION resolve_audit_share(bytea) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION resolve_audit_share(bytea) TO ruleset_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION resolve_audit_share(bytea)")
    op.drop_constraint("fk_audit_share_ai_system", "audit_share_links", type_="foreignkey")
    op.drop_column("audit_share_links", "ai_system_id")
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
