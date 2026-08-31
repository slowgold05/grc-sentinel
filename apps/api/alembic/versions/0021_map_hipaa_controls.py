"""Map HIPAA applicability to the installed HIPAA control catalog."""

from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO regulation_controls (regulation_id, control_id, obligation_text_ref) "
        "SELECT r.id, c.id, c.control_code FROM regulations r "
        "JOIN frameworks f ON f.name = 'HIPAA Security Rule' "
        "JOIN controls c ON c.framework_id = f.id WHERE r.name = 'HIPAA' "
        "ON CONFLICT DO NOTHING"
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM regulation_controls rc USING regulations r, controls c, frameworks f "
        "WHERE rc.regulation_id = r.id AND rc.control_id = c.id AND c.framework_id = f.id "
        "AND r.name = 'HIPAA' AND f.name = 'HIPAA Security Rule'"
    )
