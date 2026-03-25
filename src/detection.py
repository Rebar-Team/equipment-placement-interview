"""
Part 1: Floor Plan Tag Detection
=================================

Detect bright green rectangular tags in floor plan images using HSV color
thresholding and contour analysis. The green tags have a distinctive
saturated green color (H~60, S=255, V=160-200 in OpenCV HSV space) that
separates them from walls, grid lines, and room labels.

Approach:
  1. Convert to HSV and threshold for bright green
  2. Apply morphological closing to fill small gaps
  3. Find contours and filter by minimum area to reject noise
  4. Return axis-aligned bounding boxes for each surviving contour
"""

from typing import List
import cv2
import numpy as np
from .models import BoundingBox

# HSV range for the bright green tags (OpenCV H range is 0-179)
GREEN_LOWER = np.array([35, 100, 100])
GREEN_UPPER = np.array([85, 255, 255])

# Minimum area in pixels to be considered a real tag (rejects small noise)
MIN_TAG_AREA = 800


def detect_tags(image_path: str) -> List[BoundingBox]:
    """
    Detect green rectangular tags in a floor plan image.

    Args:
        image_path: Path to a floor plan PNG file.

    Returns:
        List of BoundingBox objects, one per detected tag.
    """
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Threshold for bright green pixels
    mask = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER)

    # Morphological closing to fill small holes within tags
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Find contours of green regions
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h >= MIN_TAG_AREA:
            boxes.append(BoundingBox(x=x, y=y, width=w, height=h))

    return boxes
