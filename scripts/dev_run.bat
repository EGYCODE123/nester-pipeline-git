@echo off
cd /d "Z:\CPQ Waste\nester-pipeline"

if not exist .venv (
    echo Creating virtual environment...
    py -m venv .venv
)

echo Installing dependencies...
.\.venv\Scripts\pip install -r nester\requirements.txt

echo Starting API server...
echo API will be available at http://localhost:8000
echo Press Ctrl+C to stop
.\.venv\Scripts\uvicorn nester.api.app:app --host 0.0.0.0 --port 8000









