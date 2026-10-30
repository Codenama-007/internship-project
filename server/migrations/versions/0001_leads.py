"""leads

Revision ID: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("broker_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(120), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("query_text", sa.String(2000), nullable=False),
        sa.Column("locality", sa.String(80), nullable=True),
        sa.Column("bhk", sa.String(20), nullable=True),
        sa.Column("budget", sa.Integer(), nullable=True),
        sa.Column("enquiry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_chat", sa.String(200), nullable=False),
        sa.Column("source_msg_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("source_msg_hash", name="uq_leads_source_msg_hash"),
    )
    op.create_index("ix_leads_broker_id", "leads", ["broker_id"])
    op.create_index("ix_leads_phone", "leads", ["phone"])
    op.create_index("ix_leads_locality", "leads", ["locality"])


def downgrade() -> None:
    op.drop_table("leads")
