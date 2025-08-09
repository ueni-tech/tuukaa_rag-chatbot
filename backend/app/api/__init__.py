from fastapi import APIRouter

from .pdf import router as pdf_router
from .lp import router as lp_router
from .embed import router as embed_router


router = APIRouter()

# 分割ルーター
router.include_router(pdf_router)
router.include_router(lp_router)
router.include_router(embed_router)
