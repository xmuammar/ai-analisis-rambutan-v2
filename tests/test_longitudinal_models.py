from datetime import datetime, timezone

import pytest

from app import db
from app.models import GrowthMeasurement, Tree, WateringEvent


def test_longitudinal_records_are_persisted(client, app):
    with app.app_context():
        tree = db.session.scalar(db.select(Tree).where(Tree.code == "RBT-001"))
        db.session.add(
            GrowthMeasurement(
                tree_id=tree.id,
                recorded_at=datetime.now(timezone.utc),
                height_cm=161,
                measurement_method="MANUAL",
                confidence=0.9,
            )
        )
        db.session.add(WateringEvent(tree_id=tree.id, liters=2.0, method="MANUAL"))
        db.session.commit()
        assert db.session.scalar(db.select(GrowthMeasurement.height_cm)) == 161
        assert db.session.scalar(db.select(WateringEvent.liters)) == 2.0


def test_negative_watering_is_rejected_by_validation_boundary():
    with pytest.raises(ValueError, match="liters"):
        WateringEvent(tree_id=1, liters=-1)
