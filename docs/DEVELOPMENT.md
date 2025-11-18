# Development Guide

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional but recommended)

### Quick Start with Docker

The easiest way to get started is using Docker Compose:

```bash
# Start all services
docker-compose up

# Backend API: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend Setup

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

#### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Project Structure

```
cloudcostly/
├── backend/
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core configuration
│   │   ├── db/          # Database setup
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── alembic/         # Database migrations
│   └── tests/           # Backend tests
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── lib/         # Utilities and API client
│   │   └── types/       # TypeScript types
│   └── public/          # Static assets
└── infrastructure/      # Terraform configurations
```

## Development Workflow

### Making Changes

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and test locally

3. Run tests:
```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

4. Format code:
```bash
# Backend
black app/

# Frontend
npm run format
```

5. Commit and push:
```bash
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature-name
```

### Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migrations:
```bash
alembic downgrade -1
```

### Adding API Endpoints

1. Create endpoint in `backend/app/api/v1/endpoints/`
2. Add route to `backend/app/api/v1/api.py`
3. Create corresponding frontend API call in `frontend/src/lib/api.ts`
4. Add tests for the endpoint

### Environment Variables

#### Backend (.env)
- `DATABASE_URL`: PostgreSQL connection string
- `AWS_REGION`: AWS region for API calls
- `API_SECRET_KEY`: Secret key for JWT tokens
- `REDIS_URL`: Redis connection string

#### Frontend (.env)
- `VITE_API_URL`: Backend API URL

## Testing

### Backend Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Frontend Testing

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage
```

## Debugging

### Backend Debugging

Add breakpoints using:
```python
import pdb; pdb.set_trace()
```

Or use VS Code debugger with this launch configuration:
```json
{
  "name": "Python: FastAPI",
  "type": "python",
  "request": "launch",
  "module": "uvicorn",
  "args": [
    "app.main:app",
    "--reload"
  ],
  "cwd": "${workspaceFolder}/backend"
}
```

### Frontend Debugging

Use browser DevTools or VS Code debugger.

## Common Tasks

### Resetting the Database

```bash
docker-compose down -v
docker-compose up -d postgres
cd backend && alembic upgrade head
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Accessing the Database

```bash
docker-compose exec postgres psql -U postgres -d cloudcostly
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
```

### Database Connection Issues

1. Ensure PostgreSQL is running
2. Check DATABASE_URL in .env
3. Verify database exists

### Module Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
npm install
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [AWS Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
