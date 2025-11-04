# Mineploy - Claude Development Guide

This file contains essential information about the Mineploy project structure, conventions, and development workflows for Claude Code.

## Project Overview

Mineploy is a self-hosted Minecraft server management platform built with FastAPI (backend) and Next.js (frontend). It allows users to create, manage, and monitor Minecraft servers through Docker containers.

## Tech Stack

### Backend
- **Framework**: FastAPI 0.120.4 (async)
- **Database**: MySQL with SQLAlchemy 2.0.44 (async) + Alembic
- **Docker**: aiodocker 0.24.0 for container management
- **Authentication**: JWT tokens (python-jose) + bcrypt
- **WebSockets**: python-socketio for real-time server logs
- **Minecraft**: mcrcon for RCON communication

### Frontend
- **Framework**: Next.js 16.0.1 (App Router) + React 19.2.0
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **State Management**: Zustand (auth store)
- **Data Fetching**: TanStack Query (React Query)
- **Terminal**: xterm.js for console logs
- **HTTP Client**: Axios

## Project Structure

```
mineploy/
├── backend/
│   ├── api/                    # API endpoints (routers)
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── servers.py         # Server CRUD operations
│   │   ├── docker.py          # Docker cleanup/monitoring
│   │   └── users.py           # User management
│   ├── core/
│   │   ├── config.py          # Application settings
│   │   ├── dependencies.py    # FastAPI dependencies (auth, etc.)
│   │   └── security.py        # JWT, password hashing
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py
│   │   └── server.py
│   ├── schemas/               # Pydantic schemas (request/response)
│   ├── services/              # Business logic
│   │   ├── docker_service.py
│   │   ├── docker_cleanup_service.py
│   │   ├── server_properties_service.py
│   │   └── websocket_service.py
│   ├── tests/                 # Pytest tests
│   ├── alembic/               # Database migrations
│   ├── main.py                # FastAPI app entry point
│   └── requirements.txt       # Python dependencies
│
└── frontend/
    ├── src/
    │   ├── app/               # Next.js App Router pages
    │   │   ├── (auth)/        # Auth pages (login, register)
    │   │   ├── servers/       # Server management pages
    │   │   │   ├── [id]/      # Server detail/settings pages
    │   │   │   └── page.tsx   # Servers list
    │   │   └── space/         # Docker cleanup/monitoring
    │   ├── components/        # React components
    │   │   ├── ui/           # shadcn/ui components
    │   │   ├── auth/         # Auth-related components
    │   │   ├── servers/      # Server-related components
    │   │   └── sidebar/      # Navigation sidebar
    │   ├── services/         # API client services
    │   ├── stores/           # Zustand stores
    │   ├── hooks/            # Custom React hooks
    │   ├── types/            # TypeScript type definitions
    │   └── lib/              # Utilities (axios config, utils)
    └── package.json
```

## Development Workflow

### Backend Development

#### Running the Backend
```bash
# From project root or backend directory
cd backend
source venv/bin/activate
python3 -m uvicorn main:app --reload --port 8000
```

#### Running Tests
```bash
# Always use this exact command
source venv/bin/activate && pytest -v

# Run specific test file
source venv/bin/activate && pytest tests/test_docker_cleanup_service.py -v

# Run specific test
source venv/bin/activate && pytest tests/test_docker_cleanup_service.py::TestPruneImages -v
```

#### Database Migrations
```bash
# Create new migration after model changes
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

#### Code Formatting (Backend)
- **Important**: Always use `python3` command, NOT `python`
- Python code follows PEP 8 conventions
- Use async/await for all I/O operations
- Type hints are encouraged but not strictly enforced

### Frontend Development

#### Running the Frontend
```bash
cd frontend
npm run dev
# Runs on http://localhost:3000
```

#### Code Formatting (Frontend)
```bash
# Run ESLint
npm run lint

# Build (checks for errors)
npm run build
```

## Important Development Guidelines

### General Rules
1. **Never run npm/uvicorn unless explicitly asked** - Don't start dev servers automatically
2. **Always check for existing components** - Reuse existing shadcn/ui components
3. **Use python3, not python** - Consistent Python command
4. **Verify Alembic integration** - Use migrations for database changes

### Backend Conventions

#### API Endpoints
- **Location**: `backend/api/`
- **Naming**: Use plural nouns (e.g., `/servers`, `/users`)
- **Auth**: Use `Depends(get_current_user)` or `Depends(require_admin)`
- **Error Handling**: Raise `HTTPException` with appropriate status codes

Example:
```python
@router.get("/servers/{server_id}")
async def get_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Implementation
    pass
