from fastapi import APIRouter
from ..core.web.rate_limit import rate_limited


router = APIRouter(prefix="/lp", tags=["LP"])


@router.get("/", summary="LP ルーター疎通確認")
@rate_limited("lp:root")
async def lp_root():
    return {"status": "ok"}


@router.post("/generate", summary="LP: 生成（雛形）")
@rate_limited("lp:generate")
async def lp_generate():
    return {"status": "ok", "action": "generate"}


@router.post("/proofread", summary="LP: 校正（雛形）")
@rate_limited("lp:proofread")
async def lp_proofread():
    return {"status": "ok", "action": "proofread"}
