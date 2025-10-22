from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from src.cluster.models import DeviceMetadata


def get_metadata(db: Session, key: str) -> Optional[str]:
    row = db.query(DeviceMetadata).filter(DeviceMetadata.key == key).first()
    return row.value if row else None


def set_metadata(db: Session, key: str, value: Optional[str]) -> None:
    row = db.query(DeviceMetadata).filter(DeviceMetadata.key == key).first()
    if row:
        row.value = value
    else:
        row = DeviceMetadata(key=key, value=value)
        db.add(row)
    db.commit()


def ensure_default_metadata(db: Session) -> None:
    # Initialize expected keys if missing
    for key, default in (
        ("node_role", None),
        ("cluster_id", None),
        ("ca_cert_pem", None),
        ("ca_key_pem", None),
        ("ca_fingerprint", None),
        ("device_id", None),
        ("device_name", None),
        ("device_model", None),
        ("device_location", None),
        ("device_group", None),
    ):
        if get_metadata(db, key) is None:
            set_metadata(db, key, default)


