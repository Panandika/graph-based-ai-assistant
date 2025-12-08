from fastapi import APIRouter

from app.api.v1.endpoints import graphs, health, workflows

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(graphs.router, prefix="/graphs", tags=["graphs"])
