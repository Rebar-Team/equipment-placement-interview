"""
Data models for the equipment placement system.
These are provided for you — do not modify.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class BoundingBox:
    """A detected tag (equipment placement zone) on a floor plan."""
    x: int
    y: int
    width: int
    height: int

    @property
    def aspect_ratio(self) -> float:
        """Width / Height ratio."""
        return self.width / self.height

    @property
    def area(self) -> int:
        return self.width * self.height

    def __repr__(self) -> str:
        return f"BoundingBox(x={self.x}, y={self.y}, w={self.width}, h={self.height}, ar={self.aspect_ratio:.2f})"


@dataclass
class Equipment:
    """A piece of equipment that needs to be placed into a tag zone."""
    id: str
    name: str
    width: float
    height: float
    priority: int  # 1–5, higher = more important to place well

    def __repr__(self) -> str:
        return f"Equipment(id={self.id}, w={self.width}, h={self.height}, pri={self.priority})"


@dataclass
class Assignment:
    """A single equipment → tag assignment."""
    tag: BoundingBox
    equipment: Equipment
    cost: float         # Candidate-defined cost of this assignment
    rotated: bool       # Whether equipment was rotated 90° for this placement

    def __repr__(self) -> str:
        r = "R" if self.rotated else ""
        return f"Assignment({self.equipment.id}{r} → tag@({self.tag.x},{self.tag.y}), cost={self.cost:.6f})"


@dataclass
class PlacementResult:
    """Result of placing equipment into all tags on a single floor plan."""
    floorplan_path: str
    assignments: List[Assignment] = field(default_factory=list)

    @property
    def total_cost(self) -> float:
        return sum(a.cost for a in self.assignments)

    @property
    def mean_cost(self) -> float:
        if not self.assignments:
            return float("inf")
        return self.total_cost / len(self.assignments)

    @property
    def num_assignments(self) -> int:
        return len(self.assignments)

    def __repr__(self) -> str:
        return (
            f"PlacementResult(floorplan={self.floorplan_path}, "
            f"assignments={self.num_assignments}, "
            f"mean_cost={self.mean_cost:.6f})"
        )
