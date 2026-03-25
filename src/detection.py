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

import cv2
import numpy as np

from .models import BoundingBox

MIN_TAG_AREA = 800


def detect_tags(image_path: str) -> List[BoundingBox]:
    """
    Detect green rectangular tags in a floor plan image.

    Uses HSV color thresholding to isolate bright green pixels,
    then finds contours and returns bounding boxes for sufficiently
    large regions.
    """
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Two HSV ranges to capture both the fill and any slightly different
    # border shade of the green tags
    lower1 = np.array([35, 100, 100])
    upper1 = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower1, upper1)

    # Morphological close to fill small gaps within tags, then open to
    # remove tiny noise specks
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    tags = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h < MIN_TAG_AREA:
            continue
        tags.append(BoundingBox(x=x, y=y, width=w, height=h))

    return tags
