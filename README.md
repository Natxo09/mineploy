# Mineploy

> Open-source Minecraft server management panel

**Status:** 🚧 Under active development

Mineploy is a modern, Docker-based panel for managing multiple Minecraft servers with a clean web interface.

## Features (Planned)

- 🎮 **Multi-version support**: Vanilla, Paper, Spigot, Fabric, Forge, NeoForge, Purpur
- 💻 **Interactive console**: Real-time logs and command execution via RCON
- 📁 **File management**: Upload/download mods, plugins, and worlds
- 💾 **Automated backups**: Schedule and restore backups with one click
- 👥 **Multi-user**: Role-based access control (Admin, Moderator, Viewer)
- 🐳 **Docker-powered**: Each server runs in an isolated container
- 🎨 **Modern UI**: Built with Next.js and shadcn/ui

## Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- MySQL (database)
- SQLAlchemy (async ORM)
- Alembic (migrations)
- aiodocker (Docker management)
- mcrcon (Minecraft RCON)

**Frontend:**
- Next.js 14
- TypeScript
- shadcn/ui + Tailwind CSS

## Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- OR: Python 3.11+ and MySQL 8.0+
- Node.js 18+ (for frontend)

### Quick Start with Docker (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/mineploy.git
cd mineploy
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start all services**
```bash
docker-compose up -d
```

The services will be available at:
- API: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000` (coming soon)

### Manual Backend Setup (Development)

1. **Clone and setup**
```bash
git clone https://github.com/yourusername/mineploy.git
cd mineploy/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

2. **Configure database**
```bash
cp ../.env.example .env
# Edit .env with MySQL credentials
```

3. **Start MySQL** (if not using Docker)
```bash
# Make sure MySQL is running and accessible
```

4. **Run migrations and start**
```bash
alembic upgrade head
uvicorn main:app --reload
```

API Documentation: `http://localhost:8000/docs`

### First Time Setup

On first run, you'll need to create an admin user:

1. Check setup status:
```bash
curl http://localhost:8000/api/v1/setup/status
```

2. Create admin user:
```bash
curl -X POST http://localhost:8000/api/v1/setup/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "your-secure-password"
  }'
```

## Development

### Running Tests

```bash
cd backend
source venv/bin/activate
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Code Quality

Format code with Black:
```bash
black .
```

Sort imports:
```bash
isort .
```

Lint:
```bash
flake8 .
```

Type checking:
```bash
mypy .
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback last migration:
```bash
alembic downgrade -1
```

## Project Structure

```
mineploy/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── core/                   # Core configuration
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── api/                    # API endpoints
│   ├── services/               # Business logic
│   ├── tests/                  # Tests
│   └── migrations/             # Alembic migrations
├── frontend/                   # Next.js app (coming soon)
├── docker-compose.yml          # Production setup
├── docker-compose.dev.yml      # Development setup
└── README.md
```

## Docker Deployment

### Using Docker Compose (Production)

1. **Configure environment**
```bash
cp .env.example .env
# Edit .env with production settings
```

2. **Generate secret key**
```bash
openssl rand -hex 32
# Add to .env as SECRET_KEY
```

3. **Start services**
```bash
docker-compose up -d
```

4. **Check logs**
```bash
docker-compose logs -f api
```

### Using Docker Compose (Development)

```bash
docker-compose -f docker-compose.dev.yml up
```

This mounts the source code for hot-reload.

## Environment Variables

Key environment variables (see `.env.example` for full list):

- `SECRET_KEY`: JWT secret (required, generate with `openssl rand -hex 32`)
- `DB_HOST`: MySQL host (default: `mysql`)
- `DB_USER`: MySQL user (default: `mineploy`)
- `DB_PASSWORD`: MySQL password (required)
- `DB_NAME`: Database name (default: `mineploy`)
- `CORS_ORIGINS`: Allowed origins (comma-separated)
- `MAX_SERVERS`: Maximum number of servers (default: `10`)
- `DEBUG`: Enable debug mode (default: `false`)

## API Endpoints

### Current Endpoints

- `GET /` - Redirect to API docs
- `GET /api/v1/health` - Health check
- `GET /api/v1/info` - Application info
- `GET /api/v1/setup/status` - Check setup status
- `POST /api/v1/setup/initialize` - Create first admin user

### Coming Soon

- Authentication (`/api/v1/auth/*`)
- Server management (`/api/v1/servers/*`)
- Console & RCON (`/api/v1/console/*`)
- File management (`/api/v1/files/*`)
- Backups (`/api/v1/backups/*`)

## Contributing

This is an open-source project and contributions are welcome!

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

## Roadmap

**Phase 1 - Foundation** ✅ (In Progress)
- [x] Project structure
- [x] Database models
- [x] Core configuration
- [x] Health check endpoints
- [x] Setup wizard
- [x] Docker setup
- [x] Testing infrastructure

**Phase 2 - Authentication**
- [ ] User authentication (JWT)
- [ ] User management
- [ ] Role-based permissions

**Phase 3 - Server Management**
- [ ] Create/start/stop/delete servers
- [ ] Docker container management
- [ ] RCON integration
- [ ] Console WebSocket

**Phase 4 - File Management**
- [ ] File explorer API
- [ ] Upload/download files
- [ ] Edit configuration files

**Phase 5 - Backups**
- [ ] Manual backup creation
- [ ] Scheduled backups
- [ ] Backup restoration

**Phase 6 - Frontend**
- [ ] Next.js app
- [ ] Dashboard
- [ ] Server management UI
- [ ] Terminal component
- [ ] File explorer UI

---

**Disclaimer:** This project is not affiliated with Mojang Studios or Microsoft. "Minecraft" is a trademark of Mojang Studios.
