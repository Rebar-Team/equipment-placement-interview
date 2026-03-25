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

# Color ranges in BGR format (OpenCV uses BGR, not RGB)
# Bright green fill: approximately RGB (0, 200, 0) -> BGR (0, 200, 0)
# Dark green border: approximately RGB (0, 128, 0) -> BGR (0, 128, 0)

# Generous HSV ranges for detecting green
# Hue: green is around 60 in OpenCV's 0-179 scale (120 degrees / 2)
GREEN_HSV_LOWER = np.array([35, 100, 100])   # Lower bound: H=35, S=100, V=100
GREEN_HSV_UPPER = np.array([85, 255, 255])   # Upper bound: H=85, S=255, V=255

# Dark green border HSV range (lower value/saturation)
DARK_GREEN_HSV_LOWER = np.array([35, 50, 50])
DARK_GREEN_HSV_UPPER = np.array([85, 255, 200])

# Minimum area threshold to filter out noise
MIN_TAG_AREA = 500


def detect_tags(image_path: str) -> List[BoundingBox]:
    """
    Detect green rectangular tags in a floor plan image.

    Args:
        image_path: Path to a floor plan PNG file.

    Returns:
        List of BoundingBox objects, one per detected tag.
        Filter out noise — real tags have significant area.

    Detection approach:
    1. Convert image to HSV color space
    2. Create mask for green colors (both bright fill and dark border)
    3. Find contours in the mask
    4. Validate contours have darker green border
    5. Return bounding boxes for valid tags
    """
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Convert BGR to HSV for better color detection
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Create mask for all green colors (both bright and dark green)
    mask_bright = cv2.inRange(hsv, GREEN_HSV_LOWER, GREEN_HSV_UPPER)
    mask_dark = cv2.inRange(hsv, DARK_GREEN_HSV_LOWER, DARK_GREEN_HSV_UPPER)
    
    # Combine masks to catch both the fill and border
    combined_mask = cv2.bitwise_or(mask_bright, mask_dark)
    
    # Apply morphological operations to clean up the mask
    kernel = np.ones((3, 3), np.uint8)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bounding_boxes = []
    
    for contour in contours:
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        
        # Filter by minimum area
        if area < MIN_TAG_AREA:
            continue
        
        # Validate that the contour has a darker green border
        if not _has_dark_green_border(hsv, x, y, w, h):
            continue
        
        bounding_boxes.append(BoundingBox(x=x, y=y, width=w, height=h))
    
    return bounding_boxes


def _extract_border_region(hsv: np.ndarray, x: int, y: int, w: int, h: int, 
                           border_width: int = 3) -> np.ndarray:
    """Extract the border pixels from a bounding box region."""
    img_h, img_w = hsv.shape[:2]
    
    # Clamp coordinates to image bounds
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(img_w, x + w), min(img_h, y + h)
    bw = border_width
    
    # Collect border slices: top, bottom, left, right
    slices = [
        hsv[y1:y1+bw, x1:x2],           # top
        hsv[max(y1, y2-bw):y2, x1:x2],  # bottom
        hsv[y1:y2, x1:x1+bw],           # left
        hsv[y1:y2, max(x1, x2-bw):x2],  # right
    ]
    
    # Filter empty slices and concatenate
    valid = [s.reshape(-1, 3) for s in slices if s.size > 0]
    return np.vstack(valid) if valid else np.array([]).reshape(0, 3)


def _has_dark_green_border(hsv: np.ndarray, x: int, y: int, w: int, h: int) -> bool:
    """Check if at least 10% of border pixels are dark green."""
    border_pixels = _extract_border_region(hsv, x, y, w, h)
    if len(border_pixels) == 0:
        return False
    
    # Reshape to (N, 1, 3) so cv2.inRange treats it as an image
    border_img = border_pixels.reshape(-1, 1, 3)
    mask = cv2.inRange(border_img, DARK_GREEN_HSV_LOWER, DARK_GREEN_HSV_UPPER)
    return np.count_nonzero(mask) / len(border_pixels) > 0.1
