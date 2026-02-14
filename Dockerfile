# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Prevents Python from writing .pyc files, and keeps logs unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional but safe)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better Docker layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the project
COPY src /app/src
COPY configs /app/configs
COPY scripts /app/scripts

# Make src importable
ENV PYTHONPATH=/app/src

# Default command shows help
CMD ["python", "-m", "bth_web.cli", "--help"]
