"""
Tests for Part 2: Equipment Placement Algorithm

These tests validate PROPERTIES of a correct solution without
prescribing a specific algorithm. Both greedy and optimal approaches
should pass all tests.

Run with: pytest tests/test_placement.py -v
"""

import pytest
import time
from src.models import BoundingBox, Equipment, PlacementResult, Assignment
from src.placement import assign_equipment
from src.loader import load_equipment


@pytest.fixture
def equipment():
    return load_equipment()


@pytest.fixture
def sample_tags():
    """A small set of tags with varied aspect ratios."""
    return [
        BoundingBox(x=0, y=0, width=100, height=100),   # AR = 1.0
        BoundingBox(x=0, y=0, width=200, height=100),   # AR = 2.0
        BoundingBox(x=0, y=0, width=50, height=100),    # AR = 0.5
    ]


class TestBasicProperties:
    """Structural correctness — any valid solution must satisfy these."""

    def test_returns_placement_result(self, sample_tags, equipment):
        result = assign_equipment(sample_tags, equipment)
        assert isinstance(result, PlacementResult)

    def test_assigns_one_equipment_per_tag(self, sample_tags, equipment):
        result = assign_equipment(sample_tags, equipment)
        assert len(result.assignments) == len(sample_tags)

    def test_no_duplicate_equipment(self, sample_tags, equipment):
        result = assign_equipment(sample_tags, equipment)
        assigned_ids = [a.equipment.id for a in result.assignments]
        assert len(assigned_ids) == len(set(assigned_ids)), "Duplicate equipment assigned"

    def test_assignments_have_valid_structure(self, sample_tags, equipment):
        result = assign_equipment(sample_tags, equipment)
        for a in result.assignments:
            assert isinstance(a, Assignment)
            assert isinstance(a.tag, BoundingBox)
            assert isinstance(a.equipment, Equipment)
            assert isinstance(a.cost, (int, float))
            assert isinstance(a.rotated, bool)

    def test_costs_are_non_negative(self, sample_tags, equipment):
        result = assign_equipment(sample_tags, equipment)
        for a in result.assignments:
            assert a.cost >= 0, f"Negative cost: {a.cost}"

    def test_handles_more_tags_than_equipment(self):
        """When tags outnumber equipment, assign what you can."""
        tags = [BoundingBox(x=0, y=i * 100, width=100, height=100) for i in range(10)]
        eq = [
            Equipment(id="EQ-1", name="A", width=100, height=100, priority=3),
            Equipment(id="EQ-2", name="B", width=200, height=100, priority=2),
        ]
        result = assign_equipment(tags, eq)
        assert result.num_assignments <= len(eq)

    def test_handles_empty_inputs(self, equipment):
        result = assign_equipment([], equipment)
        assert result.num_assignments == 0

        tags = [BoundingBox(x=0, y=0, width=100, height=100)]
        result = assign_equipment(tags, [])
        assert result.num_assignments == 0


class TestRotation:
    """Equipment rotation should be considered when beneficial."""

    def test_rotates_when_clearly_better(self):
        """If rotating gives a perfect match, the algorithm should rotate."""
        # Tag is tall and narrow: AR = 0.5
        tags = [BoundingBox(x=0, y=0, width=50, height=100)]

        # Equipment is wide: AR = 2.0 → rotated AR = 0.5 (perfect match!)
        eq = [Equipment(id="ROTME", name="R", width=200, height=100, priority=3)]

        result = assign_equipment(tags, eq)
        assert result.num_assignments == 1
        assert result.assignments[0].rotated is True, (
            "Equipment should be rotated — rotated AR (0.5) matches tag perfectly"
        )

    def test_does_not_rotate_when_unnecessary(self):
        """If the normal orientation is already a good fit, don't rotate."""
        tags = [BoundingBox(x=0, y=0, width=200, height=100)]  # AR = 2.0
        eq = [Equipment(id="NOROT", name="N", width=200, height=100, priority=3)]  # AR = 2.0

        result = assign_equipment(tags, eq)
        assert result.num_assignments == 1
        assert result.assignments[0].rotated is False, (
            "Equipment should NOT be rotated — normal AR already matches"
        )

    def test_rotation_used_in_real_data(self, equipment):
        """Across varied tags, at least some assignments should use rotation."""
        tags = [
            BoundingBox(x=0, y=0, width=50, height=200),   # AR = 0.25
            BoundingBox(x=0, y=0, width=200, height=50),   # AR = 4.0
            BoundingBox(x=0, y=0, width=100, height=300),   # AR = 0.33
            BoundingBox(x=0, y=0, width=300, height=100),   # AR = 3.0
            BoundingBox(x=0, y=0, width=80, height=200),    # AR = 0.4
        ]
        result = assign_equipment(tags, equipment)
        rotated_count = sum(1 for a in result.assignments if a.rotated)
        assert rotated_count > 0, (
            "No rotations used across varied tags — rotation logic may be missing"
        )


