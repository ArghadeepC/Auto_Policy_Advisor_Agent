"""Local JSON data access for the capstone version of the Auto Policy Advisor."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_json(filename: str, default: Any = None) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        return [] if default is None else default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data: Any) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def find_first(records: list[dict], **criteria: Any) -> dict | None:
    for row in records:
        if all(str(row.get(k, "")).strip().lower() == str(v).strip().lower() for k, v in criteria.items()):
            return row
    return None
