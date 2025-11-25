# Kvadrat Waste API Contract

## Overview

The Kvadrat Waste API calculates fabric waste efficiency for blind manufacturing orders. It uses First-Fit Decreasing Height (FFDH) nesting algorithms to optimize fabric usage and compute waste factors.

**Base URL**: `http://<host>:8000` (development)  
**API Version**: `1.0.0`

## Authentication

All API endpoints require Bearer token authentication via the `Authorization` header:

```
Authorization: Bearer <API_TOKEN>
```

The API token is configured via the `API_TOKEN` environment variable in `.env`.

## Endpoints

### GET /health

Health check endpoint to verify API availability.

**Request:**
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - API is healthy

---

### POST /api/v1/waste/efficiency

Calculate waste efficiency for a quote with multiple lines.

**Request:**
```http
POST /api/v1/waste/efficiency HTTP/1.1
Host: localhost:8000
Authorization: Bearer <API_TOKEN>
Content-Type: application/json
```

**Request Body:**
```json
{
  "quote_id": "Q-2025-00123",
  "model": "blinds",
  "available_widths_mm": [1900, 2050, 2400, 3000],
  "lines": [
    {
      "line_id": "L1",
      "width_mm": 2400,
      "drop_mm": 2100,
      "qty": 2,
      "fabric_code": "FAB001",
      "series": "SERIES-A"
    }
  ]
}
```

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quote_id` | string | Yes | Unique quote identifier |
| `model` | string | Yes | Product model: `"blinds"` or `"header"` |
| `available_widths_mm` | array of integers | No | Available roll widths in millimeters. Must be positive integers. Will be sorted and deduplicated automatically. If not provided, roll width is determined from item widths. |
| `lines` | array | Yes | List of order lines (max 1000) |

**Line Object Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `line_id` | string | Yes | Unique line identifier |
| `width_mm` | integer | Yes | Blind width in millimeters (must be > 0, max 3200) |
| `drop_mm` | integer | Yes | Blind drop/height in millimeters (must be > 0, max 5000) |
| `qty` | integer | Yes | Quantity (must be > 0) |
| `fabric_code` | string | No | Optional fabric code |
| `series` | string | No | Optional series identifier |

**Response (Success):**
```json
{
  "calc_id": "a1b2c3d4",
  "quote_id": "Q-1",
  "results": [
    {
      "line_id": "L1",
      "waste_factor_pct": 15.23,
      "utilization": 84.77,
      "used_length_mm": 4210.5,
      "blind_area_m2": 10.08,
      "roll_area_m2": 11.905,
      "waste_area_m2": 1.825,
      "roll_width_mm": 3000,
      "pieces": 2,
      "levels": 1
    }
  ],
  "totals": {
    "eff_pct": 84.77,
    "waste_pct": 15.23,
    "total_area_m2": 10.08,
    "total_used_area_m2": 11.905,
    "total_waste_area_m2": 1.825,
    "total_pieces": 2,
    "total_levels": 1
  },
  "version": "1.0.0",
  "message": "ok"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `calc_id` | string | Unique calculation ID (8 hex chars) |
| `quote_id` | string | Quote identifier from request |
| `results` | array | Per-line efficiency results |
| `totals` | object | Aggregated metrics |
| `version` | string | API version |
| `message` | string | Status message ("ok" on success) |

**Result Object Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `line_id` | string | Line identifier |
| `waste_factor_pct` | float | Waste percentage (waste_area / blind_area × 100) |
| `utilization` | float | Utilization percentage (0-100) |
| `used_length_mm` | float | Fabric length used in millimeters |
| `blind_area_m2` | float | Total blind area in square meters |
| `roll_area_m2` | float | Total roll area used in square meters |
| `waste_area_m2` | float | Waste area in square meters |
| `roll_width_mm` | integer | Roll width used in millimeters |
| `pieces` | integer | Number of pieces |
| `levels` | integer | Number of shelf levels |

**Totals Object Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `eff_pct` | float | Overall efficiency percentage (0-100) |
| `waste_pct` | float | Overall waste percentage (0-100) |
| `total_area_m2` | float | Total blind area in square meters |
| `total_used_area_m2` | float | Total roll area used in square meters |
| `total_waste_area_m2` | float | Total waste area in square meters |
| `total_pieces` | integer | Total number of pieces |
| `total_levels` | integer | Total number of levels |

**Status Codes:**
- `200 OK` - Calculation successful
- `400 Bad Request` - Invalid request (validation error)
- `401 Unauthorized` - Missing or invalid API token
- `500 Internal Server Error` - Server error during calculation

**Error Response Format:**
```json
{
  "error": "bad_request",
  "details": "Maximum 1000 lines allowed per request"
}
```

or

```json
{
  "error": "unauthorized",
  "details": "Missing or invalid Authorization header"
}
```

## Units and Percentages

- **Dimensions**: All measurements in millimeters (mm)
- **Areas**: All areas in square meters (m²)
- **Percentages**: All percentages are 0-100 scale (not 0-1)
  - `waste_factor_pct`: Waste area divided by blind area × 100
  - `utilization`: Blind area divided by roll area × 100
  - `eff_pct`: Overall efficiency percentage
  - `waste_pct`: Overall waste percentage

## Limits

- **Maximum lines per request**: 1000
- **Maximum width**: 3200mm
- **Maximum drop**: 5000mm
- **Target response time**: < 5 seconds for typical requests
- **Maximum pieces per line**: 1000 (enforced during nesting)

## Examples

### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/waste/efficiency \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quote_id": "Q-2025-00123",
    "model": "blinds",
    "available_widths_mm": [1900, 2050, 2400, 3000],
    "lines": [
      {
        "line_id": "L1",
        "width_mm": 2400,
        "drop_mm": 2100,
        "qty": 2
      }
    ]
  }'
```

### Python Example

```python
import requests

url = "http://localhost:8000/api/v1/waste/efficiency"
headers = {
    "Authorization": "Bearer YOUR_API_TOKEN",
    "Content-Type": "application/json"
}
payload = {
    "quote_id": "Q-2025-00123",
    "model": "blinds",
    "available_widths_mm": [1900, 2050, 2400, 3000],
    "lines": [
        {
            "line_id": "L1",
            "width_mm": 2400,
            "drop_mm": 2100,
            "qty": 2
        }
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

## Algorithm Details

The API uses the **First-Fit Decreasing Height (FFDH)** algorithm for fabric nesting:

1. Items are sorted by decreasing height (drop)
2. Items are placed left-to-right across the roll width within shelves
3. New shelves are created when no more items fit in the current shelf
4. Gaps between items and shelves are minimized
5. Post-pack compaction merges adjacent equal-height shelves when possible

The algorithm ensures:
- No items are cut across marker boundaries (5.9m segments)
- Optimal fabric utilization
- Deterministic results for the same input

## Notes

- The API automatically determines the optimal roll width based on the maximum item width
- All calculations assume 0mm gap between pieces (configurable in future versions)
- The `calc_id` field can be used for request tracking and debugging
- Check logs in the `logs/` directory for detailed request/response information

