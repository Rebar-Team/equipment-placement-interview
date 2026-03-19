"""
Part 1: Floor Plan Tag Detection
=================================

Implement the detect_tags() function below.

The floor plan PNGs contain green rectangular "tags" drawn on a
background with walls, grid lines, and room labels. Your job is to
detect these green rectangles and return their bounding boxes.

Expected time: ~12 minutes
"""

from typing import List
from .models import BoundingBox


def detect_tags(image_path: str) -> List[BoundingBox]:
    """
    Detect green rectangular tags in a floor plan image.

    Args:
        image_path: Path to a floor plan PNG file.

    Returns:
        List of BoundingBox objects, one per detected tag.
        Filter out noise — real tags have significant area.

    TODO: Implement this function.
    """
    raise NotImplementedError("Implement detect_tags()")
