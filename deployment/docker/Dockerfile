FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Azure Container Apps uses PORT env var, default to 8000)
EXPOSE 8000

# Health check (Container Apps will map the port correctly)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; import os; port = os.getenv('PORT', '8000'); requests.get(f'http://localhost:{port}/health')"

# Run application (use PORT env var for Azure Container Apps compatibility)
CMD sh -c "PORT=\${PORT:-8000} && uvicorn api.main:app --host 0.0.0.0 --port \$PORT"
