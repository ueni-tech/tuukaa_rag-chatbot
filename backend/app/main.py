"""
FastAPIアプリケーションのメインエントリーポイント
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

try:
    from zoneinfo import ZoneInfo  # Python 3.9以降
except ImportError:
    from pytz import timezone as ZoneInfo  # それ以前はpytzを使う

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .api.endpoints import router as api_router
from .core.config import settings
from .core.dependencies import get_rag_engine, initialize_rag_engine
from .core.rag_engine import RAGEngine
from .models.schemas import HealthResponse

# タイムゾーン設定
JST = ZoneInfo("Asia/Tokyo")

# ロギング設定
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# NOTE
# @asynccontextmanager を使った関数は、FastAPIのライフサイクル管理（アプリケーションの起動時・終了時の処理）に利用できる
@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理
    起動時にRAGエンジンを初期化し、終了時にクリーンアップを行う
    """

    logger.info("アプリケーションを起動中...")
    try:
        await initialize_rag_engine()
        logger.info("RAGエンジンの初期化が完了しました")
    except Exception as e:
        logger.error(f"RAGエンジンの初期化に失敗しました: {e}")
        raise

    yield

    logger.info("アプリケーション終了中...")


def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成
    Returns:
        設定済みのFastAPIアプリケーション
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="LangChainとRAGを活用したコーディング規約Q&Aシステム",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # CROS設定
    app.add_middleware(
        CORSMiddleware,
        # TODO
        # 本番用ドメインを設定する
        allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # セキュリティ設定
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware, allow_hosts=["yourdomain.com", "*.yourdomain.com"]
        )

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()


@app.get("/", response_model=HealthResponse)
async def root():
    """ルートエンドポイント（ヘルスチェック）"""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now(JST).isoformat(),
    )


@app.get("/health", response_model=HealthResponse)
async def health_check(rag_engine: RAGEngine = Depends(get_rag_engine)):
    """詳細なヘルスチェック"""
    try:
        sytem_info = await rag_engine.get_system_info()
        status = "healthy" if sytem_info["status"] == "initialized" else "degraded"

        return HealthResponse(
            status=status,
            version=settings.app_version,
            timestamp=datetime.now(JST).isoformat(),
        )
    except Exception as e:
        logger.error(f"ヘルスチェックでエラーが発生しました: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
