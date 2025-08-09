from fastapi import APIRouter


router = APIRouter(prefix="/lp", tags=["LP"])


@router.get("/", summary="LP ルーター疎通確認")
async def lp_root():
    return {"status": "ok"}


@router.post("/generate", summary="LP: 生成（雛形）")
async def lp_generate():
    return {"status": "ok", "action": "generate"}


@router.post("/proofread", summary="LP: 校正（雛形）")
async def lp_proofread():
    return {"status": "ok", "action": "proofread"}
