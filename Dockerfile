# Multi-stage build for the entire application
FROM node:20-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
COPY frontend/yarn.lock ./

# Install frontend dependencies
RUN yarn install --frozen-lockfile

# Copy frontend source code
COPY frontend/ ./

# Build the frontend application
RUN yarn build

# Backend stage
FROM python:3.11-slim AS backend-builder

# Set working directory for backend
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libffi-dev \
        libssl-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./

# Final stage - Nginx to serve both frontend and backend
FROM nginx:alpine

# Install Python runtime and dependencies for backend
RUN apk add --no-cache python3 py3-pip curl

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy built frontend from frontend stage
COPY --from=frontend-builder /app/frontend/build /usr/share/nginx/html

# Copy backend code
COPY --from=backend-builder /app/backend /app/backend

# Copy custom nginx configuration for Railway
COPY docker/nginx/nginx-railway.conf /etc/nginx/conf.d/default.conf

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose port (Railway will set the PORT environment variable)
EXPOSE 3000 8001

# Start both services
CMD ["/start.sh"] 