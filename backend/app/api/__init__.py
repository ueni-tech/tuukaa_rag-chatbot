from fastapi import APIRouter

from .lp import router as lp_router
from .embed import router as embed_router
from .embed_ingest import router as embed_ingest_router


router = APIRouter()

# 分割ルーター
router.include_router(lp_router)
router.include_router(embed_router)
router.include_router(embed_ingest_router)
