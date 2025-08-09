from fastapi import APIRouter


router = APIRouter(prefix="/lp", tags=["LP"])


@router.get("/", summary="LP ルーター疎通確認")
async def lp_root():
    return {"status": "ok"}


