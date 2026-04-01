"""Part 2: Equipment Placement"""

from typing import List
from .models import Rect, Equipment, Assignment, PlacementResult


def assign_equipment(
    tags: List[Rect],
    equipment: List[Equipment],
    floorplan_path: str = "",
) -> PlacementResult:
    """
    Assign equipment to detected zones.

    Args:
        tags: Detected rectangles from a floor plan.
        equipment: Full catalog of available equipment.
        floorplan_path: Path to the floor plan (for result tracking).

    Returns:
        A PlacementResult containing the assignments.

    TODO: Implement this function.
    """
    raise NotImplementedError("Implement assign_equipment()")
