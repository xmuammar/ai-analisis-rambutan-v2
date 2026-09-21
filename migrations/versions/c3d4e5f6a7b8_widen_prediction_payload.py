"""allow long JSON prediction payloads

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
"""

import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("field_prediction") as batch_op:
        batch_op.alter_column(
            "prediction",
            existing_type=sa.String(length=255),
            type_=sa.Text(),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table("field_prediction") as batch_op:
        batch_op.alter_column(
            "prediction",
            existing_type=sa.Text(),
            type_=sa.String(length=255),
            existing_nullable=False,
        )