```

#### Services
- **Location**: `backend/services/`
- **Purpose**: Business logic separated from API layer
- **Pattern**: Service classes with async methods
- **Dependencies**: Inject aiodocker, database sessions as needed

Example:
```python
class DockerCleanupService:
    def __init__(self):
        self.docker: Optional[aiodocker.Docker] = None

    async def connect(self):
        if not self.docker:
            self.docker = aiodocker.Docker(url=f"unix://{settings.docker_socket}")

    async def get_disk_usage(self) -> Dict[str, Any]:
        await self.connect()
        # Implementation
```

#### Testing
- **Framework**: pytest with pytest-asyncio
- **Location**: `backend/tests/`
- **Naming**: `test_*.py` files, `Test*` classes, `test_*` functions
- **Mocking**: Use `unittest.mock` for external dependencies

Example:
```python
@pytest.mark.asyncio
async def test_prune_images_success(cleanup_service, mock_docker):
    """Test successful image pruning."""
    mock_docker.images.prune = AsyncMock(return_value={
        "ImagesDeleted": [{"Deleted": "sha256:abc123"}],
        "SpaceReclaimed": 2 * 1024 * 1024 * 1024,
    })

    cleanup_service.docker = mock_docker
    result = await cleanup_service.prune_images()

    assert result["images_deleted"] == 1
```

#### Docker Resource Management
- **Images**: Only count/delete `itzg/minecraft-server` images
- **Containers**: Filter by label `mineploy.managed=true`
- **Volumes**: Track orphaned volumes (not attached to containers)
- **Networks**: Protect default networks: `bridge`, `host`, `none`, `minecraft_network`, `mineploy_network`

### Frontend Conventions

#### Page Structure
All pages should follow this consistent structure:

```tsx
export default function PageName() {
  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Icon className="size-8" />
            Page Title
          </h1>
          <p className="text-muted-foreground">
            Page description
          </p>
        </div>
        <Button>Action</Button>
      </div>

      <Separator />

      {/* Main Content */}
      {/* ... */}
    </>
  );
}
```

#### Layout Structure
Use layout.tsx for consistent page structure:

```tsx
export default function PageLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-4 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="!h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbPage>Page Name</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </header>
          <div className="flex flex-1 flex-col p-4 pt-0 overflow-auto">
            <div className="rounded-xl border-2 bg-background shadow-sm p-6 h-full flex flex-col gap-6">
              {children}
            </div>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </AuthGuard>
  );
}
```

#### Components
- **UI Components**: Located in `frontend/src/components/ui/` (shadcn/ui)
- **Custom Components**: Group by feature (e.g., `servers/`, `auth/`)
- **Reusability**: Always check if component exists before creating new one
- **Naming**: PascalCase for components, kebab-case for files

#### API Services
- **Location**: `frontend/src/services/`
- **Pattern**: Export service object with methods
- **Base Client**: Use configured axios instance from `lib/axios.ts`

Example:
```typescript
import { api } from "@/lib/axios";
import { DiskUsage, PruneResult } from "@/types/docker";

export const dockerService = {
  async getDiskUsage(): Promise<DiskUsage> {
    const { data } = await api.get("/docker/disk-usage");
    return data;
  },

  async pruneImages(): Promise<PruneResult> {
    const { data } = await api.post("/docker/prune-images");
    return data;
  },
};
```

#### State Management
- **TanStack Query**: For server state (API data)
- **Zustand**: For client state (auth, UI state)
- **React Query Keys**: Use array format: `["resource", id]`

Example:
```typescript
const { data, isLoading } = useQuery({
  queryKey: ["server", serverId],
  queryFn: () => serverService.getServer(serverId),
});

