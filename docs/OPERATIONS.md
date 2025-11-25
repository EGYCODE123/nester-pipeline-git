# Operations Guide - Kvadrat Waste API

## Service Management

### Installation

Install the Windows service using NSSM:

```powershell
cd "Z:\CPQ Waste\nester-pipeline"
.\infra\windows\install_service.ps1
```

Or with custom service name and port:

```powershell
.\infra\windows\install_service.ps1 -ServiceName "KvadratWasteAPI" -Port 8000
```

**Prerequisites:**
- NSSM must be installed and in PATH (download from https://nssm.cc/download)
- Virtual environment must exist (run `scripts/dev_run.ps1` first to create it)
- `.env` file must exist with `API_TOKEN` configured

### Starting the Service

```powershell
nssm start KvadratWasteAPI
```

### Stopping the Service

```powershell
nssm stop KvadratWasteAPI
```

### Restarting the Service

```powershell
nssm restart KvadratWasteAPI
```

### Uninstalling the Service

```powershell
cd "Z:\CPQ Waste\nester-pipeline"
.\infra\windows\uninstall_service.ps1
```

Or with custom service name:

```powershell
.\infra\windows\uninstall_service.ps1 -ServiceName "KvadratWasteAPI"
```

## Log Files

### Service Logs

Service output and error logs are written to:
- `logs/service_out.log` - Standard output
- `logs/service_err.log` - Standard error

### Application Logs

Application request/response logs are written to:
- `logs/waste_api_YYYY-MM-DD_HH-MM-SS.log` - Rotated log files

**Log Rotation:**
- Maximum file size: 10 MB
- Retention: 10 files
- Old logs are automatically deleted

### Viewing Logs

**PowerShell:**
```powershell
# View service output
Get-Content "Z:\CPQ Waste\nester-pipeline\logs\service_out.log" -Tail 50

# View application logs
Get-Content "Z:\CPQ Waste\nester-pipeline\logs\waste_api_*.log" -Tail 50
```

**Follow logs in real-time:**
```powershell
Get-Content "Z:\CPQ Waste\nester-pipeline\logs\service_out.log" -Wait
```

## Service Configuration

### Service Properties

View service properties:
```powershell
nssm get KvadratWasteAPI AppDirectory
nssm get KvadratWasteAPI AppParameters
nssm get KvadratWasteAPI AppEnvironmentExtra
```

### Update Service Configuration

Update environment variables:
```powershell
nssm set KvadratWasteAPI AppEnvironmentExtra "API_TOKEN=your_new_token"
```

Update port:
```powershell
nssm set KvadratWasteAPI AppParameters "nester.api.app:app --host 0.0.0.0 --port 8001"
```

### Service Status

Check if service is running:
```powershell
Get-Service KvadratWasteAPI
```

## Troubleshooting

### Service Won't Start

1. Check service logs:
   ```powershell
   Get-Content "Z:\CPQ Waste\nester-pipeline\logs\service_err.log"
   ```

2. Verify virtual environment exists:
   ```powershell
   Test-Path "Z:\CPQ Waste\nester-pipeline\.venv\Scripts\uvicorn.exe"
   ```

3. Verify .env file exists and has API_TOKEN:
   ```powershell
   Get-Content "Z:\CPQ Waste\nester-pipeline\.env"
   ```

4. Test manually:
   ```powershell
   cd "Z:\CPQ Waste\nester-pipeline"
   .\.venv\Scripts\uvicorn nester.api.app:app --host 0.0.0.0 --port 8000
   ```

### Service Stops Unexpectedly

1. Check Windows Event Viewer for service errors
2. Review application logs in `logs/` directory
3. Verify API_TOKEN is valid
4. Check for port conflicts:
   ```powershell
   netstat -ano | findstr :8000
   ```

### API Not Responding

1. Verify service is running:
   ```powershell
   Get-Service KvadratWasteAPI | Select-Object Status
   ```

2. Test health endpoint:
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8000/health"
   ```

3. Check firewall rules (Windows Firewall may block port 8000)

## Manual Development Run

For development, you can run the API directly without installing as a service:

```powershell
cd "Z:\CPQ Waste\nester-pipeline"
.\scripts\dev_run.ps1
```

This will:
- Create virtual environment if missing
- Install dependencies
- Start the API server on http://localhost:8000

## Environment Variables

The service reads configuration from `.env` file in the project root:

- `API_TOKEN` - Required API authentication token
- `LOG_DIR` - Log directory (default: `logs`)
- `SQL_CONN` - Optional database connection string

## Backup and Recovery

### Backup Configuration

Before making changes, backup:
- `.env` file (contains API token)
- Service configuration (export via NSSM if needed)

### Restore Service

1. Restore `.env` file
2. Reinstall service using `install_service.ps1`
3. Start service

## Monitoring

### Health Check

Monitor service health:
```powershell
# PowerShell script to check health
$response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
$response.StatusCode  # Should be 200
```

### Performance Monitoring

- Monitor log file sizes in `logs/` directory
- Check service memory usage in Task Manager
- Review API response times in application logs









