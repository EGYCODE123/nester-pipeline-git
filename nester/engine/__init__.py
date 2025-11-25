"""
Nesting Engine Core Module
Exports all nesting functionality: Fabric, Marker, and Aluminum Tube calculations
"""

from .core import (
    # Configuration
    MARKER_ROLL_LENGTH_MM,
    SAFETY_GAP_X_MM,
    SAFETY_GAP_Y_MM,
    APPLY_GAPS_TO_LENGTH,
    BOUNDARY_EPS,
    
    # Data Models
    Placement,
    MarkerPlacedRect,
    Marker,
    TubeCut,
    TubePattern,
    TubePlan,
    Line,
    
    # Fabric Nesting
    compute_layout,
    compute_layout_per_line,
    
    # Marker Nesting
    build_markers_from_layout,
    clear_marker_cache,
    
    # Aluminum Tube Cutting
    compute_tube_plan,
    validate_pieces,
    pack_bfd,
    improve_pair_swaps,
    dedupe_patterns,
    
    # API Efficiency Calculation
    compute_efficiency,
)

__all__ = [
    # Configuration
    'MARKER_ROLL_LENGTH_MM',
    'SAFETY_GAP_X_MM',
    'SAFETY_GAP_Y_MM',
    'APPLY_GAPS_TO_LENGTH',
    'BOUNDARY_EPS',
    
    # Data Models
    'Placement',
    'MarkerPlacedRect',
    'Marker',
    'TubeCut',
    'TubePattern',
    'TubePlan',
    'Line',
    
    # Fabric Nesting
    'compute_layout',
    'compute_layout_per_line',
    
    # Marker Nesting
    'build_markers_from_layout',
    'clear_marker_cache',
    
    # Aluminum Tube Cutting
    'compute_tube_plan',
    'validate_pieces',
    'pack_bfd',
    'improve_pair_swaps',
    'dedupe_patterns',
    
    # API Efficiency Calculation
    'compute_efficiency',
]

