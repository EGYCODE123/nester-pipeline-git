"""
Consolidated Nesting Engine Core
Contains all nesting logic: Fabric Nesting
"""

from __future__ import annotations
from typing import List, Dict, Any, NamedTuple, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import time
import hashlib
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration Constants
# ============================================================================

MARKER_ROLL_LENGTH_MM = 5900  # Marker length constraint (5.9 meters)
SAFETY_GAP_X_MM = 10  # Gap along roll length (x-direction) between pieces with different heights
SAFETY_GAP_Y_MM = 10  # Gap across roll width (y-direction) between shelves with different widths
APPLY_GAPS_TO_LENGTH = True  # Include gaps in used length calculation
BOUNDARY_EPS = 1e-6  # Epsilon for boundary detection (prevents floating-point issues)

# ============================================================================
# Data Models
# ============================================================================

class Placement(NamedTuple):
    """Placement from Fabric Nesting Engine."""
    x: float       # mm along fabric length (X axis, from roll start)
    y: float       # mm across roll width (Y axis, from roll edge)
    w: float       # mm piece width across the roll (Y-extent)
    h: float       # mm piece drop/length (X-extent)
    level: int     # shelf index (0..)
    item_id: int   # index within input list
    line_id: int = 1  # optional: source line for multi-line views


@dataclass(frozen=True)
class MarkerPlacedRect:
    """A placed rectangle in a marker with exact coordinates from Fabric Nesting."""
    item_id: int      # Original item_id from Fabric Nesting
    level: int        # Shelf level (0-based)
    x: float          # Local to marker, mm along roll length (from marker start)
    y: float          # Across roll width (from edge), mm
    w: float          # Width across roll (y-extent), mm
    h: float          # Height along roll length (x-extent), mm


@dataclass
class Marker:
    """A 5.9m segment of the roll containing placed rects."""
    idx: int                  # sequential across the order, 1-based
    batch_id: int             # contiguous markers of same roll width share batch id
    roll_width_mm: int
    length_mm: float = 5900.0  # Actual used length (float for precision)
    rects: Optional[List[MarkerPlacedRect]] = None  # exact placements from Fabric Nesting

    @property
    def efficiency(self) -> float:
        """Calculate utilization percentage of this marker."""
        if self.rects is None:
            return 0.0
        used = sum(rect.w * rect.h for rect in self.rects)
        total = self.roll_width_mm * self.length_mm
        return 0.0 if total == 0 else 100.0 * used / total


@dataclass(frozen=True)
class TubeCut:
    """Represents a single tube with its cuts."""
    pieces_mm: List[int]           # in cut order for drawing
    used_mm: int                   # includes kerfs
    waste_mm: int


@dataclass(frozen=True)
class TubePattern:
    """Represents a unique cutting pattern with count."""
    key: Tuple[int, ...]           # sorted piece list for deduplication
    sample: TubeCut                # representative cut for rendering
    count: int                     # number of tubes with this pattern


@dataclass(frozen=True)
class TubePlan:
    """Complete cutting plan with all metrics."""
    total_pieces: int
    num_tubes: int
    stock_length_mm: int
    kerf_mm: int
    efficiency: float              # 0..1
    total_used_mm: int
    total_waste_mm: int
    tubes: List[TubeCut]
    patterns: List[TubePattern]    # deduped for UI
    infeasible_pieces: List[Tuple[int, str]]  # (width_mm, reason)


@dataclass
class Line:
    """Line input for efficiency calculation."""
    line_id: str
    width_mm: int
    drop_mm: int
    qty: int
    fabric_code: str | None = None
    series: str | None = None

# ============================================================================
# Fabric Nesting - FFDH Algorithm
# ============================================================================

