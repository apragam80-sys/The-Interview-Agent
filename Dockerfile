# ========================================================
# Stage 1: Build React Frontend UI
# ========================================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci || npm install

COPY frontend/ ./
RUN npm run build

# ========================================================
# Stage 2: Python Backend & Unified Production Image
# ========================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application and data
COPY backend /app
COPY data /data

# Copy compiled React frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend_dist

# Set environment variables
ENV PYTHONPATH=/app
ENV FRONTEND_DIST=/app/frontend_dist
ENV PORT=8000

EXPOSE 8000

# Railway dynamically injects $PORT at runtime
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
