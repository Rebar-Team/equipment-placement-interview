"""
Part 2: Equipment Placement Optimization
==========================================

Assign equipment to tags using the Hungarian algorithm (scipy) to find
the globally optimal assignment that minimizes total weighted cost.

Cost function design:
  cost(equipment, tag) = geometric_error * priority_weight

  - geometric_error: squared log-ratio of aspect ratios between equipment
    (possibly rotated) and tag. Log-ratio is symmetric — a 2:1 mismatch
    costs the same whether the equipment is wider or taller than the tag.

  - priority_weight: 1 / priority. Higher-priority equipment (priority 5)
    gets a lower multiplier (0.2) so the optimizer works harder to give
    it a good geometric fit. Lower-priority items (priority 1) tolerate
    more mismatch (weight 1.0).

  For each (equipment, tag) pair we consider both orientations and pick
  the one with lower geometric error. The cost matrix is then solved
  optimally via scipy.optimize.linear_sum_assignment.

Performance: Building an N×M cost matrix and solving the assignment is
O(min(N,M)^3) with scipy's implementation — well within the 5s budget
for 300 equipment × 100 tags.
"""

import math
from typing import List
from scipy.optimize import linear_sum_assignment
import numpy as np
from .models import BoundingBox, Equipment, Assignment, PlacementResult


def _geometric_error(eq_ar: float, tag_ar: float) -> float:
    """Squared log-ratio of aspect ratios — symmetric and zero when matched."""
    return math.log(eq_ar / tag_ar) ** 2


def _cost_for_pair(eq: Equipment, tag: BoundingBox):
    """
    Compute assignment cost and optimal rotation for an equipment-tag pair.

    Returns (cost, rotated).
    """
    tag_ar = tag.width / tag.height
    normal_ar = eq.width / eq.height
    rotated_ar = eq.height / eq.width

    err_normal = _geometric_error(normal_ar, tag_ar)
    err_rotated = _geometric_error(rotated_ar, tag_ar)

    if err_rotated < err_normal:
        geo_err = err_rotated
        rotated = True
    else:
        geo_err = err_normal
        rotated = False

    priority_weight = 1.0 / eq.priority
    cost = geo_err * priority_weight
    return cost, rotated


def assign_equipment(
    tags: List[BoundingBox],
    equipment: List[Equipment],
    floorplan_path: str = "",
) -> PlacementResult:
    """
    Assign equipment to tags, optimizing for geometric fit and priority.

    Uses the Hungarian algorithm on a cost matrix to find the globally
    optimal one-to-one assignment minimizing total cost.
    """
    if not tags or not equipment:
        return PlacementResult(floorplan_path=floorplan_path)

    n_tags = len(tags)
    n_eq = len(equipment)

    # Build cost matrix: rows = tags, cols = equipment
    # Also track rotation decisions
    cost_matrix = np.zeros((n_tags, n_eq))
    rotation_matrix = np.zeros((n_tags, n_eq), dtype=bool)

    for i, tag in enumerate(tags):
        for j, eq in enumerate(equipment):
            c, r = _cost_for_pair(eq, tag)
            cost_matrix[i, j] = c
            rotation_matrix[i, j] = r

    # Solve assignment (Hungarian algorithm)
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    assignments = []
    for i, j in zip(row_ind, col_ind):
        assignments.append(Assignment(
            tag=tags[i],
            equipment=equipment[j],
            cost=cost_matrix[i, j],
            rotated=bool(rotation_matrix[i, j]),
        ))

    return PlacementResult(floorplan_path=floorplan_path, assignments=assignments)
