from fastapi import APIRouter

from app.api.v1.endpoints import graphs, health, uploads, workflows

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(graphs.router, prefix="/graphs", tags=["graphs"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
