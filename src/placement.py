"""
Part 2: Equipment Placement Optimization
==========================================

Implement the assign_equipment() function below.

Given a list of detected tags (placement zones) and a catalog of
equipment, determine the optimal assignment of equipment to zones.
"""

from typing import List, Tuple
import bisect
from .models import BoundingBox, Equipment, Assignment, PlacementResult

# Cost function weights
ASPECT_RATIO_WEIGHT = 0.5
PRIORITY_WEIGHT = 0.5

# Binary search tolerance for aspect ratio matching
ASPECT_RATIO_TOLERANCE = 0.5


def normalized_aspect_ratio(width: float, height: float) -> float:
    """Normalize aspect ratio to max/min so rotation doesn't affect sorting."""
    return max(width, height) / min(width, height)


def compute_aspect_ratio_cost(tag: BoundingBox, eq: Equipment, rotated: bool) -> float:
    """Compute MSE between tag and equipment aspect ratios."""
    eq_w, eq_h = (eq.height, eq.width) if rotated else (eq.width, eq.height)
    tag_ar = tag.width / tag.height
    eq_ar = eq_w / eq_h
    return (tag_ar - eq_ar) ** 2


def compute_priority_cost(eq: Equipment) -> float:
    """Lower cost for higher priority (priority 5 -> cost 0, priority 1 -> cost 0.8)."""
    return (5 - eq.priority) / 5.0


def compute_cost(tag: BoundingBox, eq: Equipment, rotated: bool) -> float:
    """Combined cost function with aspect ratio and priority."""
    ar_cost = compute_aspect_ratio_cost(tag, eq, rotated)
    pri_cost = compute_priority_cost(eq)
    return ASPECT_RATIO_WEIGHT * ar_cost + PRIORITY_WEIGHT * pri_cost


def should_rotate(tag: BoundingBox, eq: Equipment) -> bool:
    """Decide if rotation improves the fit."""
    cost_normal = compute_aspect_ratio_cost(tag, eq, rotated=False)
    cost_rotated = compute_aspect_ratio_cost(tag, eq, rotated=True)
    return cost_rotated < cost_normal


def assign_equipment(
    tags: List[BoundingBox],
    equipment: List[Equipment],
    floorplan_path: str = "",
) -> PlacementResult:
    """
    Assign equipment to tags, optimizing for geometric fit and priority.
    
    Algorithm:
    1. Sort equipment by normalized aspect ratio
    2. For each tag, binary search to find equipment with similar aspect ratio
    3. Within the search range, pick the highest priority equipment
    """
    if not tags or not equipment:
        return PlacementResult(floorplan_path=floorplan_path, assignments=[])

    # Sort equipment by normalized aspect ratio
    sorted_equipment = sorted(
        equipment,
        key=lambda eq: normalized_aspect_ratio(eq.width, eq.height)
    )
    sorted_ars = [normalized_aspect_ratio(eq.width, eq.height) for eq in sorted_equipment]

    used_equipment_ids = set()
    assignments = []

    for tag in tags:
        tag_ar = normalized_aspect_ratio(tag.width, tag.height)

        # Binary search for the range of equipment with similar aspect ratio
        lo = bisect.bisect_left(sorted_ars, tag_ar - ASPECT_RATIO_TOLERANCE)
        hi = bisect.bisect_right(sorted_ars, tag_ar + ASPECT_RATIO_TOLERANCE)

        # Find best equipment in range (highest priority, then lowest AR cost)
        best_eq = None
        best_cost = float('inf')
        best_rotated = False

        # Search within the tolerance range
        for i in range(lo, hi):
            eq = sorted_equipment[i]
            if eq.id in used_equipment_ids:
                continue

            rotated = should_rotate(tag, eq)
            cost = compute_cost(tag, eq, rotated)

            if cost < best_cost:
                best_cost = cost
                best_eq = eq
                best_rotated = rotated

        # If no equipment found in range, search all remaining equipment
        if best_eq is None:
            for eq in sorted_equipment:
                if eq.id in used_equipment_ids:
                    continue

                rotated = should_rotate(tag, eq)
                cost = compute_cost(tag, eq, rotated)

                if cost < best_cost:
                    best_cost = cost
                    best_eq = eq
                    best_rotated = rotated

        if best_eq is not None:
            used_equipment_ids.add(best_eq.id)
            assignments.append(Assignment(
                tag=tag,
                equipment=best_eq,
                cost=best_cost,
                rotated=best_rotated
            ))

    return PlacementResult(floorplan_path=floorplan_path, assignments=assignments)
