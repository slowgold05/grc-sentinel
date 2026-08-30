"""Add a least-privilege cross-tenant retention sweep."""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create a constrained function that deletes only expired records."""
    op.execute(
        "CREATE FUNCTION sweep_expired(p_now timestamptz) "
        "RETURNS TABLE(expired_uploads bigint, expired_engagements bigint) "
        "LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$ "
        "BEGIN "
        "WITH deleted AS (DELETE FROM public.uploads WHERE expires_at <= p_now RETURNING 1) "
        "SELECT count(*) INTO expired_uploads FROM deleted; "
        "WITH deleted AS (DELETE FROM public.engagements WHERE expires_at <= p_now RETURNING 1) "
        "SELECT count(*) INTO expired_engagements FROM deleted; "
        "RETURN NEXT; END; $$"
    )
    op.execute("REVOKE ALL ON FUNCTION sweep_expired(timestamptz) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION sweep_expired(timestamptz) TO ruleset_app")


def downgrade() -> None:
    """Remove the constrained retention function."""
    op.execute("DROP FUNCTION sweep_expired(timestamptz)")

