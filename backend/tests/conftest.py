import os
import types
from contextlib import asynccontextmanager
from typing import Any

import pytest
from fastapi.testclient import TestClient

# テスト時は先に最低限の環境変数を設定（app.main を import する前に行う）
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("EMBED_ALLOWED_ORIGINS", "http://localhost")


class FakeDocument:
    def __init__(self, page_content: str, metadata: dict[str, Any] | None = None):
        self.page_content = page_content
        self.metadata = metadata or {}


class FakeRAGEngine:
    """外部依存(OpenAI/Chroma)を使わないテスト用スタブ"""

    async def create_vectorstore_from_chunks(
        self,
        chunks: list[str],
        filename: str,
        tenant: str | None = None,
        source_type: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        return {
            "status": "success",
            "chunks_count": len(chunks),
            "collection_id": "test-collection-id",
            "filename": filename,
        }

    async def search_documents(
        self, query: str, top_k: int | None, tenant: str | None = None
    ) -> list[FakeDocument]:
        # クエリ文字列を元に簡単なドキュメントを返す
        return [
            FakeDocument(page_content=f"doc for {query}", metadata={
                         "tenant": tenant})
        ]

    async def generate_answer(
        self,
        question: str,
        top_k: int | None,
        model: str | None = None,
        temperature: float | None = None,
        tenant: str | None = None,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        return {
            "answer": f"answer to: {question}",
            "documents": [
                {"content": f"doc for {question}", "metadata": {"tenant": tenant}}
            ],
            "context_used": f"context for {question}",
            "llm_model": model or "fake-llm",
        }

    async def get_system_info(self) -> dict[str, Any]:
        return {
            "status": "initialized",
            "embedding_model": "test-embed",
            "vectorstore_ready": True,
            "vector_document_count": 1,
            "collection_id": "test-collection-id",
        }

    async def get_document_list(self, tenant: str | None = None) -> dict[str, Any]:
        return {
            "files": [
                {
                    "filename": "sample.txt",
                    "file_id": "file-1",
                    "upload_time": "2024-01-01T00:00:00",
                    "chunk_count": 1,
                    "file_size": 12,
                }
            ],
            "total_files": 1,
            "total_chunks": 1,
        }

    async def delete_document_by_file_id(
        self,
        file_id: str | None = None,
        tenant: str | None = None,
    ) -> dict[str, Any]:
        return {
            "status": "success",
            "message": f"deleted {file_id}",
            "deleted_file_id": file_id,
            "deleted_chunks": 1,
            "remaining_files": 0,
            "remaining_chunks": 0,
        }

    async def reset_vectorstore(self) -> dict[str, str]:
        return {"status": "success", "message": "reset"}


@asynccontextmanager
async def dummy_lifespan(app):
    # 起動時初期化を無効化
    yield


@pytest.fixture()
def app(monkeypatch):
    from app.core.config import settings
    # ドキュメント用キーを設定
    settings.embed_api_keys = "acme:demo123"
    # TrustedHostMiddleware を避けるため debug を有効化
    settings.debug = True

    # 起動時の実初期化を無効化
    import app.main as main_mod

    monkeypatch.setattr(main_mod, "lifespan", dummy_lifespan)
    from app.main import create_app
    application = create_app()

    # 依存関係をスタブに差し替え
    from app.core.web.dependencies import get_rag_engine
    application.dependency_overrides[get_rag_engine] = lambda: FakeRAGEngine()

    return application


@pytest.fixture()
def client(app):
    return TestClient(app)
