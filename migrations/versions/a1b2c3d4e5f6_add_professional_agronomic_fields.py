"""add professional agronomic fields

Revision ID: a1b2c3d4e5f6
Revises: 958d06f21f28
"""

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "958d06f21f28"
branch_labels = None
depends_on = None


def upgrade():
    additions = {
        "tree": [
            ("planting_date", sa.Date()),
            ("row_number", sa.Integer()),
            ("column_number", sa.Integer()),
            ("spacing_cm", sa.Float()),
            ("initial_height_cm", sa.Float()),
            ("initial_stem_circumference_cm", sa.Float()),
            ("root_condition_initial", sa.String(80)),
        ],
        "observation_session": [
            ("days_after_planting", sa.Integer()),
            ("priority", sa.String(32)),
            ("weather_summary", sa.String(120)),
        ],
        "soil_observation": [
            ("soil_surface_condition", sa.String(80)),
            ("soil_compaction", sa.String(40)),
            ("soil_drainage", sa.String(40)),
            ("standing_water_depth_cm", sa.Float()),
            ("visible_cracks", sa.Boolean()),
            ("mulch_present", sa.Boolean()),
            ("root_zone_confidence", sa.Float()),
        ],
        "growth_measurement": [
            ("canopy_height_cm", sa.Float()),
            ("canopy_ns_cm", sa.Float()),
            ("canopy_ew_cm", sa.Float()),
            ("primary_branch_count", sa.Integer()),
        ],
        "flowering_observation": [
            ("flower_drop_level", sa.String(40)),
            ("pollination_activity", sa.String(40)),
        ],
        "fruit_observation": [
            ("fruit_drop_count", sa.Integer()),
            ("fruit_drop_level", sa.String(40)),
            ("fruit_color", sa.String(40)),
            ("ripeness", sa.String(40)),
        ],
        "pest_observation": [
            ("affected_part", sa.String(80)),
            ("spread", sa.String(40)),
        ],
        "disease_observation": [
            ("affected_part", sa.String(80)),
            ("spread", sa.String(40)),
        ],
        "weed_observation": [
            ("density", sa.String(40)),
            ("removal_method", sa.String(80)),
        ],
    }
    for table, columns in additions.items():
        for name, column_type in columns:
            op.add_column(table, sa.Column(name, column_type, nullable=True))


def downgrade():
    additions = {
        "tree": ["planting_date", "row_number", "column_number", "spacing_cm",
                 "initial_height_cm", "initial_stem_circumference_cm", "root_condition_initial"],
        "observation_session": ["days_after_planting", "priority", "weather_summary"],
        "soil_observation": ["soil_surface_condition", "soil_compaction", "soil_drainage",
                             "standing_water_depth_cm", "visible_cracks", "mulch_present",
                             "root_zone_confidence"],
        "growth_measurement": ["canopy_height_cm", "canopy_ns_cm", "canopy_ew_cm",
                               "primary_branch_count"],
        "flowering_observation": ["flower_drop_level", "pollination_activity"],
        "fruit_observation": ["fruit_drop_count", "fruit_drop_level", "fruit_color", "ripeness"],
        "pest_observation": ["affected_part", "spread"],
        "disease_observation": ["affected_part", "spread"],
        "weed_observation": ["density", "removal_method"],
    }
    for table, columns in additions.items():
        for column in columns:
            op.drop_column(table, column)
