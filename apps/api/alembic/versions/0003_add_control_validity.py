"""Add control validity dates for framework drift."""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add optional validity bounds to versioned controls."""
    op.add_column("controls", sa.Column("valid_from", sa.Date()))
    op.add_column("controls", sa.Column("valid_to", sa.Date()))
    op.create_check_constraint(
        "ck_controls_valid_dates",
        "controls",
        "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
    )


def downgrade() -> None:
    """Remove control validity bounds."""
    op.drop_constraint("ck_controls_valid_dates", "controls", type_="check")
    op.drop_column("controls", "valid_to")
    op.drop_column("controls", "valid_from")

