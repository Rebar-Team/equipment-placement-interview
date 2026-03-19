"""
Part 2: Equipment Placement Optimization
==========================================

Implement the assign_equipment() function below.

Given a list of detected tags (placement zones) and a catalog of
equipment, determine the optimal assignment of equipment to zones.

Design considerations:
  - Each piece of equipment has physical dimensions (width × height)
    and a priority level (1–5, where 5 = most critical).
  - Equipment CAN be rotated 90° if it provides a better fit.
  - There are more equipment items than tags — not all equipment
    will be placed.
  - Each equipment item can be assigned to at most one tag.
  - Every tag should receive exactly one equipment assignment
    (if enough equipment is available).
  - Higher-priority equipment should receive better placements.

You must define an appropriate cost function that accounts for BOTH
geometric fit and equipment priority. Populate each Assignment's
`cost` field with your computed cost, and set `rotated` accordingly.

Your solution must handle the full dataset (300 equipment, 5–15 tags
per floor plan, 20 floor plans) efficiently — it should complete all
20 floor plans in under 10 seconds total.

Expected time: ~18 minutes
"""

from typing import List
from .models import BoundingBox, Equipment, Assignment, PlacementResult


def assign_equipment(
    tags: List[BoundingBox],
    equipment: List[Equipment],
    floorplan_path: str = "",
) -> PlacementResult:
    """
    Assign equipment to tags, optimizing for geometric fit and priority.

    Args:
        tags: Detected bounding boxes from a floor plan.
        equipment: Full catalog of available equipment.
        floorplan_path: Path to the floor plan (for result tracking).

    Returns:
        A PlacementResult containing the assignments.

    TODO: Implement this function.
          - Define a cost function
          - Handle equipment rotation
          - Respect priority levels
          - Ensure no duplicate equipment assignments
    """
    raise NotImplementedError("Implement assign_equipment()")
