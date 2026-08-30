"""Link verified Clerk organizations to internal tenant UUIDs."""

from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orgs", sa.Column("auth_provider_id", sa.Text()))
    op.create_unique_constraint("uq_orgs_auth_provider_id", "orgs", ["auth_provider_id"])
    op.execute(
        "CREATE FUNCTION resolve_auth_org(p_provider_id text) RETURNS uuid "
        "LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, public AS $$ "
        "SELECT id FROM public.orgs WHERE auth_provider_id = p_provider_id $$"
    )
    op.execute("REVOKE ALL ON FUNCTION resolve_auth_org(text) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION resolve_auth_org(text) TO ruleset_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION resolve_auth_org(text)")
    op.drop_constraint("uq_orgs_auth_provider_id", "orgs", type_="unique")
    op.drop_column("orgs", "auth_provider_id")