def _pack_ffdh(
    items: List[Tuple[int, int]],  # (width_mm, drop_mm), already expanded by qty
    roll_width_mm: int,
    gap_mm: float,
    keep_input_order: bool = False,
) -> Tuple[List[Placement], List[Dict[str, float]]]:
    """
    First-Fit Decreasing Height (FFDH) with shelves aligned along X.
    - Sort by drop (h) desc, then width (w) desc for stability (unless keep_input_order=True).
    - In each shelf we consume Y (width) from 0→roll_width_mm.
    - New shelf opens at x0 += prev.height + gap_mm.
    Returns placements and shelf metadata [{'x0','height','used_y'}].
    """
    if not items:
        return [], []

    # Defensive clamps
    gap_mm = max(0.0, float(gap_mm))
    roll_width_mm = int(roll_width_mm)

    # Validate immediate constraints
    max_w = max(w for w, _ in items)
    if max_w > roll_width_mm:
        raise ValueError(f"Item width {max_w}mm exceeds roll width {roll_width_mm}mm.")

    # Stable order
    enumerated = list(enumerate(items))
    if not keep_input_order:
        # OLD: height-desc resort; keep for legacy callers
        enumerated.sort(key=lambda t: (-t[1][1], -t[1][0], t[0]))

    placements: List[Placement] = []
    shelves: List[Dict[str, float]] = []

    for idx, (w_mm, h_mm) in enumerated:
        if w_mm <= 0 or h_mm <= 0:
            raise ValueError(f"Non-positive piece size at index {idx}: {w_mm}x{h_mm} mm.")

        placed = False

        # Best-Fit: choose shelf with least Y leftover after placement
        best = None
        for s_idx, s in enumerate(shelves):
            # A piece can go on this shelf only if its drop fits within shelf height
            if h_mm > s["height"] + 1e-9:
                continue

            remaining_y = roll_width_mm - s["used_y"]
            need_y = w_mm if s["used_y"] == 0 else (gap_mm + w_mm)

            if need_y <= remaining_y + 1e-9:
                leftover = remaining_y - need_y
                if best is None or leftover < best[0]:
                    best = (leftover, s_idx, s)
        
        if best is not None:
            _, s_idx, s = best
            x = s["x0"]
            y = 0.0 if s["used_y"] == 0 else s["used_y"] + gap_mm
            placements.append(Placement(x=float(x), y=float(y), w=float(w_mm), h=float(h_mm), level=s_idx, item_id=idx))
            s["used_y"] += (w_mm if y == 0.0 else gap_mm + w_mm)
            placed = True

        if placed:
            continue

        # Open a new shelf
        x0 = 0.0 if not shelves else shelves[-1]["x0"] + shelves[-1]["height"] + gap_mm
        s = {"x0": float(x0), "height": float(h_mm), "used_y": 0.0}
        shelves.append(s)

        # Place first item at y=0
        placements.append(Placement(x=float(x0), y=0.0, w=float(w_mm), h=float(h_mm), level=len(shelves) - 1, item_id=idx))
        s["used_y"] = float(w_mm)

    # Final invariant pass (strict)
    for p in placements:
        if p.y + p.w > roll_width_mm + 1e-6:
            raise AssertionError(f"Overflow across width: y={p.y} + w={p.w} > roll={roll_width_mm}")

    for s_idx, s in enumerate(shelves):
        # Pieces on a shelf must not overlap in Y and must have h <= shelf.height
        ys = []
        for p in placements:
            if p.level == s_idx:
                if p.h > s["height"] + 1e-6 or abs(p.x - s["x0"]) > 1e-6:
                    raise AssertionError("Invalid piece placed into shelf.")
                ys.append((p.y, p.y + p.w))
        ys.sort()
        for a, b in zip(ys, ys[1:]):
            if a[1] > b[0] + 1e-6:
                raise AssertionError("Overlap within shelf detected.")

    return placements, shelves


def _compact_layout(
    placements: List[Placement],
    shelves: List[Dict[str, float]],
    roll_width_mm: int,
    gap_y: float,
) -> Tuple[List[Placement], List[Dict[str, float]]]:
    """
    Post-pack compaction:
    - Intra-shelf left-shift (normalize y based on sorted order, closing numerical gaps)
    - Merge adjacent equal-height shelves if the combined used_y fits within roll width
    Returns updated placements and shelves. Never increases used length.
    """
    if not placements or not shelves:
        return placements, shelves

    # Intra-shelf normalize (left-shift)
    by_level: Dict[int, List[Placement]] = {}
    for p in placements:
        by_level.setdefault(p.level, []).append(p)
    new_placements: List[Placement] = list(placements)
    for lvl, plist in by_level.items():
        # Sort by y ascending
        plist_sorted = sorted(plist, key=lambda p: p.y)
        cursor_y = 0.0
        for idx, p in enumerate(plist_sorted):
            desired_y = cursor_y
            if abs(p.y - desired_y) > 1e-6:
                # Update placement y
                i = new_placements.index(p)
                new_placements[i] = Placement(x=p.x, y=float(desired_y), w=p.w, h=p.h, level=p.level, item_id=p.item_id, line_id=p.line_id)
            cursor_y += p.w + (gap_y if idx < len(plist_sorted) - 1 else 0.0)
        # Update shelf used_y
        shelves[lvl]["used_y"] = min(float(roll_width_mm), float(cursor_y))

    # Attempt merges for adjacent equal-height shelves
    i = 0
    while i < len(shelves) - 1:
        s1 = shelves[i]
        s2 = shelves[i + 1]
        if abs(s1["height"] - s2["height"]) <= 1e-6:
            # Sum used_y with one in-shelf gap if both have items
            connector = gap_y if (s1["used_y"] > 0 and s2["used_y"] > 0) else 0.0
            if s1["used_y"] + connector + s2["used_y"] <= roll_width_mm + 1e-6:
                # We can merge: move all level i+1 placements to level i, packed after s1.used_y
                start_y = s1["used_y"] + (gap_y if s1["used_y"] > 0 and s2["used_y"] > 0 else 0.0)
                moved: List[Placement] = []
                for idx_p, p in enumerate(new_placements):
                    if p.level == i + 1:
                        new_p = Placement(x=s1["x0"], y=float(start_y), w=p.w, h=p.h, level=i, item_id=p.item_id, line_id=p.line_id)
                        moved.append((idx_p, new_p))
                        start_y += p.w + (gap_y if start_y > 0 else 0.0)
                for idx_p, new_p in moved:
                    new_placements[idx_p] = new_p
                # Remove shelf i+1 and collapse subsequent x0 by (s2.height + gap_y)
                delta_x = s2["height"] + gap_y
                del shelves[i + 1]
                for j in range(i + 1, len(shelves)):
                    shelves[j]["x0"] -= delta_x
                # Update s1 used_y
                s1["used_y"] = min(float(roll_width_mm), float(start_y))
                # Update levels for placements beyond removed shelf
                updated: List[Placement] = []
                for p in new_placements:
                    lvl = p.level - 1 if p.level > i + 1 else p.level
                    updated.append(Placement(x=p.x if lvl != i else s1["x0"], y=p.y, w=p.w, h=p.h, level=lvl, item_id=p.item_id, line_id=p.line_id))
                new_placements = updated
                # Do not advance i to re-check potential further merges
                continue
        i += 1

    return new_placements, shelves


