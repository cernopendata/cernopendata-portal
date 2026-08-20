"""Create cernopendata tables."""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c17474edeffe"
down_revision = "c99fb6f8ac5a"
branch_labels = ()
depends_on = ("862037093962", "9848d0149abd")

RELEASE_STATUS_VALUES = (
    "DRAFT",
    "READY",
    "EDITING",
    "STAGED",
    "STAGING",
    "ROLLINGBACK",
    "PUBLISHING",
    "PUBLISHED",
)


def _release_status():
    """Return the release status enum without automatic type creation."""
    return postgresql.ENUM(
        *RELEASE_STATUS_VALUES, name="releasestatus", create_type=False
    )


def upgrade():
    """Upgrade database."""
    op.create_table(
        "cold_location",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cold_path", sa.String(length=512), nullable=False),
        sa.Column("hot_path", sa.String(length=512), nullable=False),
        sa.Column("manager_class", sa.String(length=512), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cold_location")),
        sa.UniqueConstraint("hot_path", name=op.f("uq_cold_location_hot_path")),
    )
    op.create_table(
        "cold_requests_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("record_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("num_transfers", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "subscribers", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("size", sa.BigInteger(), nullable=True),
        sa.Column("file", sa.String(length=255), nullable=True),
        sa.Column("num_hot_files", sa.Integer(), nullable=True),
        sa.Column("num_cold_files", sa.Integer(), nullable=True),
        sa.Column("num_record_files", sa.Integer(), nullable=True),
        sa.Column("record_size", sa.BigInteger(), nullable=True),
        sa.Column("num_failed_transfers", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["record_id"],
            ["records_metadata.id"],
            name=op.f("fk_cold_requests_metadata_record_id_records_metadata"),
        ),
        sa.PrimaryKeyConstraint(
            "id", "record_id", name=op.f("pk_cold_requests_metadata")
        ),
    )
    op.create_index(
        "ix_cold_requests_action", "cold_requests_metadata", ["action"], unique=False
    )
    op.create_index(
        "ix_cold_requests_completed_at",
        "cold_requests_metadata",
        ["completed_at"],
        unique=False,
    )
    op.create_index(
        "ix_cold_requests_status", "cold_requests_metadata", ["status"], unique=False
    )
    op.create_table(
        "cold_transfers_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("record_uuid", sa.String(length=36), nullable=False),
        sa.Column("file_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("new_filename", sa.String(length=512), nullable=False),
        sa.Column("method", sa.String(length=512), nullable=False),
        sa.Column("method_id", sa.String(length=36), nullable=False),
        sa.Column("submitted", sa.DateTime(), nullable=False),
        sa.Column("last_check", sa.DateTime(), nullable=False),
        sa.Column("finished", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("size", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cold_transfers_metadata")),
    )
    op.create_index(
        "ix_cold_transfers_last_check",
        "cold_transfers_metadata",
        ["last_check"],
        unique=False,
    )
    op.create_index(
        "ix_cold_transfers_record",
        "cold_transfers_metadata",
        ["record_uuid"],
        unique=False,
    )
    op.create_index(
        "ix_cold_transfers_status", "cold_transfers_metadata", ["status"], unique=False
    )

    postgresql.ENUM(*RELEASE_STATUS_VALUES, name="releasestatus").create(op.get_bind())

    op.create_table(
        "releases_metadata",
        sa.Column("status", _release_status(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("discussion_url", sa.String(length=2048), nullable=True),
        sa.Column("experiment", sa.String(length=50), nullable=False),
        sa.Column("records", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("documents", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("errors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("num_records", sa.Integer(), nullable=False),
        sa.Column("num_errors", sa.Integer(), nullable=False),
        sa.Column("num_docs", sa.Integer(), nullable=False),
        sa.Column("num_files", sa.Integer(), nullable=False),
        sa.Column("num_file_indices", sa.Integer(), nullable=False),
        sa.Column("size_files", sa.BigInteger(), nullable=False),
        sa.Column("size_indexFiles", sa.BigInteger(), nullable=False),
        sa.Column("max_recid", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_releases_metadata")),
    )
    op.create_index(
        op.f("ix_releases_metadata_status"),
        "releases_metadata",
        ["status"],
        unique=False,
    )
    op.create_table(
        "releases_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("release_id", sa.Integer(), nullable=False),
        sa.Column("status", _release_status(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["release_id"],
            ["releases_metadata.id"],
            name=op.f("fk_releases_history_release_id_releases_metadata"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["accounts_user.id"],
            name=op.f("fk_releases_history_user_id_accounts_user"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_releases_history")),
    )
    op.create_table(
        "releases_validations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("release_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["release_id"],
            ["releases_metadata.id"],
            name=op.f("fk_releases_validations_release_id_releases_metadata"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_releases_validations")),
        sa.UniqueConstraint("release_id", "name", name="uq_release_validation"),
    )
    op.create_index(
        op.f("ix_releases_validations_name"),
        "releases_validations",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_releases_validations_release_id"),
        "releases_validations",
        ["release_id"],
        unique=False,
    )


def downgrade():
    """Downgrade database."""
    op.drop_index(
        op.f("ix_releases_validations_release_id"), table_name="releases_validations"
    )
    op.drop_index(
        op.f("ix_releases_validations_name"), table_name="releases_validations"
    )
    op.drop_table("releases_validations")
    op.drop_table("releases_history")
    op.drop_index(op.f("ix_releases_metadata_status"), table_name="releases_metadata")
    op.drop_table("releases_metadata")
    postgresql.ENUM(name="releasestatus").drop(op.get_bind())
    op.drop_index("ix_cold_transfers_status", table_name="cold_transfers_metadata")
    op.drop_index("ix_cold_transfers_record", table_name="cold_transfers_metadata")
    op.drop_index("ix_cold_transfers_last_check", table_name="cold_transfers_metadata")
    op.drop_table("cold_transfers_metadata")
    op.drop_index("ix_cold_requests_status", table_name="cold_requests_metadata")
    op.drop_index("ix_cold_requests_completed_at", table_name="cold_requests_metadata")
    op.drop_index("ix_cold_requests_action", table_name="cold_requests_metadata")
    op.drop_table("cold_requests_metadata")
    op.drop_table("cold_location")
