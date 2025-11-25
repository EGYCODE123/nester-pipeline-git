# Kvadrat Waste API - Enterprise Deployment Guide

## Overview

The Kvadrat Waste API is a production-ready microservice for calculating fabric waste efficiency in CPQ (Configure, Price, Quote) systems. This service provides RESTful endpoints to compute optimal fabric utilization for window covering orders.

### Key Features

- **RESTful API**: FastAPI-based service with OpenAPI documentation
- **Authentication**: Bearer token/API key authentication
- **Rate Limiting**: Per-client rate limiting to prevent abuse
- **Structured Logging**: Centralized logging with correlation IDs for request tracing
- **Health Checks**: Liveness and readiness endpoints for monitoring
- **Docker Support**: Containerized for easy deployment
- **Production Ready**: Non-root user, proper error handling, comprehensive testing

## API Contract

### Endpoint: `POST /api/v1/waste/efficiency`

Calculate waste efficiency for a quote.

**Request Body:**
```json
{
  "quote_id": "Q-TEST-001",
  "model": "blinds",
  "available_widths_mm": [1900, 2050, 2400, 3000],
  "lines": [
    {
      "line_id": "L1",
      "width_mm": 2300,
      "drop_mm": 2100,
      "qty": 2,
      "fabric_code": "FAB001",
      "series": "SERIES-A"
    }
  ]
}
```

**Response:**
```json
{
  "calc_id": "a1b2c3d4",
  "quote_id": "Q-TEST-001",
  "results": [
    {
      "line_id": "L1",
      "waste_factor_pct": 12.5,
      "utilization": 87.5,
      "used_length_mm": 2100.0,
      "blind_area_m2": 9.66,
      "roll_area_m2": 11.04,
      "waste_area_m2": 1.38,
      "roll_width_mm": 3000,
      "pieces": 2,
      "levels": 1
    }
  ],
  "totals": {
    "eff_pct": 87.5,
    "waste_pct": 12.5,
    "total_area_m2": 9.66,
    "total_used_area_m2": 11.04,
    "total_waste_area_m2": 1.38,
    "total_pieces": 2,
    "total_levels": 1
  },
  "version": "1.0.0",
  "message": "ok"
}
```

**Authentication:** Required via `Authorization: Bearer <token>` header

**Rate Limit:** 60 requests per minute per client

## Prerequisites

- **Python**: 3.11 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+ (optional, for local development)
- **Reverse Proxy**: Nginx or IIS (for HTTPS termination in production)

## Local Development

### 1. Clone and Setup

```bash
cd nester-pipeline
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
API_HOST=0.0.0.0
API_PORT=8000
API_LOG_LEVEL=info
API_ALLOWED_ORIGINS=
API_KEY=your-secure-api-key-here
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=20
LOG_DIR=logs
```

### 3. Run the API

```bash
# Option 1: Using uvicorn directly
uvicorn nester_api.app.main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Using Python module
python -m nester_api

# Option 3: Using Docker Compose
docker-compose up --build
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/health/live

# API docs
open http://localhost:8000/docs
```

## Docker Deployment

### Building the Image

```bash
docker build -t nester-api:latest .
```

### Running the Container

```bash
docker run -d \
  --name nester-api \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  nester-api:latest
```

### Using Docker Compose

```bash
docker-compose up -d
```

### Verifying Container

```bash
docker logs nester-api
docker exec nester-api curl http://localhost:8000/health/live
```

## Production Deployment on Company Server

### Step 1: Prepare the Server

1. **Install Docker** (if not already installed):
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Windows Server
   # Download Docker Desktop from docker.com
   ```

2. **Create deployment directory**:
   ```bash
   mkdir -p /opt/nester-api
   cd /opt/nester-api
   ```

3. **Copy files to server**:
   - `Dockerfile`
   - `docker-compose.yml`
   - `requirements.txt`
   - `nester_api/` directory
   - `nester/` directory
   - `.env` file (with production API key)

### Step 2: Configure Environment

Create `.env` file on the server:

```env
API_HOST=0.0.0.0
API_PORT=8000
API_LOG_LEVEL=info
API_ALLOWED_ORIGINS=https://your-cpq-domain.com
API_KEY=<generate-strong-random-key>
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=20
LOG_DIR=logs
```

**Generate a secure API key:**
```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### Step 3: Build and Run

```bash
cd /opt/nester-api
docker-compose up -d --build
```

### Step 4: Verify Deployment

```bash
# Check container status
docker ps | grep nester-api

# Check logs
docker logs nester-api

# Test health endpoint
curl http://localhost:8000/health/live
```

## Reverse Proxy Configuration

### Nginx Configuration (Linux)

Create `/etc/nginx/sites-available/nester-api`:

```nginx
upstream nester_api {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name api.yourcompany.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://nester_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no auth required)
    location /health/ {
        proxy_pass http://nester_api;
        access_log off;
    }
}
```

Enable and restart:

```bash
ln -s /etc/nginx/sites-available/nester-api /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### IIS Configuration (Windows Server)

1. **Install IIS** and **URL Rewrite** module

2. **Create Application Pool**:
   - Name: `nester-api`
   - .NET CLR Version: No Managed Code
   - Managed Pipeline Mode: Integrated

3. **Create Reverse Proxy Rule**:
   - Open IIS Manager
   - Select your site
   - URL Rewrite → Add Rule → Reverse Proxy
   - Inbound URL: `(.*)`
   - Rewrite URL: `http://localhost:8000/{R:1}`
   - Check "Enable SSL Offloading"

4. **Configure SSL**:
   - Bind HTTPS on port 443
   - Select your SSL certificate

