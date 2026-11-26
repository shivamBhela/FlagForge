from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    organizations,
    projects,
    flagsmith,
    webhooks,
    scanner,
    dependencies,
    chaos,
    telemetry,
    guardian,
    incidents,
    cleanup,
    seed,
    jobs,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(projects.router, prefix="/organizations", tags=["projects"])
api_router.include_router(flagsmith.router, prefix="/flagsmith", tags=["flagsmith"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(scanner.router, tags=["scanner"])
api_router.include_router(dependencies.router, tags=["dependencies"])
api_router.include_router(chaos.router, tags=["chaos"])
api_router.include_router(telemetry.router, tags=["telemetry"])
api_router.include_router(guardian.router, tags=["guardian"])
api_router.include_router(incidents.router, tags=["incidents"])
api_router.include_router(cleanup.router, tags=["cleanup"])
api_router.include_router(seed.router, tags=["seed"])
api_router.include_router(jobs.router, tags=["background jobs"])

