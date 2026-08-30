"""Add tenant-scoped OSINT caching and retention."""

from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the 30-day cache and include it in the privileged sweeper."""
    op.create_table(
        "osint_cache",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.Text(), nullable=False),
        sa.Column("module", sa.Text(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("org_id", "domain", "module"),
    )
    for statement in (
        "ALTER TABLE osint_cache ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE osint_cache FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON osint_cache USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
        "DROP FUNCTION public.sweep_expired(timestamptz)",
        """CREATE FUNCTION public.sweep_expired(p_now timestamptz)
RETURNS TABLE(expired_uploads bigint, expired_engagements bigint, expired_osint bigint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE upload_count bigint; engagement_count bigint; osint_count bigint;
BEGIN
  DELETE FROM public.uploads WHERE expires_at <= p_now; GET DIAGNOSTICS upload_count = ROW_COUNT;
  DELETE FROM public.engagements WHERE expires_at <= p_now; GET DIAGNOSTICS engagement_count = ROW_COUNT;
  DELETE FROM public.osint_cache WHERE expires_at <= p_now; GET DIAGNOSTICS osint_count = ROW_COUNT;
  RETURN QUERY SELECT upload_count, engagement_count, osint_count;
END $$""",
        "REVOKE ALL ON FUNCTION public.sweep_expired(timestamptz) FROM PUBLIC",
        "GRANT EXECUTE ON FUNCTION public.sweep_expired(timestamptz) TO ruleset_app",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove OSINT caching."""
    op.execute("DROP FUNCTION public.sweep_expired(timestamptz)")
    op.drop_table("osint_cache")
