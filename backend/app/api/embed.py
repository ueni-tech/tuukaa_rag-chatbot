from fastapi import APIRouter


router = APIRouter(prefix="/embed", tags=["Embed"])


@router.get("/", summary="Embed ルーター疎通確認")
async def embed_root():
    return {"status": "ok"}


@router.post("/ingest", summary="Embed: ページ投入（雛形）")
async def embed_ingest():
    return {"status": "ok", "action": "ingest"}


@router.post("/chat", summary="Embed: チャット（雛形）")
async def embed_chat():
    return {"status": "ok", "action": "chat"}


