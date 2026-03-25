"""
Part 3: Orchestration, Visualization & Analysis
=================================================

Implement ALL functions below.

This part ties everything together:
  1. Run detection + placement across all floor plans
  2. Render annotated floor plans for the top results
  3. Produce a summary report

The rendered images should visually prove your algorithm works by
overlaying each assignment on the original floor plan with color-coded
quality indicators.

Expected time: ~15 minutes
"""

import os
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
    Process all floor plans and return results sorted by mean cost.

    Requirements:
      - Load equipment ONCE (shared across all floor plans)
      - Detect tags, assign equipment for each floor plan
      - Sort results by mean_cost ascending

    Returns:
        List of PlacementResult objects, sorted by mean_cost (ascending).
    """
    equipment = load_equipment()
    floorplans = list_floorplans()
    
    results = []
    for floorplan_path in floorplans:
        tags = detect_tags(floorplan_path)
        result = assign_equipment(tags, equipment, floorplan_path)
        results.append(result)
    
    results.sort(key=lambda r: r.mean_cost)
    return results


def find_best_floorplan() -> Optional[PlacementResult]:
    """
    Return the single PlacementResult with the lowest mean cost, or None.
    """
    results = find_all_results()
    if not results:
        return None
    return results[0]


# ---------------------------------------------------------------------------
# 3b. Visualization
# ---------------------------------------------------------------------------

def cost_to_color(cost: float, max_cost: float) -> Tuple[int, int, int]:
    """
    Map a cost value to a BGR color on a green -> yellow -> red gradient.

    - 0 cost           -> pure green  (0, 255, 0)
    - max_cost / 2     -> yellow      (0, 255, 255)
    - max_cost         -> pure red    (0, 0, 255)

    Clamp values outside [0, max_cost]. Return BGR tuple (for OpenCV).
    """
    if max_cost <= 0:
        return (0, 255, 0)
    
    # Clamp cost to [0, max_cost]
    cost = max(0.0, min(cost, max_cost))
    
    # Normalize to [0, 1]
    ratio = cost / max_cost
    
    # Green -> Yellow -> Red gradient
    # [0, 0.5]: green to yellow (increase red, keep green at 255)
    # [0.5, 1]: yellow to red (decrease green, keep red at 255)
    if ratio <= 0.5:
        # Green to yellow: red increases from 0 to 255
        t = ratio * 2  # 0 to 1
        r = int(255 * t)
        g = 255
    else:
        # Yellow to red: green decreases from 255 to 0
        t = (ratio - 0.5) * 2  # 0 to 1
        r = 255
        g = int(255 * (1 - t))
    
    return (0, g, r)  # BGR format


def render_placement(result: PlacementResult, output_path: str) -> str:
    """
    Render an annotated floor plan showing equipment assignments.

    For each assignment, draw on the ORIGINAL floor plan image:
      1. A translucent equipment footprint INSIDE the tag showing the
         equipment's actual proportions (scaled to fit within the tag,
         preserving its aspect ratio). A perfect match fills the tag
         entirely; a poor match shows visible dead space between the
         footprint and the tag boundary. Color the footprint using
         cost_to_color().
      2. A rectangle border around the tag, colored by cost_to_color()
         (thickness: 3px)
      3. Text labels (on top, not translucent) showing:
         - Equipment ID (e.g. "EQ-0042")
         - Priority level (e.g. "P5")
         - Whether equipment was rotated (e.g. "ROT" if rotated)
      4. A summary overlay in the top-left corner showing:
         - Floor plan filename
         - Number of assignments (and how many rotated)
         - Mean cost value

    Args:
        result: A PlacementResult with assignments.
        output_path: Where to save the annotated PNG.

    Returns:
        The output_path.
    """
    image = cv2.imread(result.floorplan_path)
    if image is None:
        raise ValueError(f"Could not read image: {result.floorplan_path}")
    
    overlay = image.copy()
    
    # Find max cost for color scaling
    max_cost = max((a.cost for a in result.assignments), default=1.0)
    if max_cost <= 0:
        max_cost = 1.0
    
    # Count rotated assignments
    num_rotated = sum(1 for a in result.assignments if a.rotated)
    
    for assignment in result.assignments:
        tag = assignment.tag
        eq = assignment.equipment
        color = cost_to_color(assignment.cost, max_cost)
        
        # Get equipment dimensions (apply rotation if needed)
        eq_w, eq_h = (eq.height, eq.width) if assignment.rotated else (eq.width, eq.height)
        
        # Calculate scaled equipment footprint inside the tag
        # Scale to fit within tag while preserving aspect ratio
        scale_x = tag.width / eq_w
        scale_y = tag.height / eq_h
        scale = min(scale_x, scale_y)
        
        footprint_w = int(eq_w * scale)
        footprint_h = int(eq_h * scale)
        
        # Center the footprint inside the tag
        footprint_x = tag.x + (tag.width - footprint_w) // 2
        footprint_y = tag.y + (tag.height - footprint_h) // 2
        
        # Draw translucent equipment footprint
        cv2.rectangle(
            overlay,
            (footprint_x, footprint_y),
            (footprint_x + footprint_w, footprint_y + footprint_h),
            color,
            -1  # filled
        )
        
        # Draw tag border (on overlay for now, will blend later)
        cv2.rectangle(
            overlay,
            (tag.x, tag.y),
            (tag.x + tag.width, tag.y + tag.height),
            color,
            3
        )
    
    # Blend overlay with original image (translucent effect)
    alpha = 0.4
    image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    
    # Draw non-translucent elements on top
    for assignment in result.assignments:
        tag = assignment.tag
        eq = assignment.equipment
        color = cost_to_color(assignment.cost, max_cost)
        
        # Re-draw tag border (solid, on top)
        cv2.rectangle(
            image,
            (tag.x, tag.y),
            (tag.x + tag.width, tag.y + tag.height),
            color,
            3
        )
        
        # Text labels
        label_y = tag.y - 5
        if label_y < 15:
            label_y = tag.y + tag.height + 15
        
        # Equipment ID
        cv2.putText(
            image,
            eq.id,
            (tag.x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 0, 0),
            1,
            cv2.LINE_AA
        )
        
        # Priority and rotation status
        rot_str = " ROT" if assignment.rotated else ""
        info_str = f"P{eq.priority}{rot_str}"
        cv2.putText(
            image,
            info_str,
            (tag.x, label_y + 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (0, 0, 0),
            1,
            cv2.LINE_AA
        )
    
    # Summary overlay in top-left corner
    floorplan_name = os.path.basename(result.floorplan_path)
    summary_lines = [
        f"File: {floorplan_name}",
        f"Assignments: {result.num_assignments} ({num_rotated} rotated)",
        f"Mean cost: {result.mean_cost:.4f}"
    ]
    
    # Draw semi-transparent background for summary
    padding = 10
    line_height = 20
    box_height = len(summary_lines) * line_height + padding * 2
    box_width = 280
    
    summary_overlay = image.copy()
    cv2.rectangle(
        summary_overlay,
        (0, 0),
        (box_width, box_height),
        (255, 255, 255),
        -1
    )
    image = cv2.addWeighted(summary_overlay, 0.7, image, 0.3, 0)
    
    # Draw summary text
    for i, line in enumerate(summary_lines):
        cv2.putText(
            image,
            line,
            (padding, padding + (i + 1) * line_height - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
            cv2.LINE_AA
        )
    
    # Save the output image
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    cv2.imwrite(output_path, image)
    
    return output_path


def render_top_n(n: int = 5, output_dir: str = "output") -> List[str]:
    """
    Full pipeline: process all floor plans, render the top N by mean cost.

    Steps:
      1. Run find_all_results()
      2. Take the top N (lowest mean cost)
      3. For each, call render_placement() saving to:
         output_dir/rank_1_<floorplan_name>.png
         output_dir/rank_2_<floorplan_name>.png
         ...
      4. Print a summary table to stdout showing rank, floor plan name,
         number of tags, and mean cost.

    Args:
        n: Number of top results to render (default 5).
        output_dir: Directory to write annotated PNGs.

    Returns:
        List of output file paths for the rendered images.
    """
    results = find_all_results()
    top_results = results[:n]
    
    os.makedirs(output_dir, exist_ok=True)
    
    output_paths = []
    
    # Print summary table header
    print(f"\n{'Rank':<6}{'Floor Plan':<25}{'Tags':<8}{'Mean Cost':<12}")
    print("-" * 51)
    
    for rank, result in enumerate(top_results, start=1):
        floorplan_name = os.path.basename(result.floorplan_path)
        # Remove .png extension for cleaner filename
        name_without_ext = os.path.splitext(floorplan_name)[0]
        
        output_filename = f"rank_{rank}_{name_without_ext}.png"
        output_path = os.path.join(output_dir, output_filename)
        
        render_placement(result, output_path)
        output_paths.append(output_path)
        
        # Print summary row
        print(f"{rank:<6}{floorplan_name:<25}{result.num_assignments:<8}{result.mean_cost:<12.6f}")
    
    print()
    
    return output_paths
