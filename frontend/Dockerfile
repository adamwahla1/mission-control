# Mission Control Frontend - Production Build
FROM node:20-alpine AS builder

# Install git
RUN apk add --no-cache git

# Clone the repo
RUN git clone https://github.com/adamwahla1/mission-control.git /mc

WORKDIR /mc/frontend

# Install and build
RUN npm ci
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /mc/frontend/dist /usr/share/nginx/html

# Create nginx config
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    location /assets/ { alias /usr/share/nginx/html/assets/; } \
    location /api/ { proxy_pass http://backend:8000/api/; } \
    location /ws { proxy_pass http://backend:8000/ws; proxy_http_version 1.1; proxy_set_header Upgrade $$http_upgrade; proxy_set_header Connection "upgrade"; } \
    location / { try_files $$uri $$uri/ /index.html; } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]