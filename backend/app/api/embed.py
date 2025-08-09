from fastapi import APIRouter


router = APIRouter(prefix="/embed", tags=["Embed"])


@router.get("/", summary="Embed ルーター疎通確認")
async def embed_root():
    return {"status": "ok"}


