from flask import Blueprint, flash, render_template
import json
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.forms import InspectionForm
from app.main import build_ml_form_fields, create_inspection
from app.models import Tree
from app.services import confidence_label

bp = Blueprint("trees", __name__, url_prefix="/trees")


@bp.get("")
@login_required
def list_trees():
    trees = db.session.scalars(
        db.select(Tree).where(Tree.active.is_(True)).order_by(Tree.code)
    ).all()
    return render_template("trees/list.html", trees=trees)


@bp.route("/<int:tree_id>")
@login_required
def detail(tree_id):
    tree = db.get_or_404(Tree, tree_id)
    return render_template("trees/detail.html", tree=tree)


@bp.route("/<int:tree_id>/inspection", methods=["GET", "POST"])
@login_required
def inspection(tree_id):
    tree = db.get_or_404(Tree, tree_id)
    form = InspectionForm()
    if form.validate_on_submit():
        try:
            observation, inference, level, reasons = create_inspection(tree, form)
            auto_prediction = next(
                (
                    prediction
                    for prediction in observation.predictions
                    if prediction.field_key == "vision_auto_extraction"
                ),
                None,
            )
            try:
                import json

                auto_payload = (
                    json.loads(auto_prediction.prediction) if auto_prediction else None
                )
            except json.JSONDecodeError:
                auto_payload = None
            flash(
                "Pemeriksaan tersimpan. Hasil model visual dan data yang perlu dikonfirmasi telah dicatat.",
                "success",
            )
            advanced = next(
                (
                    prediction
                    for prediction in observation.predictions
                    if prediction.field_key == "advanced_explainable_analysis"
                ),
                None,
            )
            assessment_payload = {}
            if observation.assessment:
                assessment_payload = json.loads(
                    observation.assessment.payload_json
                )
            return render_template(
                "trees/inspection_result.html",
                tree=tree,
                observation=observation,
                inference=inference,
                confidence_label=confidence_label(inference.confidence),
                level=level,
                reasons=reasons,
                ml_fields=build_ml_form_fields(auto_payload),
                algorithms=auto_payload.get("algorithms", []) if auto_payload else [],
                pipeline=auto_payload.get("pipeline", {}) if auto_payload else {},
                advanced_analysis=advanced,
                extracted_parameters=assessment_payload.get(
                    "extracted_parameters", []
                ),
                architecture_parameters=assessment_payload.get(
                    "architecture_parameters", []
                ),
                soil_parameters=assessment_payload.get("soil_parameters", []),
                weed_parameters=assessment_payload.get("weed_parameters", []),
                microclimate_parameters=assessment_payload.get(
                    "microclimate_parameters", []
                ),
                pest_disease_screening=assessment_payload.get(
                    "pest_disease_screening", {}
                ),
            )
        except SQLAlchemyError:
            db.session.rollback()
            flash(
                "Data belum dapat disimpan. Tidak ada data yang hilang. Silakan coba kembali.",
                "error",
            )
    return render_template("trees/inspection.html", tree=tree, form=form)