def compute_layout(
    blinds: List[Tuple[int, int]],
    roll_width_mm: int,
    gap_mm: float = 0.0,
) -> Dict[str, Any]:
    """
    Pack a single set of blinds on one roll width.
    Returns:
      {
        'placements': [Placement],
        'used_length_mm': float,               # along X
        'utilization': float,                  # area / (roll_width * used_length)
        'levels': int,                         # number of shelves
        'meta': {'roll_width_mm', 'gap_mm', 'algo', 'ms'}
      }
    """
    t0 = time.perf_counter()
    
    # Force largest-first to land at bottom-left
    blinds = sorted(blinds, key=lambda t: (-(t[0]*t[1]), -t[0], -t[1]))

    # Empty fast-path
    if not blinds:
        return {
            "placements": [],
            "used_length_mm": 0.0,
            "utilization": 0.0,
            "levels": 0,
            "meta": {
                "roll_width_mm": int(roll_width_mm),
                "gap_mm": float(gap_mm),
                "algo": "FFDH-horizontal",
                "ms": 0,
            },
        }

    # Hard limits (as specified)
    if len(blinds) > 100000:  # safety guard for accidental huge inputs
        raise ValueError("Too many pieces.")

    for (w, h) in blinds:
        if w > 3200:
            raise ValueError(f"Width {w}mm exceeds maximum 3200mm.")
        if h > 5000:
            raise ValueError(f"Drop {h}mm exceeds maximum 5000mm.")
        if w <= 0 or h <= 0:
            raise ValueError("Non-positive dimensions encountered.")

    placements, shelves = _pack_ffdh(blinds, int(roll_width_mm), float(gap_mm), keep_input_order=True)

    # Post-pack compaction (uses gap as in-shelf gap; shelf gap is not increased)
    placements, shelves = _compact_layout(placements, shelves, int(roll_width_mm), float(gap_mm))

    used_len = 0.0
    if shelves:
        used_len = shelves[-1]["x0"] + shelves[-1]["height"]  # no trailing gap

    total_area = float(sum(w * h for (w, h) in blinds))
    denom = (roll_width_mm * used_len) if used_len > 0 else 0.0
    util = (total_area / denom) if denom > 0 else 0.0

    ms = int(round((time.perf_counter() - t0) * 1000))

    return {
        "placements": placements,
        "used_length_mm": round(used_len, 3),
        "utilization": max(0.0, min(1.0, util)),
        "levels": len(shelves),
        "meta": {
            "roll_width_mm": int(roll_width_mm),
            "gap_mm": float(gap_mm),
            "algo": "FFDH-horizontal",
            "ms": ms,
        },
    }


def compute_layout_per_line(
    lines: List[Dict[str, Any]],
    roll_width_mm: int = 0,   # ignored if a line provides its own width
    gap_mm: float = 0.0,      # default gap unless overridden by line
) -> Dict[str, Any]:
    """
    Compute packing per line and a simple combined metric.
    Each line dict may contain:
      {"line_id": int, "items": [(w,h), ...], "gap_mm": float, "roll_width_mm": int}
    """
    t0 = time.perf_counter()
    results: List[Dict[str, Any]] = []

    total_area = 0.0
    total_roll_area = 0.0
    combined_used_length = 0.0

    for li, line in enumerate(lines):
        lid = int(line.get("line_id", li + 1))
        rw = int(line.get("roll_width_mm", roll_width_mm))
        gp = float(line.get("gap_mm", gap_mm))
        items: List[Tuple[int, int]] = list(line.get("items", []))

        # Limits: qty ≤ 1000 per spec
        if len(items) > 1000:
            raise ValueError(f"Line {lid}: quantity {len(items)} exceeds 1000.")

        # Validate width ≤ roll
        if items:
            mw = max(w for w, _ in items)
            if mw > rw:
                raise ValueError(f"Line {lid}: item width {mw}mm exceeds roll width {rw}mm.")

        layout = compute_layout(items, rw, gp)

        used = float(layout["used_length_mm"])
        fabric_m1 = used / 1000.0
        fabric_m2 = (rw * used) / 1_000_000.0

        # Tag placements with line id
        tagged = [Placement(p.x, p.y, p.w, p.h, p.level, p.item_id, line_id=lid) for p in layout["placements"]]

        lr = {
            "line_id": lid,
            "placements": tagged,
            "used_length_mm": used,
            "util": float(layout["utilization"]),
            "fabric_m1": fabric_m1,
            "fabric_m2": fabric_m2,
            "levels": int(layout["levels"]),
            "pieces": len(items),
            "roll_width_mm": rw,
        }
        results.append(lr)

        # Combined metrics
        total_area += sum(w * h for (w, h) in items)
        total_roll_area += rw * used
        combined_used_length += used

    combined = {
        "placements": [],  # viewer renders per-line; combined placements not required
        "used_length_mm": combined_used_length,
        "util": (total_area / total_roll_area) if total_roll_area > 0 else 0.0,
        "fabric_m1": combined_used_length / 1000.0,
        "fabric_m2": total_roll_area / 1_000_000.0,
        "levels": sum(r["levels"] for r in results),
        "pieces": sum(r["pieces"] for r in results),
    }

    return {
        "lines": results,
        "combined": combined,
        "meta": {
            "compute_time_ms": int(round((time.perf_counter() - t0) * 1000)),
            "algo": "FFDH-horizontal-per-line",
        },
    }

