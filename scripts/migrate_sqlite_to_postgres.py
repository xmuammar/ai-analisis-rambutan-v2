"""Copy an existing SQLite database into a migrated PostgreSQL database.

The target must already be upgraded with ``flask db upgrade``. The command is
read-only by default; pass ``--apply`` to perform the copy.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import MetaData, create_engine, text

from config import normalize_database_url
from app.ai.assessment import build_assessment


def _table_names(metadata: MetaData) -> list[str]:
    return [
        table.name
        for table in metadata.sorted_tables
        if table.name != "alembic_version"
    ]


def migrate(source_url: str, target_url: str, *, apply: bool = False) -> dict[str, int]:
    source = create_engine(source_url)
    target = create_engine(normalize_database_url(target_url), pool_pre_ping=True)
    source_meta = MetaData()
    target_meta = MetaData()
    source_meta.reflect(bind=source)
    target_meta.reflect(bind=target)
    missing = set(_table_names(source_meta)) - set(_table_names(target_meta))
    if missing:
        raise RuntimeError(
            "Target schema is missing tables; run `flask db upgrade` first: "
            + ", ".join(sorted(missing))
        )

    counts: dict[str, int] = {}
    with source.connect() as source_conn, target.connect() as target_conn:
        target_conn.execution_options(isolation_level="SERIALIZABLE")
        existing = target_conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name <> 'alembic_version'"
            )
        ).scalars().all()
        nonempty = [
            table
            for table in existing
            if target_conn.execute(text(f'SELECT 1 FROM "{table}" LIMIT 1')).first()
        ]
        if nonempty:
            raise RuntimeError(
                "Target database is not empty: "
                + ", ".join(sorted(nonempty))
                + ". Use a fresh database; this tool never merges rows."
            )

        for name in _table_names(source_meta):
            source_table = source_meta.tables[name]
            target_table = target_meta.tables[name]
            source_columns = {column.name for column in source_table.columns}
            columns = [
                column.name
                for column in target_table.columns
                if column.name in source_columns
            ]
            rows = source_conn.execute(source_table.select()).mappings().all()
            counts[name] = len(rows)
            if not apply or not rows:
                continue
            target_conn.execute(
                target_table.insert().values(
                    [{column: row[column] for column in columns} for row in rows]
                )
            )
        if apply:
            target_conn.commit()
            _reset_sequences(target_conn, target_meta, counts)
            _backfill_assessments(target_conn, target_meta)
            target_conn.commit()
    return counts


def _backfill_assessments(connection, metadata: MetaData) -> None:
    """Create conservative v2 payloads for legacy observations without one."""
    if "agronomic_assessment" not in metadata.tables:
        return
    existing = connection.execute(
        text("SELECT count(*) FROM agronomic_assessment")
    ).scalar_one()
    if existing:
        return
    rows = connection.execute(
        text(
            "SELECT o.id, o.tree_id, s.standing_water, s.leaf_wilt, "
            "s.soil_surface_condition, s.soil_compaction, s.mulch_present, "
            "p.present AS pest_present, d.present AS disease_present, "
            "w.level AS weed_level, g.height_cm, g.stem_diameter_cm, "
            "g.canopy_width_cm "
            "FROM observation_session o "
            "LEFT JOIN soil_observation s ON s.observation_id = o.id "
            "LEFT JOIN LATERAL (SELECT present FROM pest_observation "
            "WHERE tree_id = o.tree_id ORDER BY recorded_at DESC, id DESC LIMIT 1) p ON true "
            "LEFT JOIN LATERAL (SELECT present FROM disease_observation "
            "WHERE tree_id = o.tree_id ORDER BY recorded_at DESC, id DESC LIMIT 1) d ON true "
            "LEFT JOIN LATERAL (SELECT level FROM weed_observation "
            "WHERE tree_id = o.tree_id ORDER BY recorded_at DESC, id DESC LIMIT 1) w ON true "
            "LEFT JOIN LATERAL (SELECT height_cm, stem_diameter_cm, canopy_width_cm "
            "FROM growth_measurement WHERE tree_id = o.tree_id "
            "ORDER BY recorded_at DESC, id DESC LIMIT 1) g ON true "
            "ORDER BY o.id"
        )
    ).mappings()
    assessment_table = metadata.tables["agronomic_assessment"]
    payloads = []
    for row in rows:
        payload = build_assessment(
            manual={
                "tree_id": row["tree_id"],
                "height_cm": row["height_cm"],
                "stem_diameter_cm": row["stem_diameter_cm"],
                "canopy_width_cm": row["canopy_width_cm"],
                "standing_water": row["standing_water"],
                "leaf_wilt": row["leaf_wilt"],
                "pest_present": row["pest_present"],
                "disease_present": row["disease_present"],
                "weed_level": row["weed_level"],
                "soil_surface_condition": row["soil_surface_condition"],
                "soil_compaction": row["soil_compaction"],
                "mulch_present": row["mulch_present"],
            }
        )
        payloads.append(
            {
                "observation_id": row["id"],
                "analysis_type": payload["analysis_type"],
                "analysis_version": payload["analysis_version"],
                "overall_status": payload["agronomic_assessment"][
                    "overall_visual_status"
                ],
                "confirmation_required": True,
                "payload_json": json.dumps(
                    payload, ensure_ascii=False, sort_keys=True
                ),
                "created_at": datetime.now(timezone.utc),
            }
        )
    if payloads:
        connection.execute(assessment_table.insert().values(payloads))


def upgrade_assessment_payloads(connection) -> int:
    """Add the v2 parameter table to assessments created by older releases."""
    rows = connection.execute(
        text(
            "SELECT id, payload_json FROM agronomic_assessment "
            "WHERE payload_json NOT LIKE '%extracted_parameters%' "
            "OR payload_json NOT LIKE '%architecture_parameters%' "
            "OR payload_json NOT LIKE '%soil_parameters%' "
            "OR payload_json NOT LIKE '%weed_parameters%' "
            "OR payload_json NOT LIKE '%microclimate_parameters%' "
            "OR payload_json NOT LIKE '%pest_disease_screening%' "
            "OR payload_json NOT LIKE '%agronomic_risks%' "
            "OR payload_json NOT LIKE '%plant_status_indices%'"
        )
    ).mappings()
    updated = 0
    for row in rows:
        payload = json.loads(row["payload_json"])
        template = build_assessment()
        payload.setdefault("extracted_parameters", template["extracted_parameters"])
        payload.setdefault("architecture_parameters", template["architecture_parameters"])
        payload.setdefault("soil_parameters", template["soil_parameters"])
        payload.setdefault("weed_parameters", template["weed_parameters"])
        payload.setdefault(
            "microclimate_parameters", template["microclimate_parameters"]
        )
        payload.setdefault(
            "pest_disease_screening", template["pest_disease_screening"]
        )
        payload.setdefault("agronomic_risks", template["agronomic_risks"])
        payload.setdefault(
            "plant_status_indices", template["plant_status_indices"]
        )
        connection.execute(
            text(
                "UPDATE agronomic_assessment SET payload_json = :payload "
                "WHERE id = :id"
            ),
            {
                "id": row["id"],
                "payload": json.dumps(payload, ensure_ascii=False, sort_keys=True),
            },
        )
        updated += 1
    return updated


def _reset_sequences(connection, metadata: MetaData, counts: dict[str, int]) -> None:
    for name, count in counts.items():
        if count == 0:
            continue
        table = metadata.tables[name]
        primary_key = next(iter(table.primary_key.columns), None)
        if primary_key is None:
            continue
        sequence = connection.execute(
            text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
            {"table_name": name, "column_name": primary_key.name},
        ).scalar_one_or_none()
        if sequence is None:
            continue
        maximum = connection.execute(
            text(f'SELECT MAX("{primary_key.name}") FROM "{name}"')
        ).scalar_one()
        connection.execute(
            text("SELECT setval(:sequence_name, :value, true)"),
            {"sequence_name": sequence, "value": maximum},
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=os.getenv(
            "SOURCE_DATABASE_URL", "sqlite:///instance/ai_analis_rambutan.sqlite3"
        ),
    )
    parser.add_argument("--target", default=os.getenv("DATABASE_URL"))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write rows. Without this flag, only validate and count source rows.",
    )
    args = parser.parse_args()
    if not args.target:
        parser.error("--target or DATABASE_URL is required")
    counts = migrate(args.source, args.target, apply=args.apply)
    mode = "copied" if args.apply else "validated"
    print(f"Migration {mode}: {sum(counts.values())} rows")
    for table, count in counts.items():
        print(f"{table}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
