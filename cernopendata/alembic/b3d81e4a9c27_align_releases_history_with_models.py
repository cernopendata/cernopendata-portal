"""Align releases history with the models."""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b3d81e4a9c27"
down_revision = "c17474edeffe"
branch_labels = ()
depends_on = "9848d0149abd"


def upgrade():
    """Upgrade database."""
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
