from typing import List

from sortedcontainers import SortedKeyList

from .models import BoundingBox, Equipment, Assignment, PlacementResult


def _compute_cost(priority: int, ar_diff: float) -> float:
    """Cost = priority^4 * (aspect-ratio mismatch)^2."""
    return (priority ** 4) * (ar_diff ** 2)


def assign_equipment(
    tags: List[BoundingBox],
    equipment: List[Equipment],
    floorplan_path: str = "",
) -> PlacementResult:
    """
    Greedy assignment: highest-priority equipment gets first pick of the
    best aspect-ratio-matched tag via binary search on a SortedKeyList.
    """
    if not tags or not equipment:
        return PlacementResult(floorplan_path=floorplan_path)

    # Sort equipment by priority desc, then by max(ar, 1/ar) desc for
    # tie-breaking so extreme-shaped equipment picks first within a tier
    sorted_eq = sorted(
        equipment,
        key=lambda e: (-e.priority, -max(e.width / e.height, e.height / e.width)),
    )

    # Maintain available tags in a sorted structure keyed by aspect ratio
    # for O(log n) closest-AR lookup via binary search
    available = SortedKeyList(range(len(tags)), key=lambda i: tags[i].aspect_ratio)

    assignments: list[Assignment] = []

    for eq in sorted_eq:
        if not available:
            break

        eq_ar = eq.width / eq.height
        eq_ar_rot = eq.height / eq.width

        best_tag_idx = None
        best_rotated = False
        best_diff = float("inf")

        # Check both orientations, binary search for closest AR each time
        for ar, rotated in [(eq_ar, False), (eq_ar_rot, True)]:
            pos = available.bisect_key_left(ar)
            # Examine the two nearest neighbours (left and right of insertion point)
            for p in (pos - 1, pos):
                if 0 <= p < len(available):
                    idx = available[p]
                    diff = abs(tags[idx].aspect_ratio - ar)
                    if diff < best_diff:
                        best_diff = diff
                        best_tag_idx = idx
                        best_rotated = rotated

        tag = tags[best_tag_idx]
        cost = _compute_cost(eq.priority, best_diff)

        assignments.append(Assignment(
            tag=tag,
            equipment=eq,
            cost=cost,
            rotated=best_rotated,
        ))
        available.remove(best_tag_idx)

    return PlacementResult(floorplan_path=floorplan_path, assignments=assignments)
