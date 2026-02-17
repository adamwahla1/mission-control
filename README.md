# Mission Control Dashboard

AI Agent Mission Control Dashboard for monitoring and managing agent workflows.

## Quick Start

### 1. Clone and Deploy

```bash
git clone https://github.com/YOUR_USERNAME/mission-control.git
cd mission-control
docker-compose up -d
```

### 2. Access

- Dashboard: http://YOUR_VPS_IP:8080
- API Docs: http://YOUR_VPS_IP:8080/api/v1/docs

## Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind
- **Backend**: FastAPI + PostgreSQL + Redis
- **WebSocket**: Real-time updates
- **Auth**: JWT with httpOnly cookies

## Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 8080 | Nginx serving React app |
| Backend API | 8000 (internal) | FastAPI REST + WebSocket |
| PostgreSQL | 5432 (internal) | Database |
| Redis | 6379 (internal) | Cache + Pub/Sub |

## Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
DB_PASSWORD=your-secure-password
JWT_SECRET=your-jwt-secret
TELEGRAM_BOT_TOKEN=optional-bot-token
```

## Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Update (pull latest and restart)
git pull
docker-compose up --build -d
```

## Development

Managed by OpenClaw AI. For updates, contact via Telegram.

## Security

- JWT stored in httpOnly cookies
- XSS protection with DOMPurify
- CSRF token validation
- CORS configured
- WCAG 2.1 AA accessibility compliant

## License

Private - For personal use only.