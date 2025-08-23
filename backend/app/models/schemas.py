"""
APIスキーマ定義
FastAPIのリクエスト/レスポンスモデルの定義
"""

from typing import Any
from pydantic import BaseModel, Field, field_validator

# PDFドメインのスキーマは重複定義を避けるため再エクスポートする
from ..domains.pdf.schemas import (
    QuestionRequest,
    DocumentInfo,
    SearchResponse,
    AnswerResponse,
    UploadResponse,
)  # noqa: F401 (re-export)

__all__ = [
    "QuestionRequest",
    "DocumentInfo",
    "SearchResponse",
    "AnswerResponse",
    "UploadResponse",
    "SystemInfoResponse",
    "ErrorResponse",
    "HealthResponse",
]


class SystemInfoResponse(BaseModel):
    """システム情報レスポンスモデル"""

    status: str = Field(..., description="システムステータス")
    embedding_model: str = Field(..., description="埋め込みモデル")
    llm_model: str = Field(..., description="LLMモデル")
    vectorstore_ready: bool = Field(..., description="ベクトルストア準備状況")
    document_count: int | None = Field(None, description="保存されている文書数")
    collection_id: str | None = Field(None, description="コレクションID")


class ErrorResponse(BaseModel):
    """エラーレスポンスモデル"""

    error: str = Field(..., description="エラータイプ")
    message: str = Field(..., description="エラーメッセージ")
    details: dict[str, Any] | None = Field(None, description="詳細情報")


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンスモデル"""

    status: str = Field(..., description="サービスステータス")
    version: str = Field(..., description="アプリケーションバージョン")
    timestamp: str = Field(..., description="チェック時刻")
