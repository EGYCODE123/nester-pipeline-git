"""Tests for nesting engine core functions."""

from nester.engine.core import Line, compute_efficiency


def test_engine_stub_shape():
    """Test compute_efficiency with basic Line input."""
    lines = [Line(line_id="L1", width_mm=2400, drop_mm=2100, qty=2)]
    results, totals = compute_efficiency(lines)
    
    assert results is not None
    assert len(results) == 1
    assert results[0]["line_id"] == "L1"
    assert "waste_factor_pct" in results[0]
    assert "utilization" in results[0]
    assert "used_length_mm" in results[0]
    
    assert totals is not None
    assert "eff_pct" in totals
    assert "waste_pct" in totals
    assert "total_area_m2" in totals
    assert "total_used_area_m2" in totals
    assert "total_waste_area_m2" in totals
    
    # Verify percentages are in 0-100 range
    assert 0 <= totals["eff_pct"] <= 100
    assert 0 <= totals["waste_pct"] <= 100
    assert 0 <= results[0]["utilization"] <= 100


def test_engine_empty_lines():
    """Test compute_efficiency with empty input."""
    results, totals = compute_efficiency([])
    
    assert results == []
    assert totals["eff_pct"] == 0.0
    assert totals["waste_pct"] == 100.0
    assert totals["total_area_m2"] == 0.0


def test_engine_multiple_lines():
    """Test compute_efficiency with multiple lines."""
    lines = [
        Line(line_id="L1", width_mm=2400, drop_mm=2100, qty=3),
        Line(line_id="L2", width_mm=1800, drop_mm=1500, qty=5),
    ]
    results, totals = compute_efficiency(lines)
    
    assert len(results) == 2
    assert totals["total_pieces"] == 8  # 3 + 5
    assert totals["eff_pct"] > 0
    assert totals["waste_pct"] < 100


def test_engine_with_candidate_widths():
    """Test compute_efficiency with candidate_widths_mm parameter."""
    lines = [Line(line_id="L1", width_mm=2400, drop_mm=2100, qty=2)]
    candidate_widths = [1900, 2050, 2400, 3000]
    results, totals = compute_efficiency(lines, candidate_widths_mm=candidate_widths)
    
    assert results is not None
    assert len(results) == 1
    assert results[0]["line_id"] == "L1"
    assert "waste_factor_pct" in results[0]
    assert totals is not None
    assert "eff_pct" in totals

