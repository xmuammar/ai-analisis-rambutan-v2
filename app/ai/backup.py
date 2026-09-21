import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BACKUP_FORMAT = "AiAnalisRambutan.JSON.v2"


def build_backup(data: dict) -> dict:
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return {
        "backup_format": BACKUP_FORMAT,
        "schema_version": 2,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
        "checksum_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def validate_backup(payload: dict) -> tuple[bool, str]:
    if payload.get("backup_format") not in {"AiAnalisRambutan.JSON.v1", BACKUP_FORMAT}:
        return False, "Format backup tidak didukung."
    data = payload.get("data")
    if not isinstance(data, dict):
        return False, "Data backup tidak valid."
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    expected = hashlib.sha256(encoded).hexdigest()
    if payload.get("checksum_sha256") != expected:
        return False, "Checksum backup tidak cocok."
    return True, "Backup valid."


def read_backup(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    valid, message = validate_backup(payload)
    if not valid:
        raise ValueError(message)
    return payload
