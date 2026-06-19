# ===========================================
# Dockerfile для модуля 2 - Chat Frontend
# ===========================================
# Простая сборка:
# 1. Backend stage - Python FastAPI + WebSocket
# 2. Production stage - объединение

# ===========================================
# Stage 1: Setup Python backend
# ===========================================
FROM python:3.11-slim AS backend-builder

WORKDIR /app/backend

# Install dependencies via pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/backend/ ./src/

# Copy pre-generated proto files
COPY src/backend/grpc_client/proto_gen/chameleon /app/backend/chameleon/

# ===========================================
# Stage 2: Production image
# ===========================================
FROM python:3.11-slim

# Install curl for health check
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend from builder (includes installed packages)
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy frontend build (dist folder - should be built locally)
COPY src/frontend/dist /app/frontend/dist

# Copy backend source (including __init__.py for proper Python package)
COPY --from=backend-builder /app/backend/src/ /app/backend/

# Copy config (optional)
RUN mkdir -p /app/config || true

# Set working directory for backend
WORKDIR /app/backend

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV ORCHESTRATOR_HOST=host.docker.internal
ENV ORCHESTRATOR_PORT=8001

# Expose ports (HTTP and WebSocket on same port)
EXPOSE ${PORT}

# Health check using curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

# Run backend server
CMD ["python", "-m", "main"]
