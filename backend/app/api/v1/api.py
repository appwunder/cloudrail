from fastapi import APIRouter
from app.api.v1.endpoints import auth, costs, aws_accounts, cloud_accounts, architectures, budgets

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(aws_accounts.router, prefix="/aws-accounts", tags=["aws-accounts"])
api_router.include_router(cloud_accounts.router, prefix="/cloud-accounts", tags=["cloud-accounts"])
api_router.include_router(costs.router, prefix="/costs", tags=["costs"])
api_router.include_router(architectures.router, prefix="/architectures", tags=["architectures"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
