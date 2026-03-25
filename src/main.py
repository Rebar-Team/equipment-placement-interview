"""
Part 3: Orchestration, Visualization & Analysis
=================================================

Ties together detection and placement, then renders annotated floor plans
with color-coded cost indicators and equipment labels.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from .models import PlacementResult
from .loader import load_equipment, list_floorplans
from .detection import detect_tags
from .placement import assign_equipment


# ---------------------------------------------------------------------------
# 3a. Orchestration
# ---------------------------------------------------------------------------

def find_all_results() -> List[PlacementResult]:
    """
    Process all floor plans and return results sorted by mean cost ascending.
    """
    equipment = load_equipment()
    floorplans = list_floorplans()
    results = []
    for fp in floorplans:
        tags = detect_tags(fp)
        result = assign_equipment(tags, equipment, floorplan_path=fp)
        results.append(result)
    results.sort(key=lambda r: r.mean_cost)
    return results


def find_best_floorplan() -> Optional[PlacementResult]:
    """Return the single PlacementResult with the lowest mean cost, or None."""
    results = find_all_results()
    return results[0] if results else None


# ---------------------------------------------------------------------------
# 3b. Visualization
# ---------------------------------------------------------------------------

def cost_to_color(cost: float, max_cost: float) -> Tuple[int, int, int]:
    """
    Map a cost value to a BGR color on a green -> yellow -> red gradient.

    0          -> green  (0, 255, 0)
    max_cost/2 -> yellow (0, 255, 255)
    max_cost   -> red    (0, 0, 255)
    """
    if max_cost <= 0:
        return (0, 255, 0)

    t = max(0.0, min(1.0, cost / max_cost))

    if t <= 0.5:
        # Green to yellow: increase red channel
        ratio = t / 0.5
        g = 255
        r = int(255 * ratio)
    else:
        # Yellow to red: decrease green channel
        ratio = (t - 0.5) / 0.5
        r = 255
        g = int(255 * (1.0 - ratio))

    return (0, g, r)


def render_placement(result: PlacementResult, output_path: str) -> str:
    """
    Render an annotated floor plan showing equipment assignments.
    """
    img = cv2.imread(result.floorplan_path)
    overlay = img.copy()

    max_cost = max((a.cost for a in result.assignments), default=1.0)
    if max_cost <= 0:
        max_cost = 1.0

    for a in result.assignments:
        color = cost_to_color(a.cost, max_cost)
        tx, ty, tw, th = a.tag.x, a.tag.y, a.tag.width, a.tag.height

        # Draw translucent equipment footprint scaled to fit within the tag
        eq_w, eq_h = (a.equipment.height, a.equipment.width) if a.rotated else (a.equipment.width, a.equipment.height)
        eq_ar = eq_w / eq_h
        tag_ar = tw / th

        if eq_ar > tag_ar:
            # Equipment is wider relative to tag — fit to tag width
            fp_w = tw
            fp_h = int(tw / eq_ar)
        else:
            # Equipment is taller relative to tag — fit to tag height
            fp_h = th
            fp_w = int(th * eq_ar)

        # Center the footprint within the tag
        fp_x = tx + (tw - fp_w) // 2
        fp_y = ty + (th - fp_h) // 2
        cv2.rectangle(overlay, (fp_x, fp_y), (fp_x + fp_w, fp_y + fp_h), color, -1)

        # Border around the tag
        cv2.rectangle(overlay, (tx, ty), (tx + tw, ty + th), color, 3)

    # Blend overlay with original for translucency
    img = cv2.addWeighted(overlay, 0.6, img, 0.4, 0)

    # Draw text labels on top (not translucent)
    for a in result.assignments:
        tx, ty = a.tag.x, a.tag.y
        label_y = ty - 5 if ty > 20 else ty + a.tag.height + 15

        rot_str = " ROT" if a.rotated else ""
        label = f"{a.equipment.id} P{a.equipment.priority}{rot_str}"
        cv2.putText(img, label, (tx, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, label, (tx, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)

    # Summary overlay in top-left corner
    fp_name = Path(result.floorplan_path).name
    n_rot = sum(1 for a in result.assignments if a.rotated)
    lines = [
        fp_name,
        f"Assignments: {result.num_assignments} ({n_rot} rotated)",
        f"Mean cost: {result.mean_cost:.6f}",
    ]
    cv2.rectangle(img, (5, 5), (350, 10 + 20 * len(lines)), (0, 0, 0), -1)
    for i, line in enumerate(lines):
        cv2.putText(img, line, (10, 22 + 20 * i),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, img)
    return output_path


def render_top_n(n: int = 5, output_dir: str = "output") -> List[str]:
    """
    Full pipeline: process all floor plans, render the top N by mean cost.
    """
    results = find_all_results()
    top = results[:n]

    os.makedirs(output_dir, exist_ok=True)
    paths = []

    print(f"{'Rank':<6} {'Floor Plan':<25} {'Tags':<6} {'Mean Cost':<12}")
    print("-" * 52)

    for rank, result in enumerate(top, start=1):
        fp_name = Path(result.floorplan_path).stem
        out_path = os.path.join(output_dir, f"rank_{rank}_{fp_name}.png")
        render_placement(result, out_path)
        paths.append(out_path)
        print(f"{rank:<6} {fp_name:<25} {result.num_assignments:<6} {result.mean_cost:<12.6f}")

    return paths
