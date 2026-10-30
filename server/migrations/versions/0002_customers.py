"""leads -> customers, plus source and agent_log

Revision ID: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("leads", "customers")
    op.add_column(
        "customers",
        sa.Column("source", sa.String(200), nullable=False, server_default="text"),
    )
    op.alter_column("customers", "source", server_default=None)

    op.create_table(
        "agent_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(64), nullable=False),
        sa.Column("node", sa.String(40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("counts", sa.JSON(), nullable=True),
    )
    op.create_index("ix_agent_log_job_id", "agent_log", ["job_id"])


def downgrade() -> None:
    op.drop_table("agent_log")
    op.drop_column("customers", "source")
    op.rename_table("customers", "leads")
