# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A take-home interview challenge for engineering candidates at Rebar. Candidates analyze industrial floor plan images to detect green rectangular tags (equipment placement zones), then optimally assign equipment from a 300-item catalog to those zones. The challenge has three parts with 38 total tests.

## Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run all 38 tests
pytest tests/ -v

# Run tests by part
pytest tests/test_detection.py -v      # Part 1: Tag detection (5 tests)
pytest tests/test_placement.py -v      # Part 2: Placement algorithm (12 tests)
pytest tests/test_integration.py -v    # Part 3: Orchestration & rendering (21 tests)

# Run a single test
pytest tests/test_placement.py::TestRotation::test_rotates_when_clearly_better -v

# Run the full pipeline (requires all parts implemented)
python run.py              # Render top 5 to output/
python run.py --top 10     # Render top 10
python run.py --all        # Render all 20
```

## Architecture

The candidate implements three files; everything else is read-only:

| File | Part | What to implement |
|---|---|---|
| `src/detection.py` | 1 | `detect_tags()` — OpenCV-based green rectangle detection in floor plan PNGs |
| `src/placement.py` | 2 | `assign_equipment()` — cost function + assignment optimization (Hungarian/greedy) |
| `src/main.py` | 3 | Orchestration (`find_all_results`, `find_best_floorplan`), visualization (`cost_to_color`, `render_placement`, `render_top_n`) |

**Do not modify:** `src/models.py`, `src/loader.py`, `tests/`, `run.py`, `data/`

### Data flow

1. `loader.py` loads `data/equipment.json` (300 items with id/name/width/height/priority) and lists `data/floorplans/*.png` (20 images, 1200x900px)
2. `detection.py` finds green rectangles in each floorplan → `List[BoundingBox]`
3. `placement.py` assigns equipment to tags, considering aspect ratio fit, 90° rotation, and priority (1-5) → `PlacementResult`
4. `main.py` orchestrates across all 20 floorplans, renders annotated images with color-coded overlays (BGR green→yellow→red gradient)

### Key data models (`src/models.py`)

- **BoundingBox**: x, y, width, height (with aspect_ratio and area properties)
- **Equipment**: id, name, width, height, priority
- **Assignment**: tag + equipment + cost + rotated flag
- **PlacementResult**: floorplan_path + assignments list (with total_cost, mean_cost, num_assignments properties)

### Key constraints

- 300 equipment items vs 5-15 tags per plan — not all equipment gets placed
- Equipment can be rotated 90° when it improves fit
- Higher priority (5) = more critical to place well — must affect cost function
- All 20 floorplans must process in under 10 seconds total; 100 tags + 300 equipment in under 5 seconds
- `ground_truth.json` has expected tag counts per floorplan (detection tolerance: ±2)

## Dependencies

opencv-python, numpy, scipy, sortedcontainers, pytest
