from fastapi import APIRouter

from .endpoints import router as legacy_router
from .pdf import router as pdf_router
from .lp import router as lp_router
from .embed import router as embed_router


router = APIRouter()

# 既存の互換ルート
router.include_router(legacy_router)

# 新規の分割ルーター（段階移行）
router.include_router(pdf_router)
router.include_router(lp_router)
router.include_router(embed_router)


