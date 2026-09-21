"""add versioned agronomic assessment

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
"""

import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agronomic_assessment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("observation_id", sa.Integer(), sa.ForeignKey("observation_session.id"), nullable=False, unique=True),
        sa.Column("analysis_type", sa.String(length=100), nullable=False),
        sa.Column("analysis_version", sa.String(length=20), nullable=False, server_default="2.0"),
        sa.Column("overall_status", sa.String(length=40), nullable=False, server_default="FAIR_TO_GOOD"),
        sa.Column("confirmation_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("agronomic_assessment")
