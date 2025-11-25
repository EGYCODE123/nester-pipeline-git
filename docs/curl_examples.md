# cURL Examples for Kvadrat Waste API

## Prerequisites

Replace `YOUR_API_TOKEN` with your actual API token from `.env` file.

## Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Calculate Efficiency - Single Line

```bash
curl -X POST http://localhost:8000/api/v1/waste/efficiency \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quote_id": "Q-1",
    "model": "blinds",
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

## Calculate Efficiency - Multiple Lines

```bash
curl -X POST http://localhost:8000/api/v1/waste/efficiency \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quote_id": "Q-2",
    "model": "blinds",
    "lines": [
      {
        "line_id": "L1",
        "width_mm": 2400,
        "drop_mm": 2100,
        "qty": 3,
        "fabric_code": "FAB001"
      },
      {
        "line_id": "L2",
        "width_mm": 1800,
        "drop_mm": 1500,
        "qty": 5,
        "fabric_code": "FAB002"
      }
    ]
  }'
```

## Calculate Efficiency - Header Model

```bash
curl -X POST http://localhost:8000/api/v1/waste/efficiency \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quote_id": "Q-3",
    "model": "header",
    "lines": [
      {
        "line_id": "L1",
        "width_mm": 2000,
        "drop_mm": 500,
        "qty": 4
      }
    ]
  }'
```

## Test Authentication Failure

```bash
curl -X POST http://localhost:8000/api/v1/waste/efficiency \
  -H "Authorization: Bearer INVALID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quote_id": "Q-1",
    "model": "blinds",
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

**Expected Response (401):**
```json
{
  "detail": {
    "error": "unauthorized",
    "details": "Invalid API token"
  }
}
```

## Using from PowerShell

```powershell
$token = "YOUR_API_TOKEN"
$body = @{
    quote_id = "Q-1"
    model = "blinds"
    lines = @(
        @{
            line_id = "L1"
            width_mm = 2400
            drop_mm = 2100
            qty = 2
        }
    )
} | ConvertTo-Json

$headers = @{
    Authorization = "Bearer $token"
    "Content-Type" = "application/json"
}

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/waste/efficiency" -Method Post -Headers $headers -Body $body
```









