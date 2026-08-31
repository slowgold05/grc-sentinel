"""Provision verified Clerk organizations on first authenticated request."""

from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE FUNCTION provision_auth_org(p_provider_id text, p_name text) RETURNS uuid "
        "LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, public AS $$ "
        "INSERT INTO public.orgs (name, auth_provider_id) "
        "VALUES (COALESCE(NULLIF(p_name, ''), p_provider_id), p_provider_id) "
        "ON CONFLICT (auth_provider_id) DO UPDATE "
        "SET auth_provider_id = EXCLUDED.auth_provider_id RETURNING id $$"
    )
    op.execute("REVOKE ALL ON FUNCTION provision_auth_org(text, text) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION provision_auth_org(text, text) TO ruleset_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION provision_auth_org(text, text)")
