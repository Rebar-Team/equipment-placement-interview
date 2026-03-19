"""
Data loaders for equipment and floor plans.
These are provided for you — do not modify.
"""

import json
from pathlib import Path
from typing import List

from .models import Equipment

DATA_DIR = Path(__file__).parent.parent / "data"
FLOORPLAN_DIR = DATA_DIR / "floorplans"
EQUIPMENT_FILE = DATA_DIR / "equipment.json"


def load_equipment() -> List[Equipment]:
    """
    Load all equipment from equipment.json.

    Returns a list of Equipment objects. The list is in no particular order.
    Each equipment has: id, name, width, height, priority.
    """
    with open(EQUIPMENT_FILE) as f:
        raw = json.load(f)

    return [
        Equipment(
            id=item["id"],
            name=item["name"],
            width=item["width"],
            height=item["height"],
            priority=item["priority"],
        )
        for item in raw
    ]


def list_floorplans() -> List[str]:
    """
    Return sorted list of absolute paths to all floor plan PNGs.
    """
    return sorted(str(p) for p in FLOORPLAN_DIR.glob("*.png"))


def load_ground_truth() -> dict:
    """
    Load ground truth data (for validation/testing).
    Contains the expected number of tags per floor plan.
    """
    truth_path = DATA_DIR / "ground_truth.json"
    with open(truth_path) as f:
        return json.load(f)
