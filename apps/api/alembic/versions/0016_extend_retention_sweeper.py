"""Enforce retention for monitoring and audit-hub records."""

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP FUNCTION public.sweep_expired(timestamptz)")
    op.execute(
        """CREATE FUNCTION public.sweep_expired(p_now timestamptz)
RETURNS TABLE(expired_uploads bigint, expired_engagements bigint, expired_osint bigint,
expired_evidence bigint, expired_audit_events bigint, expired_share_links bigint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE upload_count bigint; engagement_count bigint; osint_count bigint;
evidence_count bigint; event_count bigint; share_count bigint;
BEGIN
  DELETE FROM public.uploads WHERE expires_at <= p_now; GET DIAGNOSTICS upload_count = ROW_COUNT;
  DELETE FROM public.engagements WHERE expires_at <= p_now; GET DIAGNOSTICS engagement_count = ROW_COUNT;
  DELETE FROM public.osint_cache WHERE expires_at <= p_now; GET DIAGNOSTICS osint_count = ROW_COUNT;
  DELETE FROM public.control_evidence WHERE tested_at <= p_now - interval '1 year';
  GET DIAGNOSTICS evidence_count = ROW_COUNT;
  DELETE FROM public.audit_events WHERE created_at <= p_now - interval '1 year';
  GET DIAGNOSTICS event_count = ROW_COUNT;
  DELETE FROM public.audit_share_links WHERE expires_at <= p_now;
  GET DIAGNOSTICS share_count = ROW_COUNT;
  RETURN QUERY SELECT upload_count, engagement_count, osint_count, evidence_count,
    event_count, share_count;
END $$"""
    )
    op.execute("REVOKE ALL ON FUNCTION public.sweep_expired(timestamptz) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.sweep_expired(timestamptz) TO ruleset_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION public.sweep_expired(timestamptz)")
    op.execute(
        """CREATE FUNCTION public.sweep_expired(p_now timestamptz)
RETURNS TABLE(expired_uploads bigint, expired_engagements bigint, expired_osint bigint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE upload_count bigint; engagement_count bigint; osint_count bigint;
BEGIN
  DELETE FROM public.uploads WHERE expires_at <= p_now; GET DIAGNOSTICS upload_count = ROW_COUNT;
  DELETE FROM public.engagements WHERE expires_at <= p_now; GET DIAGNOSTICS engagement_count = ROW_COUNT;
  DELETE FROM public.osint_cache WHERE expires_at <= p_now; GET DIAGNOSTICS osint_count = ROW_COUNT;
  RETURN QUERY SELECT upload_count, engagement_count, osint_count;
END $$"""
    )
    op.execute("REVOKE ALL ON FUNCTION public.sweep_expired(timestamptz) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.sweep_expired(timestamptz) TO ruleset_app")