5. **Set Headers** (via web.config):
   ```xml
   <system.webServer>
     <rewrite>
       <rules>
         <rule name="ReverseProxy" stopProcessing="true">
           <match url="(.*)" />
           <action type="Rewrite" url="http://localhost:8000/{R:1}" />
           <serverVariables>
             <set name="HTTP_X_FORWARDED_FOR" value="{REMOTE_ADDR}" />
             <set name="HTTP_X_REAL_IP" value="{REMOTE_ADDR}" />
           </serverVariables>
         </rule>
       </rules>
     </rewrite>
   </system.webServer>
   ```

## Experlogix CPQ Integration

### Step 1: Update CPQ Model

1. **Open your Experlogix CPQ model** in the CPQ Designer

2. **Locate the waste calculation logic** (likely in a custom action or calculation)

3. **Update the API endpoint URL**:
   - Old: `http://localhost:8000/api/v1/waste/efficiency`
   - New: `https://api.yourcompany.com/api/v1/waste/efficiency`

4. **Add authentication header**:
   ```csharp
   request.Headers.Add("Authorization", "Bearer YOUR_API_KEY_HERE");
   ```

### Step 2: Update .NET Bridge DLL

If you're using the `Kvadrat.NesterBridge.dll`:

1. **Update the API URL** in `EffClient.cs`:
   ```csharp
   private const string API_BASE_URL = "https://api.yourcompany.com";
   ```

2. **Update the API key**:
   ```csharp
   private const string API_KEY = "YOUR_API_KEY_HERE";
   ```

3. **Rebuild the DLL**:
   ```powershell
   .\build.ps1
   ```

4. **Copy both DLLs to CPQ**:
   - `Kvadrat.NesterBridge.dll`
   - `Newtonsoft.Json.dll`

### Step 3: Test Integration

1. **Create a test quote** in CPQ
2. **Trigger the waste calculation**
3. **Verify the response** in CPQ logs
4. **Check API logs** on the server:
   ```bash
   docker logs nester-api
   ```

## Monitoring and Health Checks

### Health Endpoints

- **Liveness**: `GET /health/live`
  - Returns 200 if process is running
  - Use for basic health monitoring

- **Readiness**: `GET /health/ready`
  - Returns 200 if app is initialized and engine is importable
  - Use for load balancer health checks

### Logging

Logs are written to:
- **Console**: Structured JSON format
- **File**: `logs/nester_api.log` (rotates at 10MB, keeps 10 backups)

Log format:
```
2024-01-15 10:30:45 INFO     [a1b2c3d4] nester_api: Request started: calc_id=..., quote_id=Q-001
```

### Monitoring Integration

**Prometheus** (if needed):
- Add `/metrics` endpoint using `prometheus-fastapi-instrumentator`

**Grafana Dashboards**:
- Request rate
- Response times
- Error rates
- Rate limit hits

## Troubleshooting

### API Not Responding

1. **Check container status**:
   ```bash
   docker ps -a | grep nester-api
   ```

2. **Check logs**:
   ```bash
   docker logs nester-api
   ```

3. **Verify port binding**:
   ```bash
   netstat -tuln | grep 8000
   ```

4. **Test locally**:
   ```bash
   curl http://localhost:8000/health/live
   ```

### Authentication Failures

1. **Verify API key** in `.env` file matches CPQ configuration
2. **Check request headers**:
   ```bash
   curl -v -H "Authorization: Bearer YOUR_KEY" \
     http://localhost:8000/api/v1/waste/efficiency \
     -d @test_request.json
   ```

### Rate Limit Errors

1. **Check rate limit settings** in `.env`
2. **Review logs** for rate limit hits
3. **Adjust limits** if needed (increase `RATE_LIMIT_PER_MINUTE`)

### Docker Build Failures

1. **Check Dockerfile syntax**
2. **Verify all files are present**:
   ```bash
   ls -la nester_api/
   ls -la nester/
   ```

3. **Build with verbose output**:
   ```bash
   docker build --progress=plain -t nester-api .
   ```

### CPQ Integration Issues

1. **Verify SSL certificate** is valid
2. **Check firewall rules** allow HTTPS traffic
3. **Review CPQ logs** for HTTP errors
4. **Test API directly** with curl/Postman

## Upgrades and Maintenance

### Updating the API

1. **Pull latest code**:
   ```bash
   cd /opt/nester-api
   git pull  # or copy new files
   ```

2. **Rebuild container**:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

3. **Verify health**:
   ```bash
   curl https://api.yourcompany.com/health/ready
   ```

### API Key Rotation

1. **Generate new key** (see Step 2 above)
2. **Update `.env` file** on server
3. **Restart container**:
   ```bash
   docker-compose restart
   ```
4. **Update CPQ configuration** with new key
5. **Test integration**

### Log Rotation

Logs are automatically rotated at 10MB. To manually clean:

```bash
# View log files
ls -lh logs/

# Archive old logs
tar -czf logs-archive-$(date +%Y%m%d).tar.gz logs/*.log.*

# Clean old logs (keep last 30 days)
find logs/ -name "*.log.*" -mtime +30 -delete
```

## Security Best Practices

1. **Use strong API keys**: Minimum 32 characters, random
2. **Enable HTTPS**: Always use SSL/TLS in production
3. **Restrict CORS**: Set `API_ALLOWED_ORIGINS` to specific domains
4. **Firewall rules**: Only allow necessary ports (443 for HTTPS)
5. **Regular updates**: Keep Docker and dependencies updated
6. **Monitor logs**: Set up alerts for authentication failures
7. **Rate limiting**: Adjust limits based on expected load

## Support and Contact

For issues or questions:
- **API Documentation**: `https://api.yourcompany.com/docs`
- **Health Status**: `https://api.yourcompany.com/health/live`
- **Logs**: Check `logs/nester_api.log` on the server

## License

Proprietary - Internal use only



