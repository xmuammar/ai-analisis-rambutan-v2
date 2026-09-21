"""Copy an existing SQLite database into a migrated PostgreSQL database.

The target must already be upgraded with ``flask db upgrade``. The command is
read-only by default; pass ``--apply`` to perform the copy.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from sqlalchemy import MetaData, create_engine, text

from config import normalize_database_url


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
            target_conn.commit()
    return counts


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
