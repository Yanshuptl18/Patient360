# ==============================================================================
# Patient360 Frontend: Multi-Stage Production Dockerfile
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Frontend Assets
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Serve via Hardened Nginx
# ------------------------------------------------------------------------------
FROM nginx:1.27-alpine AS production

# Remove default nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled static assets from builder stage
COPY --from=builder /build/dist /usr/share/nginx/html

# Copy production Nginx reverse proxy configuration template
COPY deployment/nginx/nginx.conf.template /etc/nginx/templates/default.conf.template

# Default Cloud Run port and backend URL fallback
ENV PORT=8080
ENV BACKEND_URL=http://backend:8000

EXPOSE 8080

# Container liveness healthcheck
HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:${PORT:-8080}/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
