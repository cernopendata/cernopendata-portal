"""Rename cold request statuses and create enum for request status."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1793712006"
down_revision = "b3d81e4a9c27"
branch_labels = ()
depends_on = None

REQUEST_STATUS = sa.Enum(
    "WAITING", "SUBMITTING", "IN_PROGRESS", "COMPLETED", name="requeststatus"
)


def upgrade():
    """Upgrade database."""
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'SUBMITTING'"
        " WHERE status = 'submitted' AND num_transfers > 0"
    )
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'WAITING'"
        " WHERE status = 'submitted'"
    )
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'IN_PROGRESS'"
        " WHERE status = 'started'"
    )
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'COMPLETED'"
        " WHERE status = 'completed'"
    )
    REQUEST_STATUS.create(op.get_bind())
    op.alter_column(
        "cold_requests_metadata",
        "status",
        existing_type=sa.VARCHAR(length=50),
        type_=REQUEST_STATUS,
        existing_nullable=False,
        postgresql_using="status::requeststatus",
    )


def downgrade():
    """Downgrade database."""
    op.alter_column(
        "cold_requests_metadata",
        "status",
        existing_type=REQUEST_STATUS,
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
        postgresql_using="status::text",
    )
    REQUEST_STATUS.drop(op.get_bind())
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'submitted'"
        " WHERE status IN ('WAITING', 'SUBMITTING')"
    )
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'started'"
        " WHERE status = 'IN_PROGRESS'"
    )
    op.execute(
        "UPDATE cold_requests_metadata SET status = 'completed'"
        " WHERE status = 'COMPLETED'"
    )
