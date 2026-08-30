"""Add tenant-scoped parsed upload sections."""

from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


class _Vector(sa.types.UserDefinedType):
    cache_ok = True

    def get_col_spec(self) -> str:
        return "VECTOR(1024)"


def upgrade() -> None:
    """Store parsed sections behind forced RLS and upload cascade."""
    op.create_unique_constraint("uq_uploads_id_org_id", "uploads", ["id", "org_id"])
    op.create_table(
        "upload_chunks",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("upload_id", sa.Uuid(), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", _Vector()),
        sa.ForeignKeyConstraint(
            ["upload_id", "org_id"],
            ["uploads.id", "uploads.org_id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("seq >= 1"),
        sa.UniqueConstraint("upload_id", "seq"),
    )
    for statement in (
        "ALTER TABLE upload_chunks ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE upload_chunks FORCE ROW LEVEL SECURITY",
        "CREATE POLICY tenant_isolation ON upload_chunks USING "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid) WITH CHECK "
        "(org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)",
    ):
        op.execute(statement)


def downgrade() -> None:
    """Remove parsed upload sections."""
    op.drop_table("upload_chunks")
    op.drop_constraint("uq_uploads_id_org_id", "uploads", type_="unique")

