# Getting Started with CloudCostly

Welcome to CloudCostly! This guide will help you get the project up and running.

## Project Overview

CloudCostly is a SaaS platform for cloud cost optimization with the following features:
- Real-time AWS cost visualization
- AI-powered optimization recommendations
- Multi-tenant architecture
- Visual architecture designer (coming soon)
- Multi-cloud support (AWS initially, Azure/GCP planned)

## Architecture Summary

**Backend**: Python FastAPI + PostgreSQL + Redis
**Frontend**: React + TypeScript + Tailwind CSS
**Infrastructure**: AWS (Lambda, RDS, API Gateway, S3)
**IaC**: Terraform
**CI/CD**: GitHub Actions

## Quick Start (Recommended)

### Using Docker Compose

The fastest way to get started:

```bash
# 1. Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up

# 2. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

That's it! The application is now running locally.

## Manual Setup (Alternative)

If you prefer to run services individually:

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+ (optional for caching)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database URL

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

Backend will be at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env

# Start development server
npm run dev
```

Frontend will be at http://localhost:3000

## Project Structure

```
cloudcostly/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration
│   │   ├── db/             # Database setup
│   │   ├── models/         # SQLAlchemy models
│   │   └── main.py         # Application entry
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
│
├── frontend/                # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── lib/            # API client & utilities
│   │   └── main.tsx        # Application entry
│   └── package.json        # Node dependencies
│
├── infrastructure/          # Terraform IaC
│   ├── main.tf             # Main configuration
│   ├── vpc.tf              # VPC setup
│   ├── rds.tf              # Database
│   ├── lambda.tf           # Lambda functions
│   └── api_gateway.tf      # API Gateway
│
├── .github/workflows/       # CI/CD pipelines
├── docs/                    # Documentation
├── docker-compose.yml       # Local development
└── README.md                # Project overview
```

## Next Steps

### 1. Explore the Application

- Login page: http://localhost:3000/login
- Dashboard: http://localhost:3000/
- API Documentation: http://localhost:8000/docs

### 2. Development Workflow

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development instructions.

Key commands:
```bash
# Run tests
cd backend && pytest
cd frontend && npm test

# Format code
cd backend && black app/
cd frontend && npm run lint

# Database migrations
cd backend && alembic upgrade head
```

### 3. Implement Core Features

The current setup includes:
- ✅ Project structure
- ✅ Database schema (multi-tenant)
- ✅ API endpoints (stubs)
- ✅ Frontend pages (UI only)
- ✅ Infrastructure code
- ✅ CI/CD pipelines

**Next implementation priorities** (from the roadmap):

#### Phase 1: Authentication & AWS Account Linking
- [ ] Implement JWT authentication
- [ ] User registration/login
- [ ] AWS IAM role setup for cross-account access
- [ ] AWS account linking flow

#### Phase 2: Cost Data Ingestion
- [ ] AWS Cost Explorer API integration
- [ ] Cost and Usage Reports (CUR) ingestion
- [ ] Background jobs for data sync
- [ ] Cost data storage and aggregation

#### Phase 3: Cost Visualization
- [ ] Dashboard with cost breakdown
- [ ] Charts and graphs (using Recharts)
- [ ] Filter by service, time period, tags
- [ ] Cost trend analysis

#### Phase 4: Optimization Recommendations
- [ ] AWS Compute Optimizer integration
- [ ] Rightsizing recommendations
- [ ] Idle resource detection
- [ ] Savings Plans/Reserved Instances suggestions

#### Phase 5: Architecture Designer (Advanced)
- [ ] Drag-and-drop canvas (JointJS/GoJS)
- [ ] AWS service components
- [ ] Real-time cost estimation
- [ ] CloudFormation export

### 4. AWS Setup

To connect to AWS and fetch cost data:

1. **Set up AWS credentials** in `backend/.env`:
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
```

2. **Enable Cost Explorer** in your AWS account:
   - Go to AWS Billing Console
   - Enable Cost Explorer API
   - Wait 24 hours for data to populate

3. **Set up Cost and Usage Reports** (optional but recommended):
   - Go to AWS Billing → Cost and Usage Reports
   - Create a new report
   - Deliver to S3 bucket
   - Configure hourly granularity

### 5. Deploy to AWS

When ready for production:

```bash
cd infrastructure

# Initialize Terraform
terraform init

# Review changes
terraform plan

# Deploy
terraform apply
```

See [infrastructure/README.md](infrastructure/README.md) for detailed deployment instructions.

## Configuration

### Environment Variables

**Backend (.env)**:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/cloudcostly
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
API_SECRET_KEY=change-in-production
REDIS_URL=redis://localhost:6379
```

**Frontend (.env)**:
```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=CloudCostly
```

## Troubleshooting

### Database Connection Error
```bash
# Ensure PostgreSQL is running
docker-compose up postgres

# Check connection (note: Docker uses port 5433)
psql postgresql://postgres:postgres@localhost:5433/cloudcostly
```

### Port Already in Use
```bash
# Kill process on port 8000
lsof -i :8000
kill -9 <PID>
```

### Module Not Found
```bash
# Reinstall dependencies
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

## Resources

- **API Documentation**: http://localhost:8000/docs (when running)
- **Development Guide**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **Infrastructure**: [infrastructure/README.md](infrastructure/README.md)
- **Roadmap**: [cloudcostly_prompts_full.md](cloudcostly_prompts_full.md)

## Support

For issues or questions:
1. Check existing documentation
2. Review error logs: `docker-compose logs -f`
3. Ensure all prerequisites are installed
4. Verify environment variables are set correctly

## What's Next?

Start implementing features following the development roadmap:

1. **Week 1-2**: Authentication & AWS account linking
2. **Week 3-4**: Cost data ingestion from AWS Cost Explorer
3. **Week 5-6**: Dashboard and cost visualization
4. **Week 7-8**: Optimization recommendations
5. **Week 9+**: Advanced features (architecture designer, multi-cloud)

Happy coding! 🚀
