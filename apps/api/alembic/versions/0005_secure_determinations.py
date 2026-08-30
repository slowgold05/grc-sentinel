"""Enforce engagement tenancy and seed the first regulation."""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Bind determinations to same-org engagements and seed HIPAA."""
    op.drop_constraint("determinations_engagement_id_fkey", "determinations", type_="foreignkey")
    op.create_unique_constraint("uq_engagements_id_org_id", "engagements", ["id", "org_id"])
    op.create_foreign_key(
        "fk_determinations_engagement_org",
        "determinations",
        "engagements",
        ["engagement_id", "org_id"],
        ["id", "org_id"],
        ondelete="CASCADE",
    )
    op.execute(
        "INSERT INTO regulations (name, jurisdiction, citation) "
        "VALUES ('HIPAA', 'United States', '45 CFR Part 164 Subpart C') "
        "ON CONFLICT (name, jurisdiction, citation) DO NOTHING"
    )


def downgrade() -> None:
    """Restore the single-column engagement reference."""
    op.drop_constraint("fk_determinations_engagement_org", "determinations", type_="foreignkey")
    op.drop_constraint("uq_engagements_id_org_id", "engagements", type_="unique")
    op.create_foreign_key(
        "determinations_engagement_id_fkey",
        "determinations",
        "engagements",
        ["engagement_id"],
        ["id"],
        ondelete="CASCADE",
    )

