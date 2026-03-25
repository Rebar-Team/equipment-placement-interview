"""
Part 3: Orchestration, Visualization & Analysis
=================================================
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
    """Process all floor plans and return results sorted by mean cost ascending."""
    equipment = load_equipment()
    results = []
    for plan_path in list_floorplans():
        tags = detect_tags(plan_path)
        result = assign_equipment(tags, equipment, floorplan_path=plan_path)
        results.append(result)
    results.sort(key=lambda r: r.mean_cost)
    return results


def find_best_floorplan() -> Optional[PlacementResult]:
    """Return the PlacementResult with the lowest mean cost, or None."""
    results = find_all_results()
    return results[0] if results else None


# ---------------------------------------------------------------------------
# 3b. Visualization
# ---------------------------------------------------------------------------

def cost_to_color(cost: float, max_cost: float) -> Tuple[int, int, int]:
    """
    Map cost → BGR color on a green → yellow → red gradient.

    Phase 1 (0 → max/2):      green → yellow  (G=255, R: 0→255)
    Phase 2 (max/2 → max):    yellow → red     (R=255, G: 255→0)
    """
    if max_cost <= 0:
        return (0, 255, 0)
    t = max(0.0, min(cost / max_cost, 1.0))
    if t <= 0.5:
        # green → yellow
        r = int(255 * (t / 0.5))
        g = 255
    else:
        # yellow → red
        r = 255
        g = int(255 * (1.0 - (t - 0.5) / 0.5))
    return (0, g, r)


def render_placement(result: PlacementResult, output_path: str) -> str:
    """Render annotated floor plan with translucent footprints and labels."""
    img = cv2.imread(result.floorplan_path)
    overlay = img.copy()

    max_cost = max((a.cost for a in result.assignments), default=1.0) or 1.0

    for a in result.assignments:
        color = cost_to_color(a.cost, max_cost)
        tx, ty, tw, th = a.tag.x, a.tag.y, a.tag.width, a.tag.height

        # Compute scaled equipment footprint inside the tag
        eq_w = a.equipment.height if a.rotated else a.equipment.width
        eq_h = a.equipment.width if a.rotated else a.equipment.height
        scale = min(tw / eq_w, th / eq_h)
        fw = int(eq_w * scale)
        fh = int(eq_h * scale)
        fx = tx + (tw - fw) // 2
        fy = ty + (th - fh) // 2

        # Translucent footprint
        cv2.rectangle(overlay, (fx, fy), (fx + fw, fy + fh), color, -1)

        # Tag border (on overlay so it blends too)
        cv2.rectangle(overlay, (tx, ty), (tx + tw, ty + th), color, 3)

    # Blend overlay onto original
    cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)

    # Text labels (drawn after blend so they're opaque)
    for a in result.assignments:
        tx, ty = a.tag.x, a.tag.y
        label = a.equipment.id
        pri = f"P{a.equipment.priority}"
        rot = " ROT" if a.rotated else ""
        cv2.putText(img, f"{label} {pri}{rot}", (tx, ty - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1, cv2.LINE_AA)

    # Summary overlay top-left
    filename = Path(result.floorplan_path).name
    rotated_count = sum(1 for a in result.assignments if a.rotated)
    lines = [
        filename,
        f"Assignments: {result.num_assignments} ({rotated_count} rotated)",
        f"Mean cost: {result.mean_cost:.6f}",
    ]
    for i, line in enumerate(lines):
        cv2.putText(img, line, (10, 20 + i * 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(img, line, (10, 20 + i * 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.imwrite(output_path, img)
    return output_path


def render_top_n(n: int = 5, output_dir: str = "output") -> List[str]:
    """Process all floorplans, render top N by mean cost."""
    os.makedirs(output_dir, exist_ok=True)
    results = find_all_results()
    top = results[:n]

    print(f"{'Rank':<6}{'Floor Plan':<25}{'Tags':<6}{'Mean Cost':<12}")
    print("-" * 49)

    paths = []
    for i, result in enumerate(top, start=1):
        name = Path(result.floorplan_path).stem
        out_path = os.path.join(output_dir, f"rank_{i}_{name}.png")
        render_placement(result, out_path)
        paths.append(out_path)
        print(f"{i:<6}{name:<25}{result.num_assignments:<6}{result.mean_cost:<12.6f}")

    return paths
