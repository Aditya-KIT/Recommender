import json
from pathlib import Path
from typing import Any, Dict, List

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "shl_catalog.json"


def load_catalog() -> List[Dict[str, Any]]:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Catalog not found: {CATALOG_PATH}")
    with CATALOG_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def catalog_urls(catalog: List[Dict[str, Any]]) -> set[str]:
    return {item["url"] for item in catalog if item.get("url")}
