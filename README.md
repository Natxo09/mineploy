# Mineploy

> Open-source Minecraft server management panel

**Status:** 🚧 Under active development | **Phase 7 In Progress** 🚧

[![Tests](https://img.shields.io/badge/tests-87%2F87%20passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-73%25-yellow)]()

Mineploy is a modern, Docker-based panel for managing multiple Minecraft servers with a clean web interface.

**Current Status:**
- ✅ Backend API deployed and running
- ✅ Database migrations applied
- ✅ Setup wizard (backend + frontend)
- ✅ Authentication system complete
- ✅ User management (CRUD)
- ✅ Server-specific permissions system
- ✅ Frontend authentication flow (login/logout/setup)
- ✅ Theme system (dark/light mode)
- ✅ Basic dashboard page
- ✅ Server management backend (CRUD, start/stop/restart, stats)
- ✅ Docker service integration (container management)
- 📝 Next: Server management UI

## Features (Planned)

- 🎮 **Multi-version support**: Vanilla, Paper, Spigot, Fabric, Forge, NeoForge, Purpur
- 💻 **Interactive console**: Real-time logs and command execution via RCON
- 📁 **File management**: Upload/download mods, plugins, and worlds
- 💾 **Automated backups**: Schedule and restore backups with one click
- 👥 **Multi-user**: Role-based access control (Admin, Moderator, Viewer)
- 🐳 **Docker-powered**: Each server runs in an isolated container
- 🎨 **Modern UI**: Built with Next.js and shadcn/ui

## User Permissions System

Mineploy implements a dual-layer permission system combining **global roles** with **server-specific permissions** for fine-grained access control.

### Global Roles

Every user has a global role that determines their system-wide capabilities:

| Role | Description | Capabilities |
|------|-------------|--------------|
| **ADMIN** | System administrator | Full access to everything: all servers, all users, all settings |
| **MODERATOR** | Server moderator | Can manage assigned servers, view other servers (read-only) |
| **VIEWER** | Read-only user | Can only view assigned servers, no modifications |

### Server-Specific Permissions

In addition to global roles, users can be granted specific permissions on individual servers. This allows admins to create custom access patterns:

| Permission | Description | Example Use Case |
|-----------|-------------|------------------|
| **VIEW** | Read-only access | View server status, logs, and settings |
| **CONSOLE** | Console access | Execute commands via RCON |
| **START_STOP** | Power control | Start, stop, and restart the server |
| **FILES** | File management | Upload/download/edit files (mods, plugins, configs) |
| **BACKUPS** | Backup management | Create, restore, and delete backups |
| **MANAGE** | Full server control | All of the above + server settings and deletion |

### Permission Inheritance

- **ADMIN** role: Bypasses all checks, has implicit `MANAGE` permission on all servers
- **MODERATOR** role: Has implicit `VIEW` permission on all servers
- **VIEWER** role: Only has access to explicitly assigned servers

### Permission Assignment Examples

**Example 1: Developer with Console Access**
```
User: "dev_john"
Global Role: VIEWER
Server Permissions:
  - "survival-server": [CONSOLE, VIEW]
  - "creative-server": [VIEW]
```
John can execute commands on the survival server but only view the creative server.

**Example 2: Backup Manager**
```
User: "backup_admin"
Global Role: MODERATOR
Server Permissions:
  - "survival-server": [BACKUPS, FILES, VIEW]
```
This user can manage backups and files on the survival server, plus view all other servers (via MODERATOR role).

**Example 3: Full Server Manager**
```
User: "server_manager"
Global Role: MODERATOR
Server Permissions:
  - "survival-server": [MANAGE]
  - "creative-server": [MANAGE]
```
Full control over two specific servers, read-only access to others.

### Implementation Details

The permission system is implemented via:

1. **UserServerPermission Model**: Many-to-many relationship table storing user-server-permission mappings
2. **Permission Checks**: Middleware and decorators validate permissions before allowing actions
3. **API Endpoints**: Admins can assign/revoke permissions via `/api/v1/users/{id}/permissions`

### Database Schema (Planned)

```sql
CREATE TABLE user_server_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    server_id INT NOT NULL,
    permissions JSON NOT NULL,  -- Array of permission strings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_server (user_id, server_id)
);
```

**Example JSON:**
```json
["VIEW", "CONSOLE", "START_STOP"]
```

### API Endpoints (Planned)

**Assign permissions to user on a server:**
```bash
POST /api/v1/users/{user_id}/permissions
{
  "server_id": 1,
  "permissions": ["VIEW", "CONSOLE", "START_STOP"]
}
```

**Get user permissions on all servers:**
```bash
GET /api/v1/users/{user_id}/permissions
```

**Remove user access from a server:**
```bash
DELETE /api/v1/users/{user_id}/permissions/{server_id}
```

**Check if user can perform action:**
```bash
GET /api/v1/users/me/permissions/{server_id}
# Returns: { "permissions": ["VIEW", "CONSOLE"], "effective_role": "MODERATOR" }
```

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
│   │   ├── dependencies.py
│   │   └── security.py
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py
│   │   ├── server.py
│   │   ├── user_server_permission.py
│   │   └── refresh_token.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── user.py
│   │   ├── server.py
│   │   ├── permission.py
│   │   └── setup.py
│   ├── api/                    # API endpoints
│   │   ├── setup.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── permissions.py
│   │   └── servers.py          # ✅ NEW
│   ├── services/               # Business logic
│   │   ├── permission_service.py
│   │   └── docker_service.py   # ✅ NEW
│   ├── tests/                  # Tests (87 tests)
│   │   ├── test_auth.py
│   │   ├── test_users.py
│   │   ├── test_security.py
│   │   ├── test_config.py
│   │   ├── test_health.py
│   │   ├── test_servers.py     # ✅ NEW (24 tests)
│   │   ├── test_docker_service.py  # ✅ NEW (17 tests)
│   │   └── conftest.py
│   └── migrations/             # Alembic migrations
├── frontend/                   # Next.js app
│   ├── app/                    # App router
│   ├── components/             # React components
│   └── lib/                    # Utilities
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

### Health & Info
- `GET /` - Redirect to API docs
- `GET /api/v1/health` - Health check
- `GET /api/v1/info` - Application info

### Setup
- `GET /api/v1/setup/status` - Check setup status
- `POST /api/v1/setup/initialize` - Create first admin user

### Authentication
- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/change-password` - Change own password
- `GET /api/v1/auth/me` - Get current user info

### User Management (Admin only)
- `GET /api/v1/users` - List all users
- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/users/{id}` - Get user by ID
- `POST /api/v1/users` - Create new user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Permissions (Admin only)
- `POST /api/v1/permissions/users/{user_id}` - Grant permissions on a server
- `GET /api/v1/permissions/users/{user_id}` - Get all user permissions
- `GET /api/v1/permissions/users/{user_id}/servers/{server_id}` - Check permissions
- `DELETE /api/v1/permissions/users/{user_id}/servers/{server_id}` - Revoke permissions

### Server Management
- `POST /api/v1/servers` - Create new server (Admin only)
- `GET /api/v1/servers` - List all accessible servers
- `GET /api/v1/servers/{id}` - Get server details
- `PUT /api/v1/servers/{id}` - Update server settings (MANAGE permission)
- `DELETE /api/v1/servers/{id}` - Delete server (MANAGE permission)
- `POST /api/v1/servers/{id}/start` - Start server (START_STOP permission)
- `POST /api/v1/servers/{id}/stop` - Stop server (START_STOP permission)
- `POST /api/v1/servers/{id}/restart` - Restart server (START_STOP permission)
- `GET /api/v1/servers/{id}/stats` - Get real-time server stats (VIEW permission)

### Coming Soon
- Console & RCON (`/api/v1/console/*`)
- File management (`/api/v1/files/*`)
- Backups (`/api/v1/backups/*`)

## Contributing

This is an open-source project and contributions are welcome!

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

## Roadmap

### **Phase 1 - Foundation** ✅ COMPLETED
- [x] Project structure (backend, Docker, docs)
- [x] Database models (User, Server, Backup)
- [x] Core configuration (config.py, database.py, security.py)
- [x] Health check & info endpoints
- [x] Setup wizard endpoint
- [x] Docker & Docker Compose setup
- [x] Testing infrastructure (pytest, 15/15 tests passing, 73% coverage)
- [x] Alembic migrations setup
- [x] MySQL integration
- [x] Production deployment (Dokploy)
- [x] CI/CD ready structure

### **Phase 2 - Authentication** ✅ COMPLETED
- [x] Login endpoint (POST `/api/v1/auth/login`)
- [x] JWT token generation and validation
- [x] Protected route middleware (Bearer token)
- [x] User CRUD endpoints (admin only)
- [x] Change password endpoint
- [x] Server-specific permission system (models, service, endpoints)
- [x] Permission management API
- [x] Tests for authentication (42/42 tests passing)
- [ ] Refresh token mechanism (deferred to Phase 7)

### **Phase 3 - Server Management** ✅ COMPLETED
- [x] Create server endpoint (POST `/api/v1/servers`)
- [x] Start/stop/restart server endpoints
- [x] Delete server endpoint
- [x] Get server status & stats endpoint
- [x] List all servers endpoint
- [x] Docker container integration (aiodocker service)
- [x] Docker service (create, start, stop, restart, delete containers)
- [x] Container stats retrieval (CPU, memory usage)
- [x] Port management (auto-assignment within configured ranges)
- [x] Server permissions integration (VIEW, START_STOP, MANAGE)
- [x] Tests for server management (24 tests)
- [x] Tests for Docker service (17 tests)
- [x] Full test coverage (87/87 tests passing, 73% coverage)
- [ ] RCON connection (deferred to Phase 4)
- [ ] Server logs endpoint (deferred to Phase 4)

### **Phase 4 - Console & RCON** 📋 Planned
- [ ] WebSocket connection for console
- [ ] RCON command execution
- [ ] Real-time log streaming
- [ ] Command history
- [ ] Tests for console

### **Phase 5 - File Management** 📋 Planned
- [ ] File explorer API
- [ ] Upload files endpoint
- [ ] Download files endpoint
- [ ] Edit text files (server.properties, etc.)
- [ ] Delete files
- [ ] Create directories
- [ ] Tests for file operations

### **Phase 6 - Backups** 📋 Planned
- [ ] Manual backup creation
- [ ] List backups
- [ ] Download backup
- [ ] Restore backup
- [ ] Delete backup
- [ ] Scheduled backups (APScheduler)
- [ ] Backup retention policy
- [ ] Tests for backups

### **Phase 7 - Frontend** 🚧 In Progress
- [x] Next.js app setup
- [x] Theme system (dark/light mode with next-themes)
- [x] Authentication flow (login/logout)
- [x] Setup wizard page (initial admin creation)
- [x] Route protection (middleware + AuthGuard)
- [x] Dashboard page (basic layout)
- [ ] Server list & cards
- [ ] Server detail page
- [ ] Console terminal (xterm.js)
- [ ] File explorer UI
- [ ] Backup management UI
- [ ] User management (admin only)
- [ ] Settings page
- [ ] Refresh token mechanism

### **Phase 8 - Production Ready** 📋 Future
- [ ] Contributing guidelines (CONTRIBUTING.md)
- [ ] Backup storage options (S3, local, FTP)
- [ ] Performance optimization
- [ ] Security audit

---

**Disclaimer:** This project is not affiliated with Mojang Studios or Microsoft. "Minecraft" is a trademark of Mojang Studios.
