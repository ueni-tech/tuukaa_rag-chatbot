"""
APIスキーマ定義
FastAPIのリクエスト/レスポンスモデルの定義
"""

from typing import Any
from pydantic import BaseModel, Field, field_validator


class QuestionRequest(BaseModel):
    """質問リクエストモデル"""

    # NOTE
    # ...はPydantic の「必須フィールド」を示す特殊な値
    question: str = Field(..., min_length=1, max_length=1000, description="質問内容")
    top_k: int | None = Field(None, ge=1, le=10, description="検索結果の上位k件")

    # NOTE
    # field_validator は Pydantic v2 で導入された、特定のフィールドに対する追加バリデーション／変換用のデコレータ
    @field_validator("question")
    @staticmethod
    def validate_question(v):
        """質問内容のバリエーション"""
        if not v.strip():
            raise ValueError("質問内容を入力してください")
        return v.strip()


class DocumentInfo(BaseModel):
    """文書情報モデル"""

    content: str = Field(..., description="文書内容")
    metadata: dict[str, Any] = Field(default_factory=dict, description="メタデータ")


class SearchResponse(BaseModel):
    """検索レスポンスモデル"""

    documents: list[DocumentInfo] = Field(..., description="検索結果のリスト")
    query: str = Field(..., description="検索クエリ")
    total_found: int = Field(..., description="見つかった文書数")


class AnswerResponse(BaseModel):
    """回答レスポンスモデル"""

    answer: str = Field(..., description="生成された回答")
    question: str = Field(..., description="質問内容")
    documents: list[DocumentInfo] = Field(..., description="参照された文書")
    context_used: str = Field(..., description="使用されたコンテキスト")


class UploadResponse(BaseModel):
    """アップロードレスポンスモデル"""

    status: str = Field(..., description="処理ステータス")
    message: str = Field(..., description="処理結果メッセージ")
    file_info: dict[str, Any] | None = Field(None, description="ファイル情報")
    vectorstore_info: dict[str, Any] | None = Field(
        None, description="ベクトルストア情報"
    )


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
