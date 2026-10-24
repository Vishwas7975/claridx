from fastapi import APIRouter

from app.api.v1 import auth, diabetes, health, heart, history

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(heart.router)
api_router.include_router(diabetes.router)
api_router.include_router(history.router)
