from fastapi import APIRouter

from app.api.v1 import diabetes, health, heart

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(heart.router)
api_router.include_router(diabetes.router)
