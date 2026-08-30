"""Create the shared control knowledge base."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


class _Vector(sa.types.UserDefinedType):
    cache_ok = True

    def get_col_spec(self) -> str:
        return "VECTOR(1024)"


def upgrade() -> None:
    """Create the roadmap's seven shared reference tables."""
    op.create_table(
        "frameworks",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("publisher", sa.Text(), nullable=False),
        sa.Column("machine_readable_source", sa.Text(), nullable=False),
        sa.UniqueConstraint("name", "version"),
    )
    op.create_table(
        "controls",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("framework_id", sa.Uuid(), sa.ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("control_code", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("params", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("oscal_uuid", sa.Uuid(), unique=True),
        sa.UniqueConstraint("framework_id", "control_code"),
    )
    op.create_table(
        "crosswalks",
        sa.Column("control_a", sa.Uuid(), sa.ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("control_b", sa.Uuid(), sa.ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("relation", sa.Text(), nullable=False),
        sa.Column("strength", sa.Float(), nullable=False),
        sa.Column("source", sa.Text(), primary_key=True),
        sa.CheckConstraint("relation IN ('equivalent', 'subset', 'related')"),
        sa.CheckConstraint("strength >= 0 AND strength <= 1"),
        sa.CheckConstraint("control_a <> control_b"),
    )
    op.create_table(
        "regulations",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("jurisdiction", sa.Text(), nullable=False),
        sa.Column("citation", sa.Text(), nullable=False),
        sa.UniqueConstraint("name", "jurisdiction", "citation"),
    )
    op.create_table(
        "regulation_controls",
        sa.Column("regulation_id", sa.Uuid(), sa.ForeignKey("regulations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("control_id", sa.Uuid(), sa.ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("obligation_text_ref", sa.Text(), nullable=False),
    )
    op.create_table(
        "control_embeddings",
        sa.Column("control_id", sa.Uuid(), sa.ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("embedding", _Vector(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
    )
    op.create_table(
        "policy_templates",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("policy_type", sa.Text(), nullable=False),
        sa.Column("section", sa.Text(), nullable=False),
        sa.Column("template_body", sa.Text(), nullable=False),
        sa.Column("control_ids", postgresql.ARRAY(sa.Uuid()), nullable=False),
        sa.UniqueConstraint("policy_type", "section"),
    )


def downgrade() -> None:
    """Drop the shared knowledge-base tables in dependency order."""
    for table in (
        "policy_templates",
        "control_embeddings",
        "regulation_controls",
        "regulations",
        "crosswalks",
        "controls",
        "frameworks",
    ):
        op.drop_table(table)

