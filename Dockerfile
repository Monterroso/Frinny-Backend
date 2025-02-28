FROM --platform=linux/arm64 python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Clean pycache files
RUN find . -type d -name __pycache__ -exec rm -rf {} +

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app
ENV FLASK_ENV=development

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Run the application
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:create_app()"] 