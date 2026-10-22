"""Rename cold request statuses."""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1793712006"
down_revision = "b3d81e4a9c27"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'submitting'"
        " WHERE status = 'submitted' AND num_transfers > 0"
    )
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'waiting'"
        " WHERE status = 'submitted'"
    )
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'in progress'"
        " WHERE status = 'started'"
    )


def downgrade():
    """Downgrade database."""
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'submitted'"
        " WHERE status IN ('waiting', 'submitting')"
    )
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'started'"
        " WHERE status = 'in progress'"
    )
