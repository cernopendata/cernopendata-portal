"""Fix cold transfers without status."""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1793809347"
down_revision = "1793712006"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.execute(
        "UPDATE cold_transfers_metadata"
        " SET status = 'FAILED', reason = 'Status could not be retrieved'"
        " WHERE status IS NULL AND finished IS NOT NULL"
    )
    op.execute(
        "UPDATE cold_requests_metadata SET"
        " num_failed_transfers = (SELECT count(*) FROM cold_transfers_metadata"
        " WHERE request_id = cold_requests_metadata.id AND status = 'FAILED'),"
        " size = (SELECT coalesce(sum(size), 0) FROM cold_transfers_metadata"
        " WHERE request_id = cold_requests_metadata.id AND status = 'DONE')"
    )


def downgrade():
    """Downgrade database."""
    op.execute(
        "UPDATE cold_transfers_metadata SET status = NULL, reason = NULL"
        " WHERE status = 'FAILED' AND reason = 'Status could not be retrieved'"
    )
