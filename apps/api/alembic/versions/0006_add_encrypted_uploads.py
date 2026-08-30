"""Add encrypted tenant uploads."""

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create encrypted upload storage with forced tenant isolation."""
    op.create_table(
        "uploads",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("media_type", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("nonce", sa.LargeBinary(), nullable=False),
        sa.Column("wrapped_key", sa.LargeBinary(), nullable=False),
        sa.Column("key_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["engagement_id", "org_id"],
            ["engagements.id", "engagements.org_id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("org_id", "sha256"),
    )
    for statement in (
        "ALTER TABLE uploads ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE uploads FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON uploads USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove encrypted upload storage."""
    op.drop_table("uploads")