const mutation = useMutation({
  mutationFn: serverService.createServer,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["servers"] });
    toast.success("Server created!");
  },
});
```

#### TypeScript Types
- **Location**: `frontend/src/types/`
- **Exports**: Export all types from `types/index.ts`
- **Naming**: Use descriptive names (e.g., `Server`, `ServerStatus`, `CreateServerRequest`)

## Git Commit Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org):

```bash
feat: add new feature
fix: bug fix
docs: documentation changes
style: code style (formatting, no logic changes)
refactor: code refactoring
perf: performance improvements
test: add/update tests
build: build system changes
ci: CI configuration changes
chore: other changes (no src/test files)
```

**Important**:
- Do NOT include Claude Code advertisement in commits
- Do NOT add Claude as co-author
- Only commit when user explicitly requests and confirms functionality works

## Common Issues & Solutions

### Backend

#### aiodocker API Limitations
- **No `system.df()`**: Use individual APIs (`images.list()`, `containers.list()`, `volumes.list()`)
- **No `volumes.prune()`**: Implement manual pruning by checking volume usage
- **No `networks.prune()`**: Implement manual network cleanup
- **DockerContainer objects**: Always call `await container_obj.show()` to get info dict

#### File Ownership in Containers
When uploading files to containers, set correct ownership:
```python
tarinfo.mode = 0o644
tarinfo.uid = 1000  # Match container user
tarinfo.gid = 1000  # Match container group
```

### Frontend

#### Component Imports
Always import from the correct path:
```typescript
// Correct
import { Button } from "@/components/ui/button";
import { ServerCard } from "@/components/servers/server-card";

// Incorrect
import { Button } from "components/ui/button";
```

#### API Error Handling
Always handle errors in mutations:
```typescript
const mutation = useMutation({
  mutationFn: () => api.delete(`/servers/${id}`),
  onSuccess: () => {
    toast.success("Server deleted");
  },
  onError: (error: any) => {
    toast.error("Failed to delete server", {
      description: error?.response?.data?.detail || "An error occurred",
    });
  },
});
```

## Environment Setup

### Backend Environment Variables
Create `.env` file in backend directory:
```env
# Database
DATABASE_URL=mysql+aiomysql://user:password@localhost/mineploy

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Docker
DOCKER_SOCKET=/var/run/docker.sock
```

### Frontend Environment Variables
Create `.env.local` file in frontend directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing Strategy

### Backend Tests
- **Unit Tests**: Test individual functions/methods with mocked dependencies
- **Integration Tests**: Test API endpoints with test database
- **Coverage**: Aim for >80% coverage on critical paths (services, API endpoints)

### Frontend Tests
- Currently minimal testing setup
- Focus on manual testing of UI components
- Integration testing with real backend during development

## Key Features & Functionality

### Server Management
- Create/delete Minecraft servers
- Start/stop/restart servers
- View real-time console logs (WebSocket)
- Configure server properties (server.properties file)
- RCON command execution

### Docker Cleanup (Space Management)
- Monitor disk usage by Mineploy resources
- Cleanup unused images (itzg/minecraft-server only)
- Remove stopped containers (mineploy.managed=true only)
- Delete orphaned volumes
- Prune unused networks
- **Important**: Scoped to Mineploy resources only, doesn't affect other Docker resources

### Authentication
- JWT-based authentication
- Role-based access control (admin/user)
- Password hashing with bcrypt
- Admin-only endpoints for sensitive operations

## Performance Considerations

### Backend
- Use async/await for all I/O operations
- Connection pooling for database (SQLAlchemy)
- Reuse Docker client connections
- Implement pagination for large datasets

### Frontend
- Use React Query for caching and deduplication
- Lazy load components where appropriate
- Optimize re-renders with proper React Query configuration
- Use WebSocket for real-time updates (logs)

## Security Considerations

### Backend
- Always validate user input with Pydantic
- Use parameterized queries (SQLAlchemy ORM handles this)
- Never expose internal error details to clients
- Verify user permissions before operations
- Rate limiting on authentication endpoints

### Frontend
- Store JWT in httpOnly cookies (if possible) or secure localStorage
- Validate API responses
- Sanitize user input
- Use HTTPS in production

## Deployment Notes

### Backend
- Use uvicorn with gunicorn workers for production
- Set up systemd service for auto-restart
- Configure reverse proxy (nginx) for SSL
- Run Alembic migrations before deployment

### Frontend
- Build with `npm run build`
- Serve static files with reverse proxy
- Set production environment variables
- Enable production optimizations

---

**Last Updated**: 2025-11-04
**Project Status**: Active Development
**Main Branch**: `main`
