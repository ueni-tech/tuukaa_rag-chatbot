from fastapi import APIRouter

from .embed_ingest import router as embed_ingest_router
from .admin import router as admin_router
from .reports import router as reports_router


router = APIRouter()

# 分割ルーター
router.include_router(embed_ingest_router)
router.include_router(admin_router)
router.include_router(reports_router)
