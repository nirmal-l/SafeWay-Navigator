# ── Stage 1: Build (prebuild graph + seed data) ──────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for geospatial packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-build road graphs during docker build (uses build RAM, not runtime RAM)
RUN python data/prebuild_graph.py


# ── Stage 2: Production Runtime ──────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-dev \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy pre-built graph pickles from builder stage
COPY --from=builder /app/data/*.pkl /app/data/

EXPOSE 8000

# Use gunicorn with uvicorn workers for production
CMD ["gunicorn", "main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "1", \
     "--timeout", "120"]
