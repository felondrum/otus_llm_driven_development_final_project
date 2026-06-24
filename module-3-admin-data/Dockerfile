# ===========================================
# Dockerfile for Chameleon Admin API + UI
# ===========================================

# ===========================================
# Stage 1: Build React frontend
# ===========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY src/frontend_admin/package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY src/frontend_admin/ ./

# Build frontend
RUN npm run build

# ===========================================
# Stage 2: Python backend
# ===========================================
FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy poetry files
COPY pyproject.toml .

# Install Python dependencies if pyproject.toml exists
RUN if [ -f pyproject.toml ]; then \
    pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main \
    && pip install grpcio redis httpx[socks] httpx[http2]; \
    fi

# Copy application code
COPY src/ ./src/

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist /app/src/frontend/dist

# Expose ports (API on 8100, UI will be served from same port via static files)
EXPOSE 8100

# Set PYTHONPATH to include src directory
ENV PYTHONPATH=/app/src

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8100/ || exit 1

# Default command
CMD ["python", "src/admin_api/main.py"]
