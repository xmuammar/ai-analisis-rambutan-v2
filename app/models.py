from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Garden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    location_name = db.Column(db.String(160))
    area_m2 = db.Column(db.Float)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    trees = db.relationship(
        "Tree", back_populates="garden", cascade="all, delete-orphan"
    )


class Tree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False)
    garden_id = db.Column(db.Integer, db.ForeignKey("garden.id"), nullable=False)
    species = db.Column(db.String(80), nullable=False, default="Rambutan")
    variety = db.Column(db.String(80), nullable=False, default="Belereng")
    planting_date = db.Column(db.Date)
    row_number = db.Column(db.Integer)
    column_number = db.Column(db.Integer)
    spacing_cm = db.Column(db.Float)
    initial_height_cm = db.Column(db.Float)
    initial_stem_circumference_cm = db.Column(db.Float)
    root_condition_initial = db.Column(db.String(80))
    status = db.Column(db.String(32), nullable=False, default="SEHAT")
    active = db.Column(db.Boolean, nullable=False, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    garden = db.relationship("Garden", back_populates="trees")
    observations = db.relationship(
        "ObservationSession", back_populates="tree", cascade="all, delete-orphan"
    )


class ObservationSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tree_id = db.Column(
        db.Integer, db.ForeignKey("tree.id"), nullable=False, index=True
    )
    observation_datetime = db.Column(
        db.DateTime(timezone=True), default=utcnow, nullable=False
    )
    observer = db.Column(db.String(120))
    days_after_planting = db.Column(db.Integer)
    inspection_mode = db.Column(db.String(20), nullable=False, default="PHOTO_FIRST")
    observation_quality = db.Column(db.String(32), default="UNASSESSED")
    general_condition = db.Column(db.String(80))
    priority = db.Column(db.String(32), default="NORMAL")
    weather_summary = db.Column(db.String(120))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    tree = db.relationship("Tree", back_populates="observations")
    soil = db.relationship(
        "SoilObservation",
        back_populates="observation",
        uselist=False,
        cascade="all, delete-orphan",
    )
    photos = db.relationship(
        "Photo", back_populates="observation", cascade="all, delete-orphan"
    )
    predictions = db.relationship(
        "FieldPrediction", back_populates="observation", cascade="all, delete-orphan"
    )
    assessment = db.relationship(
        "AgronomicAssessment",
        back_populates="observation",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AgronomicAssessment(db.Model):
    __tablename__ = "agronomic_assessment"
    id = db.Column(db.Integer, primary_key=True)
    observation_id = db.Column(
        db.Integer, db.ForeignKey("observation_session.id"), unique=True, nullable=False
    )
    analysis_type = db.Column(db.String(100), nullable=False)
    analysis_version = db.Column(db.String(20), nullable=False, default="2.0")
    overall_status = db.Column(db.String(40), nullable=False, default="FAIR_TO_GOOD")
    confirmation_required = db.Column(db.Boolean, nullable=False, default=True)
    payload_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    observation = db.relationship("ObservationSession", back_populates="assessment")

    @property
    def payload(self):
        import json

        return json.loads(self.payload_json)


class SoilObservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    observation_id = db.Column(
        db.Integer, db.ForeignKey("observation_session.id"), unique=True, nullable=False
    )
    soil_visual_condition = db.Column(db.String(80))
    soil_moisture_visual = db.Column(db.String(40))
    standing_water = db.Column(db.Boolean, default=False, nullable=False)
    leaf_wilt = db.Column(db.Boolean, default=False, nullable=False)
    surface_dark = db.Column(db.Boolean, default=False, nullable=False)
    soil_surface_condition = db.Column(db.String(80))
    soil_compaction = db.Column(db.String(40))
    soil_drainage = db.Column(db.String(40))
    standing_water_depth_cm = db.Column(db.Float)
    visible_cracks = db.Column(db.Boolean, default=False)
    mulch_present = db.Column(db.Boolean, default=False)
    root_zone_confidence = db.Column(db.Float)
    observation = db.relationship("ObservationSession", back_populates="soil")


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    observation_id = db.Column(
        db.Integer, db.ForeignKey("observation_session.id"), nullable=False
    )
    capture_type = db.Column(db.String(40), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    quality_status = db.Column(db.String(32), default="UNASSESSED")
    quality_reasons = db.Column(db.Text)
    checksum = db.Column(db.String(64))
    captured_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    observation = db.relationship("ObservationSession", back_populates="photos")


class FieldPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    observation_id = db.Column(
        db.Integer, db.ForeignKey("observation_session.id"), nullable=False
    )
    field_key = db.Column(db.String(100), nullable=False)
    prediction = db.Column(db.Text, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(40), nullable=False, default="AI_INFERRED")
    explanation = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    observation = db.relationship("ObservationSession", back_populates="predictions")


class UserCorrection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(
        db.Integer, db.ForeignKey("field_prediction.id"), nullable=False
    )
    ai_original_value = db.Column(db.String(255), nullable=False)
    user_final_value = db.Column(db.String(255), nullable=False)
    was_corrected = db.Column(db.Boolean, nullable=False)
    correction_source = db.Column(
        db.String(40), nullable=False, default="USER_CONFIRMED"
    )
    correction_datetime = db.Column(
        db.DateTime(timezone=True), default=utcnow, nullable=False
    )


class TreeRecord(db.Model):
    """Base fields shared by longitudinal tree records."""

    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    tree_id = db.Column(
        db.Integer, db.ForeignKey("tree.id"), nullable=False, index=True
    )
    recorded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    notes = db.Column(db.Text)


class GrowthMeasurement(TreeRecord):
    __tablename__ = "growth_measurement"
    height_cm = db.Column(db.Float)
    stem_diameter_cm = db.Column(db.Float)
    stem_circumference_cm = db.Column(db.Float)
    canopy_width_cm = db.Column(db.Float)
    canopy_height_cm = db.Column(db.Float)
    canopy_ns_cm = db.Column(db.Float)
    canopy_ew_cm = db.Column(db.Float)
    primary_branch_count = db.Column(db.Integer)
    measurement_method = db.Column(db.String(40), default="MANUAL")
    confidence = db.Column(db.Float)

    def __init__(self, **kwargs):
        confidence = kwargs.get("confidence")
        for field in (
            "height_cm",
            "stem_diameter_cm",
            "stem_circumference_cm",
            "canopy_width_cm",
        ):
            value = kwargs.get(field)
            if value is not None and value < 0:
                raise ValueError(f"{field} tidak boleh negatif")
        if confidence is not None and not 0 <= confidence <= 1:
            raise ValueError("confidence harus berada di antara 0 dan 1")
        super().__init__(**kwargs)


class WateringEvent(TreeRecord):
    __tablename__ = "watering_event"
    liters = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(80))
    duration_min = db.Column(db.Float)
    reason = db.Column(db.String(160))

    def __init__(self, **kwargs):
        if kwargs.get("liters") is not None and kwargs["liters"] < 0:
            raise ValueError("liters tidak boleh negatif")
        if kwargs.get("duration_min") is not None and kwargs["duration_min"] < 0:
            raise ValueError("duration_min tidak boleh negatif")
        super().__init__(**kwargs)


class FertilizerEvent(TreeRecord):
    __tablename__ = "fertilizer_event"
    category = db.Column(db.String(80))
    product = db.Column(db.String(160))
    amount_g = db.Column(db.Float)
    manure_kg = db.Column(db.Float)
    application_method = db.Column(db.String(80))


class PruningEvent(TreeRecord):
    __tablename__ = "pruning_event"
    pruning_type = db.Column(db.String(80))
    branch_removed_count = db.Column(db.Integer)
    reason = db.Column(db.String(160))
    wound_condition = db.Column(db.String(80))


class FloweringObservation(TreeRecord):
    __tablename__ = "flowering_observation"
    present = db.Column(db.Boolean, nullable=False, default=False)
    stage = db.Column(db.String(40))
    cluster_count = db.Column(db.Integer)
    abundance = db.Column(db.String(40))
    flower_drop_level = db.Column(db.String(40))
    pollination_activity = db.Column(db.String(40))


class FruitObservation(TreeRecord):
    __tablename__ = "fruit_observation"
    present = db.Column(db.Boolean, nullable=False, default=False)
    stage = db.Column(db.String(40))
    cluster_count = db.Column(db.Integer)
    count_estimate = db.Column(db.Integer)
    average_diameter_mm = db.Column(db.Float)
    damage_percent = db.Column(db.Float)
    fruit_drop_count = db.Column(db.Integer)
    fruit_drop_level = db.Column(db.String(40))
    fruit_color = db.Column(db.String(40))
    ripeness = db.Column(db.String(40))


class PestObservation(TreeRecord):
    __tablename__ = "pest_observation"
    present = db.Column(db.Boolean, nullable=False, default=False)
    category = db.Column(db.String(80))
    severity = db.Column(db.String(40))
    affected_percent = db.Column(db.Float)
    affected_part = db.Column(db.String(80))
    spread = db.Column(db.String(40))


class DiseaseObservation(TreeRecord):
    __tablename__ = "disease_observation"
    present = db.Column(db.Boolean, nullable=False, default=False)
    category = db.Column(db.String(80))
    symptom_type = db.Column(db.String(80))
    severity = db.Column(db.String(40))
    affected_percent = db.Column(db.Float)
    affected_part = db.Column(db.String(80))
    spread = db.Column(db.String(40))


class WeedObservation(TreeRecord):
    __tablename__ = "weed_observation"
    level = db.Column(db.String(40))
    coverage_percent = db.Column(db.Float)
    height_cm = db.Column(db.Float)
    removed = db.Column(db.Boolean, default=False, nullable=False)
    density = db.Column(db.String(40))
    removal_method = db.Column(db.String(80))


class WeatherObservation(db.Model):
    __tablename__ = "weather_observation"
    id = db.Column(db.Integer, primary_key=True)
    garden_id = db.Column(
        db.Integer, db.ForeignKey("garden.id"), nullable=False, index=True
    )
    recorded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    rain_amount_mm = db.Column(db.Float)
    rain_intensity = db.Column(db.String(40))
    sun_condition = db.Column(db.String(40))
    wind_condition = db.Column(db.String(40))


class Harvest(db.Model):
    __tablename__ = "harvest"
    id = db.Column(db.Integer, primary_key=True)
    tree_id = db.Column(
        db.Integer, db.ForeignKey("tree.id"), nullable=False, index=True
    )
    harvest_date = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    fruit_count = db.Column(db.Integer)
    weight_kg = db.Column(db.Float)
    marketable_fruit_count = db.Column(db.Integer)
    quality_grade = db.Column(db.String(40))
    revenue = db.Column(db.Float)


class SensorDevice(db.Model):
    __tablename__ = "sensor_device"
    id = db.Column(db.Integer, primary_key=True)
    device_code = db.Column(db.String(80), unique=True, nullable=False)
    sensor_type = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(40), default="AVAILABLE", nullable=False)


class SensorReading(db.Model):
    __tablename__ = "sensor_reading"
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(
        db.Integer, db.ForeignKey("sensor_device.id"), nullable=False, index=True
    )
    tree_id = db.Column(db.Integer, db.ForeignKey("tree.id"), index=True)
    recorded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    metric = db.Column(db.String(80), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    source = db.Column(db.String(40), nullable=False, default="SENSOR_MEASURED")


class ModelMetadata(db.Model):
    __tablename__ = "model_metadata"
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(160), nullable=False)
    task = db.Column(db.String(80), nullable=False)
    version = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="NOT_INSTALLED")
    runtime = db.Column(db.String(80))
    checksum = db.Column(db.String(128))
    metrics_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class SystemLog(db.Model):
    __tablename__ = "system_log"
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(40), nullable=False)
    level = db.Column(db.String(20), nullable=False, default="INFO")
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
