# Dockerfile для модуля 1 - Core Engine
# Build context: module-1-core-engine (текущая директория)

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy poetry files first for better caching
COPY pyproject.toml .
COPY README.md .

# Install Python dependencies
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY demo_data/ ./demo_data/
COPY scripts/ ./scripts/

# Expose ports
EXPOSE 8001 8002 8003 8004

# Accept SERVICE argument to specify which service to run
ARG SERVICE=orchestrator

# Ensure SERVICE is available at runtime
ENV SERVICE=${SERVICE}

# Default command - using shell format for variable expansion
CMD ["sh", "-c", "python -m src.${SERVICE}.main"]
