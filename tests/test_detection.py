"""
Tests for Part 1: Tag Detection

Run with: pytest tests/test_detection.py -v
"""

import pytest
from pathlib import Path
from src.loader import list_floorplans, load_ground_truth
from src.detection import detect_tags
from src.models import BoundingBox


@pytest.fixture
def ground_truth():
    return load_ground_truth()


@pytest.fixture
def first_floorplan():
    plans = list_floorplans()
    assert len(plans) > 0, "No floor plans found in data/floorplans/"
    return plans[0]


class TestDetectTags:

    def test_returns_list_of_bounding_boxes(self, first_floorplan):
        result = detect_tags(first_floorplan)
        assert isinstance(result, list)
        assert len(result) > 0, "Should detect at least one tag"
        assert all(isinstance(bb, BoundingBox) for bb in result)

    def test_bounding_boxes_have_positive_dimensions(self, first_floorplan):
        result = detect_tags(first_floorplan)
        for bb in result:
            assert bb.width > 0 and bb.height > 0, f"Bad dimensions: {bb}"
            assert bb.x >= 0 and bb.y >= 0, f"Negative position: {bb}"

    def test_detects_correct_count(self, first_floorplan, ground_truth):
        filename = Path(first_floorplan).name
        expected = ground_truth[filename]["num_tags"]
        result = detect_tags(first_floorplan)
        assert abs(len(result) - expected) <= 2, (
            f"Expected ~{expected} tags, detected {len(result)} in {filename}"
        )

    def test_aspect_ratios_are_reasonable(self, first_floorplan):
        result = detect_tags(first_floorplan)
        for bb in result:
            assert 0.1 < bb.aspect_ratio < 15.0, f"Unusual AR {bb.aspect_ratio:.2f}"

    def test_all_floorplans_detectable(self, ground_truth):
        plans = list_floorplans()
        for plan_path in plans:
            result = detect_tags(plan_path)
            filename = Path(plan_path).name
            expected = ground_truth[filename]["num_tags"]
            assert len(result) >= expected - 2, (
                f"{filename}: expected ~{expected}, got {len(result)}"
            )
