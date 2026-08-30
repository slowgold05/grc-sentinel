"""Enable the pgvector extension."""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable vector storage for control embeddings."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Leave the shared extension installed when rolling back."""
    pass
