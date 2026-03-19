# Equipment Placement Optimization

## Overview

You're building a system that analyzes industrial floor plans to optimally place equipment. Each floor plan contains green rectangular **tags** — these are zones where equipment will be installed. You have a catalog of **300 equipment items**, each with physical dimensions and a priority level. Your goal is to determine the best assignment of equipment to zones, then **visually prove** your solution works by rendering annotated floor plans.

## Setup

```bash
pip install -r requirements.txt
```

## The Data

**`data/floorplans/`** — 20 PNG floor plan images (1200×900 px). Each contains 5–15 bright green rectangles representing equipment placement zones (tags).

**`data/equipment.json`** — 300 equipment entries. Each has:

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier (e.g. "EQ-0042") |
| `name` | string | Equipment name |
| `width` | float | Physical width |
| `height` | float | Physical height |
| `priority` | int | 1–5, where 5 = most critical to place well |

The equipment list is **not** in any particular order.

## Your Task

Implement functions across three files. A test suite of **38 tests** validates your work.

---

### Part 1: Tag Detection (~12 min) → `src/detection.py`

Implement `detect_tags(image_path) -> List[BoundingBox]`

Detect the green rectangular tags in a floor plan PNG and return their bounding boxes. The images contain visual noise (walls, grid lines, room labels) that you should ignore.

```
pytest tests/test_detection.py -v
```

---

### Part 2: Equipment Placement (~18 min) → `src/placement.py`

Implement `assign_equipment(tags, equipment, floorplan_path) -> PlacementResult`

Given detected tags and the equipment catalog, determine the optimal assignment of equipment to zones. Minimize placement error across all assignments.

**Things you need to decide:**
- How to define the cost of assigning a given equipment item to a given tag
- Equipment can be **rotated 90°** — you must decide when rotation improves the fit
- Equipment has **priority levels** — your cost function should account for this
- There are more equipment items (300) than tags (5–15 per plan) — not all equipment will be placed
- Each equipment can be assigned to at most one tag; each tag gets at most one equipment
- Your solution must process all 20 floor plans in **under 10 seconds total**

Populate each `Assignment` with your computed `cost` and whether the equipment is `rotated`.

```
pytest tests/test_placement.py -v
```

---

### Part 3: Orchestration, Visualization & Analysis (~15 min) → `src/main.py`

Implement all five functions:

**Orchestration** — `find_all_results()` and `find_best_floorplan()` to run detection + placement across all floor plans and identify the best one.

**Visualization:**
- `cost_to_color(cost, max_cost)` — map a cost value to a green→yellow→red BGR color gradient
- `render_placement(result, output_path)` — annotate the original floor plan image with color-coded borders per tag, equipment labels (ID, priority, rotation status), and a summary overlay
- `render_top_n(n, output_dir)` — full pipeline: process all plans, render the top N, print a summary table

```
pytest tests/test_integration.py -v
```

---

## Provided Code (do not modify)

| File | What it does |
|---|---|
| `src/models.py` | Data classes: `BoundingBox`, `Equipment`, `Assignment`, `PlacementResult` |
| `src/loader.py` | Loads equipment JSON and lists floor plan paths |
| `tests/` | Full test suite (38 tests) |
| `run.py` | Runner script to execute the full pipeline and view rendered results |

Read `src/models.py` first — understand the data structures before writing code.

## Run All Tests

```bash
pytest tests/ -v
```

## View Rendered Results

Once your implementation is working, run the pipeline to see annotated floor plans:

```bash
python run.py              # Render top 5 to output/
python run.py --top 10     # Render top 10
python run.py --all        # Render all 20
```

Output images are saved to `output/`. Open them to visually verify your assignments.

## Evaluation Criteria

| Criteria | Weight |
|---|---|
| **Correctness** — tests pass | 35% |
| **Cost function design** — thoughtful handling of geometric fit, rotation, and priority | 25% |
| **Algorithm quality** — efficient approach that scales | 20% |
| **Code quality + communication** — clean code, explains approach and tradeoffs | 20% |

## Notes

- Use of AI coding tools is **encouraged**. We evaluate how you work with AI, not memorization.
- `scipy` and `sortedcontainers` are available if you want them.
- Start with Part 1, run those tests, then move forward. Part 3 builds on Parts 1 and 2.
