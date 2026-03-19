"""
Tests for Part 3: Orchestration, Visualization & Analysis

Run with: pytest tests/test_integration.py -v
"""

import os
import tempfile
import pytest
import cv2
import numpy as np

from src.main import (
    find_best_floorplan,
    find_all_results,
    cost_to_color,
    render_placement,
    render_top_n,
)
from src.models import PlacementResult


# ---------------------------------------------------------------------------
# 3a. Orchestration
# ---------------------------------------------------------------------------

class TestOrchestration:

    def test_find_all_results_returns_list(self):
        results = find_all_results()
        assert isinstance(results, list)
        assert len(results) == 20, f"Expected 20 results, got {len(results)}"

    def test_results_sorted_by_mean_cost(self):
        results = find_all_results()
        for i in range(len(results) - 1):
            assert results[i].mean_cost <= results[i + 1].mean_cost, (
                f"Not sorted: index {i} cost={results[i].mean_cost:.6f} > "
                f"index {i+1} cost={results[i+1].mean_cost:.6f}"
            )

    def test_find_best_is_first_result(self):
        best = find_best_floorplan()
        all_results = find_all_results()
        assert best is not None
        assert best.mean_cost == all_results[0].mean_cost

    def test_all_results_have_assignments(self):
        results = find_all_results()
        for r in results:
            assert r.num_assignments > 0, f"{r.floorplan_path} has 0 assignments"

    def test_no_duplicate_equipment_across_single_plan(self):
        """Each plan should have unique equipment assignments."""
        results = find_all_results()
        for r in results:
            ids = [a.equipment.id for a in r.assignments]
            assert len(ids) == len(set(ids)), (
                f"Duplicate equipment in {r.floorplan_path}"
            )


# ---------------------------------------------------------------------------
# 3b. Color gradient
# ---------------------------------------------------------------------------

class TestCostToColor:

    def test_zero_cost_is_green(self):
        color = cost_to_color(0.0, 1.0)
        assert isinstance(color, tuple) and len(color) == 3
        b, g, r = color
        assert g >= 200, f"Green channel too low: {g}"
        assert r <= 55, f"Red channel too high for zero cost: {r}"

    def test_max_cost_is_red(self):
        b, g, r = cost_to_color(1.0, 1.0)
        assert r >= 200, f"Red channel too low: {r}"
        assert g <= 55, f"Green channel too high for max cost: {g}"

    def test_mid_cost_is_yellowish(self):
        b, g, r = cost_to_color(0.5, 1.0)
        assert g >= 150, f"Green too low for mid cost: {g}"
        assert r >= 150, f"Red too low for mid cost: {r}"

    def test_clamps_above_max(self):
        b, g, r = cost_to_color(5.0, 1.0)
        assert r >= 200

    def test_clamps_below_zero(self):
        b, g, r = cost_to_color(-1.0, 1.0)
        assert g >= 200

    def test_returns_ints(self):
        color = cost_to_color(0.3, 1.0)
        assert all(isinstance(c, int) for c in color), (
            f"Color values must be ints, got {[type(c).__name__ for c in color]}"
        )


# ---------------------------------------------------------------------------
# 3c. Rendering
# ---------------------------------------------------------------------------

class TestRenderPlacement:

    @pytest.fixture
    def sample_result(self):
        results = find_all_results()
        return results[0]

    def test_creates_output_file(self, sample_result):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test_render.png")
            returned = render_placement(sample_result, out_path)
            assert os.path.exists(out_path), f"Output file not created"
            assert returned == out_path

    def test_output_is_valid_image(self, sample_result):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test_render.png")
            render_placement(sample_result, out_path)
            img = cv2.imread(out_path)
            assert img is not None, "Output is not a valid image"
            assert img.shape[0] > 0 and img.shape[1] > 0

    def test_output_differs_from_original(self, sample_result):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test_render.png")
            render_placement(sample_result, out_path)
            original = cv2.imread(sample_result.floorplan_path)
            annotated = cv2.imread(out_path)
            assert original.shape == annotated.shape, "Dimensions changed"
            diff = cv2.absdiff(original, annotated)
            assert diff.sum() > 0, "Annotated image identical to original"

    def test_has_visible_annotations(self, sample_result):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test_render.png")
            render_placement(sample_result, out_path)
            original = cv2.imread(sample_result.floorplan_path)
            annotated = cv2.imread(out_path)
            diff = cv2.absdiff(original, annotated).astype(np.float32)
            changed_pixels = np.sum(diff > 10)
            assert changed_pixels > 500, (
                f"Only {changed_pixels} pixels changed — not enough annotations"
            )


class TestRenderTopN:

    def test_renders_five_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = render_top_n(n=5, output_dir=tmpdir)
            assert len(paths) == 5, f"Expected 5 files, got {len(paths)}"
            for p in paths:
                assert os.path.exists(p), f"Missing: {p}"

    def test_filenames_contain_rank(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = render_top_n(n=5, output_dir=tmpdir)
            filenames = [os.path.basename(p) for p in paths]
            for i, fn in enumerate(filenames, start=1):
                assert f"rank_{i}" in fn.lower(), (
                    f"Filename '{fn}' should contain 'rank_{i}'"
                )

    def test_renders_arbitrary_n(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = render_top_n(n=3, output_dir=tmpdir)
            assert len(paths) == 3

    def test_all_outputs_are_valid_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = render_top_n(n=5, output_dir=tmpdir)
            for p in paths:
                img = cv2.imread(p)
                assert img is not None, f"Not a valid image: {p}"
