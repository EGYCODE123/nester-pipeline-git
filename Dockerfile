# Dockerfile for Nester API
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 nester && \
    chown -R nester:nester /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY nester_api/ ./nester_api/
COPY nester/ ./nester/

# Create logs directory
RUN mkdir -p /app/logs && \
    chown -R nester:nester /app/logs

# Switch to non-root user
USER nester

# Expose port
EXPOSE 8000

# Set environment defaults
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV API_LOG_LEVEL=info
ENV PYTHONUNBUFFERED=1

# Run uvicorn with multiple workers
# Use PORT env variable (Railway provides this) or fallback to 8000
CMD ["sh", "-c", "uvicorn nester_api.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4"]



