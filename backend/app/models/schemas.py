"""
APIスキーマ定義
FastAPIのリクエスト/レスポンスモデルの定義
"""

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator


__all__ = [
    "QuestionRequest",
    "DocumentInfo",
    "SearchResponse",
    "AnswerResponse",
    "UploadResponse",
    "GenericUploadResponse",
    "UploadFormParams",
    "FileInfo",
    "DocumentListResponse",
    "DeleteDocumentRequest",
    "DeleteDocumentResponse",
    "SystemInfoResponse",
    "ErrorResponse",
    "HealthResponse",
    "UrlRequest",
]


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="質問内容")
    top_k: int | None = Field(None, ge=1, le=10, description="検索結果の上位k件")
    model: str | None = Field(None, description="LLMモデル指定")
    temperature: float | None = Field(
        None, ge=0.0, le=0.5, description="生成温度(0.0～0.5)"
    )
    max_output_tokens: int | None = Field(
        None, ge=1, le=4096, description="出力トークンの上限(見積もり用の上限)"
    )

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
    llm_model: str = Field(..., description="回答に用いたLLMモデル")
    citations: list[DocumentInfo] | list[str] | None = Field(
        None, description="引用。なければ ['引用なし']"
    )
    tokens: int | None = Field(None, description="見積もりトークン数")
    cost_jpy: float | None = Field(None, description="見積もりコスト(円)")


class UploadResponse(BaseModel):
    status: str = Field(..., description="処理ステータス")
    message: str = Field(..., description="処理結果メッセージ")
    file_info: dict[str, Any] | None = Field(None, description="ファイル情報")
    vectorstore_info: dict[str, Any] | None = Field(
        None, description="ベクトルストア情報"
    )


class FileInfo(BaseModel):
    filename: str = Field(..., description="ファイル名")
    file_id: str = Field(..., description="ファイルID")
    upload_time: str = Field(..., description="アップロード時刻")
    chunk_count: int = Field(..., description="チャンク数")
    file_size: int = Field(..., description="ファイルサイズ（バイト）")


class DocumentListResponse(BaseModel):
    files: list[FileInfo] = Field(..., description="アップロード済みファイル一覧")
    total_files: int = Field(..., description="総ファイル数")
    total_chunks: int = Field(..., description="総チャンク数")


class DeleteDocumentRequest(BaseModel):
    filename: str = Field(..., min_length=1, description="削除するファイル名")
    file_id: str = Field(..., min_length=1, description="削除するfile_id")


class DeleteDocumentResponse(BaseModel):
    status: str = Field(..., description="削除ステータス")
    message: str = Field(..., description="削除結果メッセージ")
    deleted_filename: str | None = Field(None, description="削除されたファイル名")
    deleted_file_id: str | None = Field(None, description="削除されたfile_id")
    deleted_chunks: int | None = Field(None, description="削除チャンク数")
    remaining_files: int | None = Field(None, description="残りファイル数")
    remaining_chunks: int | None = Field(None, description="残りチャンク数")


class SystemInfoResponse(BaseModel):
    status: str = Field(..., description="システムステータス")
    embedding_model: str = Field(..., description="埋め込みモデル")
    vectorstore_ready: bool = Field(..., description="ベクトルストア準備状況")
    vector_document_count: int | None = Field(
        None, description="保存されているベクトル化ドキュメント数"
    )
    collection_id: str | None = Field(None, description="コレクションID")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="エラータイプ")
    message: str = Field(..., description="エラーメッセージ")
    details: dict[str, Any] | None = Field(None, description="詳細情報")


class HealthResponse(BaseModel):
    status: str = Field(..., description="サービスステータス")
    version: str = Field(..., description="アプリケーションバージョン")
    timestamp: str = Field(..., description="チェック時刻")


class UrlRequest(BaseModel):
    url: str = Field(..., description="テキスト抽出対象のURL")
    chunk_size: int | None = Field(None, description="チャンクサイズ")
    chunk_overlap: int | None = Field(None, description="チャンクオーバーラップ")


class GenericUploadResponse(BaseModel):
    status: Literal["success"] = Field(..., description="処理ステータス")
    chunks_count: int = Field(..., description="作成されたチャンク数")
    collection_id: str = Field(..., description="ChromaコレクションID")
    filename: str = Field(..., description="元ファイル名")
    tenant: str | None = Field(None, description="テナント識別子")