# ============================================================================
# Marker Nesting - Cut-line-aware Segmentation
# ============================================================================

# Cache for markerization results
_marker_cache: Dict[str, List[Marker]] = {}


def _make_cache_key(placements: List[Placement], roll_width_mm: int) -> str:
    """Create cache key from placements content hash."""
    items_data = []
    for p in placements:
        items_data.append((p.x, p.y, p.w, p.h, p.level, p.item_id))
    
    items_data.sort()
    content = f"{roll_width_mm}:{len(items_data)}:{tuple(items_data)}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _normalize_local_x(items: List[Tuple[int, int, float, float, float, float]], marker_idx: int) -> List[Tuple[int, int, float, float, float, float]]:
    """
    Normalize local x coordinates to ensure all rects start at x >= 0.
    CRITICAL: Ensures marker blue area always starts at (0,0) by normalizing coordinates.
    
    Args:
        items: List of (item_id, level, x, y, w, h) with x in global coordinates
        marker_idx: Marker index (0-based)
        
    Returns:
        List of (item_id, level, local_x, y, w, h) with all local_x >= 0 (guaranteed to start at x=0)
    """
    if not items:
        return []
    
    # Convert to marker-local coordinates
    roll_length_mm = MARKER_ROLL_LENGTH_MM
    marker_offset = marker_idx * roll_length_mm
    loc_items = [(iid, lvl, x - marker_offset, y, w, h) for (iid, lvl, x, y, w, h) in items]
    
    # Find minimum x (may be negative if item was pushed)
    min_x = min(x for _, _, x, _, _, _ in loc_items) if loc_items else 0.0
    
    # Shift all items right if min_x < 0 to ensure starting at x=0
    if min_x < 0:
        dx = -min_x
        loc_items = [(iid, lvl, x + dx, y, w, h) for (iid, lvl, x, y, w, h) in loc_items]
    elif min_x > 0:
        # If min_x > 0, shift left to start at 0 for consistency
        dx = -min_x
        loc_items = [(iid, lvl, x + dx, y, w, h) for (iid, lvl, x, y, w, h) in loc_items]
    
    return loc_items


def _estimate_length_with_gaps(placements: List[Placement], marker_idx: int = 0) -> float:
    """
    Estimate the total length of a group of placements including gaps.
    
    This function is used during marker splitting to ensure that gaps + drops <= 5.9m.
    It performs the same normalization and gap calculation that will be done when creating
    the actual marker, providing an accurate estimate.
    
    Args:
        placements: List of Placement objects to estimate length for
        marker_idx: Marker index for normalization (default 0 for estimation)
        
    Returns:
        Estimated total length in mm (drops + gaps if APPLY_GAPS_TO_LENGTH is True)
    """
    if not placements:
        return 0.0
    
    # Convert to (item_id, level, x, y, w, h) format
    items = [
        (p.item_id, p.level, float(p.x), float(p.y), float(p.w), float(p.h))
        for p in placements
    ]
    
    # Normalize local coordinates (ensure all x >= 0)
    loc_items = _normalize_local_x(items, marker_idx)
    
    if not loc_items:
        return 0.0
    
    # Calculate base used length (max of local_x + h)
    used_len = max((x + h) for _, _, x, _, _, h in loc_items)
    
    # Apply gaps to length if configured
    if APPLY_GAPS_TO_LENGTH:
        # Count x-gaps (different heights in same level)
        by_level = defaultdict(list)
        for (iid, lvl, x, y, w, h) in loc_items:
            by_level[lvl].append((x, y, w, h))
        
        gap_count = 0
        for level_rects in by_level.values():
            # Sort by x
            sorted_rects = sorted(level_rects, key=lambda r: r[0])
            for i in range(len(sorted_rects) - 1):
                r1 = sorted_rects[i]
                r2 = sorted_rects[i + 1]
                if abs(r1[3] - r2[3]) > 1e-6:  # Different heights (h values)
                    gap_count += 1
        
        if gap_count > 0:
            used_len += gap_count * SAFETY_GAP_X_MM
    
    return used_len


