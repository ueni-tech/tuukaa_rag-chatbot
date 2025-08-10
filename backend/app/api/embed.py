from fastapi import APIRouter
from ..core.web.rate_limit import rate_limited


router = APIRouter(prefix="/embed", tags=["Embed"])


@router.get("/", summary="Embed ルーター疎通確認")
@rate_limited("embed:root")
async def embed_root():
    return {"status": "ok"}


@router.post("/ingest", summary="Embed: ページ投入（雛形）")
@rate_limited("embed:ingest")
async def embed_ingest():
    return {"status": "ok", "action": "ingest"}


@router.post("/chat", summary="Embed: チャット（雛形）")
@rate_limited("embed:chat")
async def embed_chat():
    return {"status": "ok", "action": "chat"}
