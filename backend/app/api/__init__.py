from fastapi import APIRouter

from .embed_ingest import router as embed_ingest_router


router = APIRouter()

# 分割ルーター
router.include_router(embed_ingest_router)
