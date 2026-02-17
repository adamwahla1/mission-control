# Mission Control Frontend - Production Build
# This Dockerfile builds the frontend and bakes it into nginx

FROM node:20-alpine AS builder

# Install git
RUN apk add --no-cache git

# Clone the repo
RUN git clone https://github.com/adamwahla1/mission-control.git /mc

WORKDIR /mc/frontend

# Install dependencies and build
RUN npm ci
RUN npm run build

# Production stage - nginx with baked static files
FROM nginx:alpine

# Install curl for healthchecks
RUN apk add --no-cache curl

# Copy built assets from builder
COPY --from=builder /mc/frontend/dist /usr/share/nginx/html

# Copy the bulletproof nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Verify the CSS file exists (fail build if missing)
RUN ls -la /usr/share/nginx/html/assets/styles/ || (echo "ERROR: CSS file missing!" && exit 1)

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
