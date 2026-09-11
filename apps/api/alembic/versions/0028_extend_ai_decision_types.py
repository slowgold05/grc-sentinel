"""Add decision types required by the deployment gate."""

from alembic import op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Allow residual-risk and legal-review decisions."""
    op.drop_constraint("ai_governance_decisions_decision_type_check", "ai_governance_decisions", type_="check")
    op.create_check_constraint(
        "ai_governance_decisions_decision_type_check",
        "ai_governance_decisions",
        "decision_type IN ('assessment', 'deployment', 'material_change', 'exception', 'retirement', 'residual_risk', 'legal_review')",
    )


def downgrade() -> None:
    """Restore the original decision categories."""
    op.drop_constraint("ai_governance_decisions_decision_type_check", "ai_governance_decisions", type_="check")
    op.create_check_constraint(
        "ai_governance_decisions_decision_type_check",
        "ai_governance_decisions",
        "decision_type IN ('assessment', 'deployment', 'material_change', 'exception', 'retirement')",
    )
