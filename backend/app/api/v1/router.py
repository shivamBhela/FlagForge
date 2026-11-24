from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    organizations,
    projects,
    flagsmith,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(projects.router, prefix="/organizations", tags=["projects"])
api_router.include_router(flagsmith.router, prefix="/flagsmith", tags=["flagsmith"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
