from fastapi import APIRouter

from de_lekbak_backend.api.v1 import health, viral_cves

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(viral_cves.router, prefix="/viral-cves", tags=["viral-cves"])