class TestPriority:
    """Priority should influence the cost function."""

    def test_priority_affects_cost(self):
        """
        Same geometric mismatch + different priority → different cost.
        This verifies priority is a factor in the cost function.
        """
        # Two tags with identical AR
        tags = [
            BoundingBox(x=0, y=0, width=100, height=80),    # AR = 1.25
            BoundingBox(x=0, y=200, width=100, height=80),   # AR = 1.25
        ]
        # Two equipment with SAME dimensions but DIFFERENT priority
        eq = [
            Equipment(id="HI", name="H", width=130, height=100, priority=5),  # AR = 1.3
            Equipment(id="LO", name="L", width=130, height=100, priority=1),  # AR = 1.3
        ]

        result = assign_equipment(tags, eq)
        assert result.num_assignments == 2

        # Find costs for each equipment
        costs = {a.equipment.id: a.cost for a in result.assignments}
        assert "HI" in costs and "LO" in costs, "Both equipment should be assigned"
        assert costs["HI"] != costs["LO"], (
            f"Same geometric mismatch but costs are equal ({costs['HI']} == {costs['LO']}). "
            f"Priority should affect the cost function."
        )

    def test_high_priority_gets_good_placement(self, equipment):
        """
        High-priority equipment should tend to get lower geometric error
        than low-priority equipment, since the cost function should make
        the optimizer work harder for high-priority items.
        """
        tags = [
            BoundingBox(x=0, y=i * 100, width=50 + i * 30, height=100)
            for i in range(10)
        ]
        result = assign_equipment(tags, equipment)

        # Split assignments by priority and compute average geometric error
        hi_errors, lo_errors = [], []
        for a in result.assignments:
            eq_ar = a.equipment.height / a.equipment.width if a.rotated else a.equipment.width / a.equipment.height
            geo_error = (a.tag.aspect_ratio - eq_ar) ** 2
            if a.equipment.priority >= 4:
                hi_errors.append(geo_error)
            elif a.equipment.priority <= 2:
                lo_errors.append(geo_error)

        # We can't guarantee this in all cases (depends on data distribution),
        # but with 300 equipment and 10 tags, high-priority should be favored
        if hi_errors and lo_errors:
            avg_hi = sum(hi_errors) / len(hi_errors)
            avg_lo = sum(lo_errors) / len(lo_errors)
            # Soft check — just verify high-priority isn't dramatically worse
            assert avg_hi <= avg_lo * 5.0, (
                f"High-priority avg geo error ({avg_hi:.4f}) is much worse than "
                f"low-priority ({avg_lo:.4f}) — priority may not be working"
            )


class TestPerformance:
    """Solution must scale efficiently."""

    def test_handles_large_input(self, equipment):
        """100 tags + 300 equipment should complete in under 5 seconds."""
        large_tags = [
            BoundingBox(x=0, y=0, width=max(20, 30 + i * 3), height=100)
            for i in range(10000)
        ]

        start = time.time()
        result = assign_equipment(large_tags, equipment)
        elapsed = time.time() - start

        assert result is not None
        assert result.num_assignments > 0
        assert elapsed < 5.0, (
            f"Took {elapsed:.2f}s for 100 tags + 300 equipment. Target: < 5s."
        )

    def test_cost_values_are_finite(self, equipment):
        """All costs should be finite numbers."""
        tags = [
            BoundingBox(x=0, y=0, width=100, height=100),
            BoundingBox(x=0, y=0, width=50, height=200),
        ]
        result = assign_equipment(tags, equipment)
        for a in result.assignments:
            assert a.cost != float("inf"), "Cost should not be infinite"
            assert a.cost != float("nan"), "Cost should not be NaN"
            assert a.cost == a.cost, "Cost is NaN (failed self-equality check)"
