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
    "FileInfo",
    "DocumentListResponse",
    "DeleteDocumentRequest",
    "DeleteDocumentResponse",
    "SystemInfoResponse",
    "ErrorResponse",
    "HealthResponse",
    "UrlRequest",
    "FeedbackRequest",
]


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="質問内容")
    top_k: int | None = Field(None, ge=1, le=20, description="検索結果の上位k件")
    model: str | None = Field(None, max_length=100, description="LLMモデル指定")
    temperature: float | None = Field(
        None, ge=0.0, le=0.5, description="生成温度(0.0～0.5)"
    )
    max_output_tokens: int | None = Field(
        None, ge=1, le=4096, description="出力トークンの上限(見積もり用の上限)"
    )
    client_id: str | None = Field(
        None, max_length=64, description="匿名クライアントID（ブラウザ単位）"
    )
    session_id: str | None = Field(
        None,
        max_length=64,
        description="セッションID（30分非活動で再発行など任意運用）",
    )
    message_id: str | None = Field(
        None, max_length=64, description="このやりとりのメッセージID"
    )

    @field_validator("question")
    @classmethod
    def sanitize_question(cls, v: str) -> str:
        """質問文のサニタイゼーション: 制御文字を除去し、安全な文字列に変換"""
        if not v.strip():
            raise ValueError("質問内容を入力してください")
        # 制御文字を除去（印字可能文字と空白文字のみ許可）
        sanitized = "".join(char for char in v if char.isprintable() or char.isspace())
        return sanitized.strip()

    @field_validator("model")
    @classmethod
    def sanitize_model(cls, v: str | None) -> str | None:
        """モデル名のサニタイゼーション: 英数字、ハイフン、アンダースコアのみ許可"""
        if v is None:
            return None
        # 安全な文字のみ許可
        import re

        if not re.match(r"^[a-zA-Z0-9\-_.]+$", v):
            raise ValueError("モデル名に不正な文字が含まれています")
        return v.strip()

    @field_validator("client_id", "session_id", "message_id")
    @classmethod
    def sanitize_ids(cls, v: str | None) -> str | None:
        """ID類のサニタイゼーション: 英数字とハイフンのみ許可"""
        if v is None:
            return None
        # 安全な文字のみ許可
        import re

        if not re.match(r"^[a-zA-Z0-9\-]+$", v):
            raise ValueError("IDに不正な文字が含まれています")
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
    llm_model: str = Field(..., description="回答に用いたLLMモデル")
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


class TenantInfo(BaseModel):
    name: str = Field(..., description="テナント名")
    key: str = Field(..., description="埋め込みキー")


class TenantListResponse(BaseModel):
    tenants: list[TenantInfo] = Field(..., description="テナント一覧")


class FeedbackRequest(BaseModel):
    message_id: str = Field(
        ..., min_length=1, max_length=64, description="メッセージID"
    )
    resolved: bool = Field(..., description="解決フラグ")
    client_id: str | None = Field(None, max_length=64, description="匿名クライアントID")
    session_id: str | None = Field(None, max_length=64, description="セッションID")

    @field_validator("message_id", "client_id", "session_id")
    @classmethod
    def sanitize_feedback_ids(cls, v: str | None) -> str | None:
        """ID類のサニタイゼーション: 英数字とハイフンのみ許可"""
        if v is None:
            return None
        # 安全な文字のみ許可
        import re

        if not re.match(r"^[a-zA-Z0-9\-]+$", v):
            raise ValueError("IDに不正な文字が含まれています")
        return v.strip()
