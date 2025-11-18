# CloudCostly - Cloud Cost Optimization SaaS

A comprehensive cloud cost optimization platform that helps you visualize, analyze, and optimize your AWS spending with intelligent recommendations and visual architecture planning.

## Features

- **Real-time Cost Visualization**: Connect to AWS and see detailed cost breakdowns by service and resource
- **AI-Powered Optimization**: Get intelligent recommendations for rightsizing, idle resources, and commitment discounts
- **Architecture Designer**: Visual drag-and-drop canvas to design cloud architectures and estimate costs before deployment
- **Multi-Tenant SaaS**: Secure, scalable platform supporting multiple customers

## Architecture

```
cloudcostly/
├── backend/          # Python FastAPI backend
├── frontend/         # React TypeScript frontend
├── infrastructure/   # Terraform IaC
└── docs/            # Documentation
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Boto3, SQLAlchemy
- **Frontend**: React 18, TypeScript, Tailwind CSS
- **Database**: PostgreSQL (AWS RDS)
- **Infrastructure**: AWS (Lambda, API Gateway, RDS, S3, Cognito)
- **IaC**: Terraform

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- AWS Account
- Terraform

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Infrastructure Deployment

```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

## Development Phases

- [x] Phase 0: Project setup and foundation
- [ ] Phase 1: Authentication and AWS account linking
- [ ] Phase 2: Cost data ingestion (Cost Explorer API)
- [ ] Phase 3: Cost breakdown dashboard
- [ ] Phase 4: Basic optimization recommendations
- [ ] Phase 5: Architecture designer canvas
- [ ] Phase 6: Advanced cost estimation
- [ ] Phase 7: Multi-cloud support (Azure, GCP)

## License

Proprietary
