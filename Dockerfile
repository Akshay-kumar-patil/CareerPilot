# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for WeasyPrint and other core tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libgobject-2.0-0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code required for backend
COPY backend/ ./backend/
COPY templates/ ./templates/
COPY main.py .

# Create data directories
RUN mkdir -p data/uploads data/generated data/chroma_db

# Expose port (default for uvicorn)
EXPOSE 8000

# Start FastAPI without reload for production
# Using shell form to resolve the $PORT environment variable
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
