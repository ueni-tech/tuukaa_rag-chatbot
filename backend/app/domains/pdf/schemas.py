"""
PDFドメインのスキーマ

既存の互換ルート（`/api/v1/{upload,ask,search,...}`）は従来の
`app.models.schemas` を使用し続ける。新ルーター（`/api/v1/pdf/...`）のみ
こちらの定義を参照する段階移行。
"""

from typing import Any
from pydantic import BaseModel, Field, field_validator


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="質問内容")
    top_k: int | None = Field(None, ge=1, le=10, description="検索結果の上位k件")

    @field_validator("question")
    @staticmethod
    def validate_question(v: str) -> str:
        if not v.strip():
            raise ValueError("質問内容を入力してください")
        return v.strip()


class DocumentInfo(BaseModel):
    content: str = Field(..., description="文書内容")
    metadata: dict[str, Any] = Field(default_factory=dict, description="メタデータ")


class SearchResponse(BaseModel):
    documents: list[DocumentInfo] = Field(..., description="検索結果のリスト")
    query: str = Field(..., description="検索クエリ")
    total_found: int = Field(..., description="見つかった文書数")


class AnswerResponse(BaseModel):
    answer: str = Field(..., description="生成された回答")
    question: str = Field(..., description="質問内容")
    documents: list[DocumentInfo] = Field(..., description="参照された文書")
    context_used: str = Field(..., description="使用されたコンテキスト")


class UploadResponse(BaseModel):
    status: str = Field(..., description="処理ステータス")
    message: str = Field(..., description="処理結果メッセージ")
    file_info: dict[str, Any] | None = Field(None, description="ファイル情報")
    vectorstore_info: dict[str, Any] | None = Field(
        None, description="ベクトルストア情報"
    )
