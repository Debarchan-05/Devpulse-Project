from fastapi import APIRouter

from app.api.v1.endpoints import achievements, ai, analytics, auth, github

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(github.router)
api_router.include_router(analytics.router)
api_router.include_router(achievements.router)
api_router.include_router(ai.router)
