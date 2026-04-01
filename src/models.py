"""
Data models for the equipment placement system.
These are provided for you — do not modify.
"""

from dataclasses import dataclass, field


@dataclass
class Rect:
    """A rectangle detected in a floor plan image."""
    x: int
    y: int
    width: int
    height: int

    @property
    def area(self) -> int:
        return self.width * self.height

    def __repr__(self) -> str:
        return f"Rect(x={self.x}, y={self.y}, w={self.width}, h={self.height})"


@dataclass
class Equipment:
    """A piece of equipment with physical dimensions and a priority level."""
    id: str
    name: str
    width: float
    height: float
    priority: int  # 1–5

    def __repr__(self) -> str:
        return f"Equipment(id={self.id}, w={self.width}, h={self.height}, pri={self.priority})"


@dataclass
class Assignment:
    """Maps one equipment item to one detected rectangle."""
    tag: Rect
    equipment: Equipment
    cost: float
    rotated: bool

    def __repr__(self) -> str:
        r = "R" if self.rotated else ""
        return f"Assignment({self.equipment.id}{r} → tag@({self.tag.x},{self.tag.y}), cost={self.cost:.6f})"


@dataclass
class PlacementResult:
    """Result of processing a single floor plan."""
    floorplan_path: str
    assignments: list = field(default_factory=list)  # List[Assignment]

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
