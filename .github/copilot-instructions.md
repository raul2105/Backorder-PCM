# Backorder PCM AI Assistant Instructions

## Project Overview
Backorder PCM is a full-stack system for managing industrial label manufacturing backorders. It integrates with multiple ERPs (Syteline, Mongus), prioritizes orders, and provides a real-time dashboard.
- **Backend**: Flask 3.0, SQLAlchemy, JWT, Celery (Async tasks).
- **Frontend**: React 18 (Vite), Material UI, Recharts.
- **Infrastructure**: Docker Compose, PowerShell management scripts.
- **OS**: Optimized for Windows deployment.

## Architecture & Data Flow
- **Entry Point**: `backend/run.py` initializes the Flask app factory (`create_app` in `backend/app/__init__.py`).
- **Blueprints**: Routes are modularized in `backend/app/routes/` and registered in `create_app`.
- **Services**: Business logic resides in `backend/app/services/` (e.g., `priority_service.py`, `sync_service.py`).
- **ERP Integration**: All ERP connectors inherit from `BaseERPConnector` (`backend/app/erp_connectors/base_connector.py`).
- **Frontend API**: All HTTP requests go through `frontend/src/services/api.js`. Components consume this service.

## Critical Developer Workflows
Use the provided scripts for lifecycle management. DO NOT run `docker-compose` directly unless necessary.
- **Start System**: `.\INICIAR.bat` (Starts containers and opens browser).
- **Stop System**: `.\DETENER.bat`.
- **View Logs**: `.\ver-logs.ps1` (Real-time logs from containers).
- **Reset DB/State**: `.\reset.ps1` (Use with caution).
- **Check Status**: `.\estado.ps1`.

## Code Patterns & Conventions

### Backend (Python/Flask)
- **Configuration**: Use `config.yaml`. Loaded via `load_config` in `__init__.py`. Avoid hardcoding credentials.
- **Database**: Use SQLAlchemy models in `backend/app/models/`. Run migrations with `flask db migrate/upgrade`.
- **Authentication**: Protect routes with `@jwt_required()`. Admin context available via `get_jwt_identity()`.
- **Security**: Some routes implement IP allowlisting via `_ip_allowed` helper (e.g., `backend/app/routes/backorder.py`).
- **Structure**:
  - `routes/`: HTTP endpoints only. Delegate logic to services.
  - `services/`: Pure business logic, reusable.
  - `erp_connectors/`: External system adapters.

### Frontend (React/Vite)
- **Components**: Functional components with Hooks. Located in `frontend/src/components` (reusable) or `frontend/src/pages` (views).
- **Styling**: Material UI (MUI) components preferred over custom CSS.
- **State**: `react-query` for server state, local state for UI.
- **Build**: `npm run build` generates artifacts in `frontend/build` (served by Nginx/Flask in prod).

### Integration
- **ERP Connectors**: When adding a new ERP, subclass `BaseERPConnector` and implement all abstract methods (`connect`, `fetch_orders`, etc.).
- **Tasks**: Long-running jobs (importing CSVs, syncing ERPs) should use Celery or background threads if configured.

## Common Tasks
- **New Route**: Create file in `backend/app/routes/`, define Blueprint, register in `backend/app/__init__.py`.
- **New Config**: Add key to `config.yaml`, access via `app.config` or `load_config()`.
- **Debug**: Check `backend/logs/` or run `.\ver-logs.ps1`.
