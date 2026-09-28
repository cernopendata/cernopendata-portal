"""Align cold transfers and releases history with the models."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3d81e4a9c27"
down_revision = "c17474edeffe"
branch_labels = ()
depends_on = "9848d0149abd"


def upgrade():
    """Upgrade database."""
    op.add_column(
        "cold_transfers_metadata", sa.Column("request_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk_releases_history_user_id_accounts_user"),
        "releases_history",
        "accounts_user",
        ["user_id"],
        ["id"],
    )


def downgrade():
    """Downgrade database."""
    op.drop_constraint(
        op.f("fk_releases_history_user_id_accounts_user"),
        "releases_history",
        type_="foreignkey",
    )
    op.drop_column("cold_transfers_metadata", "request_id")