def build_markers_from_layout(
    placements: List[Placement],
    roll_width_mm: int,
    batch_id: int,
    roll_length_mm: int = MARKER_ROLL_LENGTH_MM
) -> List[Marker]:
    """
    Build markers from Fabric Nesting placements using cut-line-aware segmentation.
    
    CRITICAL: Never cuts rectangles. If a rectangle would cross the 5.9m boundary,
    it is pushed entirely into the next marker.
    
    Args:
        placements: List of Placement objects from Fabric Nesting (exact source of truth)
        roll_width_mm: Roll width in mm
        batch_id: Batch ID for grouping markers of same roll width
        roll_length_mm: Marker length constraint (default 5900mm)
        
    Returns:
        List of Marker objects with exact placements preserved
    """
    t0 = time.perf_counter()
    
    # Check cache
    cache_key = _make_cache_key(placements, roll_width_mm)
    if cache_key in _marker_cache:
        logger.info(f"[Markers] cache_hit=True batch={roll_width_mm} items={len(placements)}")
        return _marker_cache[cache_key]
    
    if not placements:
        return []
    
    # Sort placements by (x, level, item_id) to preserve order
    sorted_placements = sorted(placements, key=lambda p: (p.x, p.level, p.item_id))
    
    # Cut-line-aware segmentation: group placements into markers
    buckets: Dict[int, List[Placement]] = defaultdict(list)
    
    for p in sorted_placements:
        start = float(p.x)
        end = start + float(p.h)
        
        # Calculate which marker this placement belongs to
        m_start = int(start // roll_length_mm)
        boundary = (m_start + 1) * roll_length_mm
        
        # Push rule: if placement would cross boundary, push to next marker
        if end <= boundary - BOUNDARY_EPS:
            # Fits in current marker
            m = m_start
        else:
            # Crosses boundary - push to next marker
            m = m_start + 1
        
        buckets[m].append(p)
    
    # Convert grouped placements into Marker objects
    processed_buckets: Dict[int, List[Placement]] = {}
    next_marker_idx = max(buckets.keys()) + 1 if buckets else 0
    
    for m in sorted(buckets.keys()):
        marker_placements = buckets[m]
        
        # Estimate total length including gaps (not just sum of drops)
        estimated_length = _estimate_length_with_gaps(marker_placements, marker_idx=m)
        
        if estimated_length > roll_length_mm + BOUNDARY_EPS:
            # Split placements into multiple markers if total length (drops + gaps) exceeds 5.9m
            logger.warning(
                f"[Markers] Marker {m} has estimated length {estimated_length:.2f}mm (including gaps) > {roll_length_mm}mm. "
                f"Splitting {len(marker_placements)} placements across multiple markers."
            )
            # Group placements to ensure each group's total length (drops + gaps) <= 5.9m
            current_group: List[Placement] = []
            
            for p in sorted(marker_placements, key=lambda p: (p.x, p.level, p.item_id)):
                # Create temporary group with new placement added
                temp_group = current_group + [p]
                
                # Estimate length of temporary group including gaps
                temp_estimated_length = _estimate_length_with_gaps(temp_group, marker_idx=next_marker_idx)
                
                # If adding this placement would exceed 5.9m (and current group is not empty), split
                if temp_estimated_length > roll_length_mm + BOUNDARY_EPS and current_group:
                    # Start new group - add current group to processed buckets
                    processed_buckets[next_marker_idx] = current_group
                    next_marker_idx += 1
                    current_group = [p]
                else:
                    # Add to current group (safe to add)
                    current_group.append(p)
            
            if current_group:
                processed_buckets[next_marker_idx] = current_group
                next_marker_idx += 1
        else:
            # Estimated length (drops + gaps) is within bounds, use as-is
            processed_buckets[m] = marker_placements
    
    # Second pass: convert processed buckets into Marker objects
    markers = []
    marker_idx = 1
    
    for m in sorted(processed_buckets.keys()):
        marker_placements = processed_buckets[m]
        
        # Convert to (item_id, level, x, y, w, h) format
        items = [
            (p.item_id, p.level, float(p.x), float(p.y), float(p.w), float(p.h))
            for p in marker_placements
        ]
        
        # Determine marker segment index for normalization
        if items:
            min_global_x = min(x for _, _, x, _, _, _ in items)
            segment_idx = int(min_global_x // roll_length_mm)
        else:
            segment_idx = m
        
        # Normalize local coordinates (ensure all x >= 0)
        loc_items = _normalize_local_x(items, segment_idx)
        
        if not loc_items:
            continue
        
        # Calculate used length (max of local_x + h)
        used_len = max((x + h) for _, _, x, _, _, h in loc_items)
        
        # Apply gaps to length if configured
        if APPLY_GAPS_TO_LENGTH:
            # Count x-gaps (different heights in same level)
            by_level = defaultdict(list)
            for (iid, lvl, x, y, w, h) in loc_items:
                by_level[lvl].append((x, y, w, h))
            
            gap_count = 0
            for level_rects in by_level.values():
                # Sort by x
                sorted_rects = sorted(level_rects, key=lambda r: r[0])
                for i in range(len(sorted_rects) - 1):
                    r1 = sorted_rects[i]
                    r2 = sorted_rects[i + 1]
                    if abs(r1[3] - r2[3]) > 1e-6:  # Different heights
                        gap_count += 1
            
            if gap_count > 0:
                used_len += gap_count * SAFETY_GAP_X_MM
        
        # Assert bound with tolerance
        if used_len > roll_length_mm + 0.5:
            logger.error(
                f"[Markers] Marker {marker_idx} length {used_len:.2f}mm exceeds {roll_length_mm}mm. "
                f"Applying minimal shift. Items: {len(loc_items)}"
            )
            # Apply minimal shift to satisfy bound
            excess = used_len - roll_length_mm
            loc_items = [(iid, lvl, x - excess, y, w, h) for (iid, lvl, x, y, w, h) in loc_items]
            used_len = max((x + h) for _, _, x, _, _, h in loc_items)
        
        # Clamp used_len to roll_length_mm
        used_len = min(used_len, roll_length_mm)
        
        # Convert to MarkerPlacedRect objects
        rects = [
            MarkerPlacedRect(
                item_id=iid,
                level=lvl,
                x=x,  # Position along length - normalized to marker-local, gaps affect spacing between items
                y=y,  # Position across width - preserved from nesting, gaps affect spacing between shelves
                w=w,  # Blind width - EXACTLY from nesting, NEVER modified
                h=h   # Blind height/drop - EXACTLY from nesting, NEVER modified
            )
            for (iid, lvl, x, y, w, h) in loc_items
        ]
        
        # Create marker
        marker = Marker(
            idx=marker_idx,
            batch_id=batch_id,
            roll_width_mm=roll_width_mm,
            length_mm=used_len,
            rects=rects,
        )
        
        markers.append(marker)
        marker_idx += 1
    
    # Calculate metrics for logging
    max_len = max(m.length_mm for m in markers) if markers else 0.0
    runtime_ms = (time.perf_counter() - t0) * 1000
    
    logger.info(
        f"[Markers] batch={roll_width_mm} items={len(placements)} markers={len(markers)} "
        f"max_len={max_len:.1f}mm violations=0 runtime={runtime_ms:.1f}ms cache_hit=False"
    )
    
    # Cache result
    _marker_cache[cache_key] = markers
    
    return markers


def clear_marker_cache():
    """Clear the markerization cache (call when layout changes)."""
    global _marker_cache
    _marker_cache.clear()

# ============================================================================
# Aluminum Tube Cutting - 1D Cutting Stock Problem
# ============================================================================

def validate_pieces(
    items: List[Tuple[int, int]],
    stock_length_mm: int,
    kerf_mm: int
) -> Tuple[List[int], List[Tuple[int, str]]]:
    """
    Validate and expand pieces.
    
    Args:
        items: [(width_mm, qty), ...]
        stock_length_mm: Stock tube length
        kerf_mm: Saw blade width
        
    Returns:
        (valid_pieces, infeasible_pieces)
    """
    valid_pieces = []
    infeasible = []
    
    for width_mm, qty in items:
        # Skip invalid quantities
        if qty <= 0:
            logger.warning(f"Skipping item with non-positive quantity: {width_mm}mm × {qty}")
            continue
            
        if width_mm <= 0:
            logger.warning(f"Skipping item with non-positive width: {width_mm}mm")
            continue
        
        # Check if piece fits in stock (with kerf if not first piece)
        if width_mm > stock_length_mm:
            reason = f"{width_mm}mm exceeds stock length {stock_length_mm}mm"
            infeasible.append((width_mm, reason))
            logger.warning(f"Infeasible piece: {reason}")
            continue
        
        # Expand by quantity
        valid_pieces.extend([width_mm] * qty)
    
    return valid_pieces, infeasible


def pack_bfd(
    pieces: List[int],
    stock_length_mm: int,
    kerf_mm: int
) -> List[TubeCut]:
    """
    Best-Fit Decreasing bin packing algorithm.
    
    For each piece (already sorted descending):
    - Choose tube with minimal remaining capacity that fits
    - If no tube fits, open new tube
    
    Args:
        pieces: List of piece lengths in mm (sorted descending)
        stock_length_mm: Tube stock length
        kerf_mm: Kerf between adjacent cuts (not at tube edges)
        
    Returns:
        List of TubeCut objects
    """
    if not pieces:
        return []
    
    tubes: List[Dict] = []  # {'pieces': [int], 'used': int}
    
    for piece_mm in pieces:
        best_tube = None
        best_remaining = float('inf')
        
        # Find tube with smallest remaining capacity that fits this piece
        for tube in tubes:
            # Calculate space needed (include kerf if not first piece in tube)
            needed = piece_mm
            if tube['pieces']:  # Not empty
                needed += kerf_mm
            
            remaining = stock_length_mm - tube['used']
            
            if needed <= remaining and remaining < best_remaining:
                best_tube = tube
                best_remaining = remaining
        
        if best_tube is not None:
            # Add to best-fit tube
            if best_tube['pieces']:
                best_tube['used'] += kerf_mm
            best_tube['pieces'].append(piece_mm)
            best_tube['used'] += piece_mm
        else:
            # Open new tube
            tubes.append({
                'pieces': [piece_mm],
                'used': piece_mm
            })
    
    # Convert to TubeCut objects
    result = []
    for tube in tubes:
        waste = stock_length_mm - tube['used']
        result.append(TubeCut(
            pieces_mm=tube['pieces'],
            used_mm=tube['used'],
            waste_mm=waste
        ))
    
    return result


def improve_pair_swaps(
    tubes: List[TubeCut],
    stock_length_mm: int,
    kerf_mm: int,
    max_passes: int = 2
) -> List[TubeCut]:
    """
    Improve packing by trying piece swaps between tube pairs.
    
    For each pair of tubes, try swapping pieces to reduce tube count
    or decrease total waste.
    
    Args:
        tubes: Current tube cutting plan
        stock_length_mm: Tube stock length
        kerf_mm: Kerf between cuts
        max_passes: Maximum improvement passes
        
    Returns:
        Improved list of TubeCut objects
    """
    if len(tubes) <= 1:
        return tubes
    
    def calc_used(pieces: List[int]) -> int:
        """Calculate used length including kerfs."""
        if not pieces:
            return 0
        return sum(pieces) + kerf_mm * (len(pieces) - 1)
    
    # Convert to mutable format
    mutable_tubes = [[p for p in tube.pieces_mm] for tube in tubes]
    
    for pass_num in range(max_passes):
        improved = False
        
        # Try all tube pairs
        for i in range(len(mutable_tubes)):
            for j in range(i + 1, len(mutable_tubes)):
                tube_a = mutable_tubes[i]
                tube_b = mutable_tubes[j]
                
                if not tube_a or not tube_b:
                    continue
                
                # Try moving each piece from A to B
                for piece_idx in range(len(tube_a)):
                    piece = tube_a[piece_idx]
                    
                    # Check if piece fits in tube B
                    new_b_used = calc_used(tube_b + [piece])
                    if new_b_used <= stock_length_mm:
                        # Check if this improves the solution
                        new_a = tube_a[:piece_idx] + tube_a[piece_idx+1:]
                        
                        # If tube A becomes empty, we reduced tube count
                        if not new_a:
                            tube_a.clear()
                            tube_a.extend(new_a)
                            tube_b.append(piece)
                            improved = True
                            break
                
                if improved:
                    break
            if improved:
                break
        
        # Remove empty tubes
        mutable_tubes = [t for t in mutable_tubes if t]
        
        if not improved:
            break
    
    # Convert back to TubeCut objects
    result = []
    for pieces in mutable_tubes:
        if pieces:
            used = calc_used(pieces)
            waste = stock_length_mm - used
            result.append(TubeCut(
                pieces_mm=pieces,
                used_mm=used,
                waste_mm=waste
            ))
    
    return result


def dedupe_patterns(tubes: List[TubeCut]) -> List[TubePattern]:
    """
    Deduplicate tube patterns for UI display.
    
    Pattern key is the sorted list of piece lengths.
    
    Args:
        tubes: List of all tube cuts
        
    Returns:
        List of unique patterns with counts
    """
    pattern_map: Dict[Tuple[int, ...], Tuple[TubeCut, int]] = {}
    
    for tube in tubes:
        # Create pattern key (sorted pieces)
        key = tuple(sorted(tube.pieces_mm))
        
        if key in pattern_map:
            sample, count = pattern_map[key]
            pattern_map[key] = (sample, count + 1)
        else:
            pattern_map[key] = (tube, 1)
    
    # Convert to TubePattern objects, sorted by count (most common first)
    patterns = [
        TubePattern(key=key, sample=sample, count=count)
        for key, (sample, count) in pattern_map.items()
    ]
    patterns.sort(key=lambda p: (-p.count, -sum(p.key)))
    
    return patterns


def compute_tube_plan(
    items: List[Tuple[int, int]],
    stock_length_mm: int = 6000,
    kerf_mm: int = 0,
    algo: str = "BFD",
    exact_threshold: int = 22,
    time_limit_s: float = 2.0
) -> TubePlan:
    """
    Compute optimal tube cutting plan.
    
    Args:
        items: [(width_mm, qty), ...] from order table
        stock_length_mm: Stock tube length (default 6000mm)
        kerf_mm: Saw blade kerf (default 0mm)
        algo: Algorithm - "BFD", "FFD", or "Exact" (only BFD implemented)
        exact_threshold: Use exact solver if pieces <= this (not implemented)
        time_limit_s: Time limit for exact solver (not implemented)
        
    Returns:
        TubePlan with complete cutting solution
    """
    logger.info(f"Computing tube plan: {len(items)} items, stock={stock_length_mm}mm, kerf={kerf_mm}mm, algo={algo}")
    
    # Validate and expand pieces
    pieces, infeasible = validate_pieces(items, stock_length_mm, kerf_mm)
    
    if not pieces:
        logger.warning("No valid pieces to cut")
        return TubePlan(
            total_pieces=0,
            num_tubes=0,
            stock_length_mm=stock_length_mm,
            kerf_mm=kerf_mm,
            efficiency=0.0,
            total_used_mm=0,
            total_waste_mm=0,
            tubes=[],
            patterns=[],
            infeasible_pieces=infeasible
        )
    
    # Sort pieces descending for BFD
    pieces_sorted = sorted(pieces, reverse=True)
    
    logger.debug(f"Packing {len(pieces_sorted)} pieces (largest: {pieces_sorted[0]}mm, smallest: {pieces_sorted[-1]}mm)")
    
    # Pack using BFD
    tubes = pack_bfd(pieces_sorted, stock_length_mm, kerf_mm)
    logger.info(f"BFD result: {len(tubes)} tubes")
    
    # Improve with pair swaps
    tubes = improve_pair_swaps(tubes, stock_length_mm, kerf_mm, max_passes=2)
    logger.info(f"After pair swaps: {len(tubes)} tubes")
    
    # Deduplicate patterns
    patterns = dedupe_patterns(tubes)
    logger.debug(f"Unique patterns: {len(patterns)}")
    
    # Calculate metrics
    total_used = sum(tube.used_mm for tube in tubes)
    total_waste = sum(tube.waste_mm for tube in tubes)
    efficiency = total_used / (len(tubes) * stock_length_mm) if tubes else 0.0
    
    plan = TubePlan(
        total_pieces=len(pieces),
        num_tubes=len(tubes),
        stock_length_mm=stock_length_mm,
        kerf_mm=kerf_mm,
        efficiency=efficiency,
        total_used_mm=total_used,
        total_waste_mm=total_waste,
        tubes=tubes,
        patterns=patterns,
        infeasible_pieces=infeasible
    )
    
    logger.info(f"Final plan: {plan.num_tubes} tubes, {plan.efficiency*100:.1f}% efficiency, {len(patterns)} patterns")
    
    return plan


# ============================================================================
# API Efficiency Calculation - Wrapper for Waste API
# ============================================================================

def compute_efficiency(
    lines: List[Line],
    candidate_widths_mm: Optional[List[int]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Compute waste efficiency for a list of lines.
    
    Args:
        lines: List of Line objects with width_mm, drop_mm, qty, etc.
        candidate_widths_mm: Optional list of available roll widths in mm.
                           If provided, will be used for multi-width optimization (future).
                           Currently accepted but not yet used in logic.
        
    Returns:
        Tuple of (results: List[Dict], totals: Dict) containing:
        - results: Per-line metrics with waste_factor_pct, utilization, etc.
        - totals: Aggregated metrics with eff_pct, waste_pct, etc.
    """
    if not lines:
        return [], {
            "eff_pct": 0.0,
            "waste_pct": 100.0,
            "total_area_m2": 0.0,
            "total_used_area_m2": 0.0,
            "total_waste_area_m2": 0.0,
        }
    
    # Convert lines to format for compute_layout_per_line
    # Determine roll width (use candidate_widths_mm if provided, otherwise use max width from items, or default to 3000mm)
    if candidate_widths_mm and len(candidate_widths_mm) > 0:
        # For now, use the minimum candidate width that fits all items
        # TODO: Future - implement multi-width optimization using candidate_widths_mm
        max_item_width = max(line.width_mm for line in lines)
        # Find smallest candidate width that fits all items
        fitting_widths = [w for w in candidate_widths_mm if w >= max_item_width]
        if fitting_widths:
            roll_width_mm = min(fitting_widths)
        else:
            # If no candidate width fits, use the maximum candidate width (will fail nesting but won't crash)
            roll_width_mm = max(candidate_widths_mm)
    else:
        max_width = max(line.width_mm for line in lines)
        roll_width_mm = max(max_width, 3000)  # Ensure at least 3000mm
    
    # Create mapping from numeric line_id (used internally) to original string line_id
    line_id_map = {i + 1: line.line_id for i, line in enumerate(lines)}
    
    # Prepare lines data for compute_layout_per_line
    # Use numeric line_ids (1, 2, 3, ...) for internal processing
    lines_data = []
    for idx, line in enumerate(lines):
        # Expand items by quantity
        items = [(line.width_mm, line.drop_mm)] * line.qty
        lines_data.append({
            "line_id": idx + 1,  # Use numeric line_id for internal processing
            "items": items,
            "gap_mm": 0.0,  # Default gap, can be made configurable
            "roll_width_mm": roll_width_mm,
        })
    
    # Compute layout using fabric nesting
    layout_result = compute_layout_per_line(lines_data, roll_width_mm=roll_width_mm, gap_mm=0.0)
    
    # Build results per line
    results = []
    total_blind_area = 0.0
    total_roll_area = 0.0
    
    for line_result in layout_result["lines"]:
        numeric_line_id = line_result["line_id"]  # This is now an int (1, 2, 3, ...)
        line_id = line_id_map.get(numeric_line_id, str(numeric_line_id))  # Map back to original string
        used_length_mm = line_result["used_length_mm"]
        utilization = line_result["util"]
        roll_width = line_result["roll_width_mm"]
        
        # Calculate areas
        blind_area_m2 = sum(p.w * p.h for p in line_result["placements"]) / 1_000_000.0
        roll_area_m2 = (roll_width * used_length_mm) / 1_000_000.0
        waste_area_m2 = roll_area_m2 - blind_area_m2
        waste_factor_pct = (waste_area_m2 / blind_area_m2 * 100.0) if blind_area_m2 > 0 else 0.0
        
        results.append({
            "line_id": line_id,
            "waste_factor_pct": round(waste_factor_pct, 2),
            "utilization": round(utilization * 100.0, 2),  # Convert to percentage
            "used_length_mm": round(used_length_mm, 2),
            "blind_area_m2": round(blind_area_m2, 3),
            "roll_area_m2": round(roll_area_m2, 3),
            "waste_area_m2": round(waste_area_m2, 3),
            "roll_width_mm": roll_width,
            "pieces": line_result["pieces"],
            "levels": line_result["levels"],
        })
        
        total_blind_area += blind_area_m2
        total_roll_area += roll_area_m2
    
    # Calculate totals
    total_waste_area = total_roll_area - total_blind_area
    overall_utilization = (total_blind_area / total_roll_area) if total_roll_area > 0 else 0.0
    overall_waste = 1.0 - overall_utilization
    
    totals = {
        "eff_pct": round(overall_utilization * 100.0, 2),
        "waste_pct": round(overall_waste * 100.0, 2),
        "total_area_m2": round(total_blind_area, 3),
        "total_used_area_m2": round(total_roll_area, 3),
        "total_waste_area_m2": round(total_waste_area, 3),
        "total_pieces": sum(r["pieces"] for r in results),
        "total_levels": sum(r["levels"] for r in results),
    }
    
    return results, totals

