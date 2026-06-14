from fastapi import APIRouter

from app.api.routes import (
    items,
    login,
    private,
    users,
    utils,
    profile,
    resume,
    question_memory,
    jobs,
    applications,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(profile.router)
api_router.include_router(resume.router)
api_router.include_router(question_memory.router)
api_router.include_router(jobs.router)
api_router.include_router(applications.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
