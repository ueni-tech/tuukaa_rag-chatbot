import pytest
import tempfile
from pathlib import Path
from app.core import config
from app.core.rag_engine import RAGEngine


@pytest.fixture(autouse=True)
def patch_paths(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # persist_path, upload_path の property を両方上書き
        monkeypatch.setattr(
            type(config.settings),
            "persist_path",
            property(lambda self: tmp_path / "vectorstore"),
        )
        monkeypatch.setattr(
            type(config.settings),
            "upload_path",
            property(lambda self: tmp_path / "uploads"),
        )
        yield


@pytest.mark.asyncio
async def test_initialize():
    engine = RAGEngine()
    await engine.initialize()
    assert engine.embeddings is not None
    assert engine.llm is not None


@pytest.mark.asyncio
async def test_create_vectorstore_from_chunks():
    engine = RAGEngine()
    await engine.initialize()
    chunks = ["テスト文書1", "テスト文書2"]
    result = await engine.create_vectorstore_from_chunks(chunks)
    assert result["status"] == "success"
    assert result["chunks_count"] == 2


@pytest.mark.asyncio
async def test_search_documents():
    engine = RAGEngine()
    await engine.initialize()
    await engine.create_vectorstore_from_chunks(["テスト文書"])
    docs = await engine.search_documents("テスト")
    assert isinstance(docs, list)


@pytest.mark.asyncio
async def test_generate_answer():
    engine = RAGEngine()
    await engine.initialize()
    await engine.create_vectorstore_from_chunks(["テスト文書"])
    result = await engine.generate_answer("テストとは？", top_k=1)
    assert "answer" in result
    assert "documents" in result


@pytest.mark.asyncio
async def test_get_system_info():
    engine = RAGEngine()
    await engine.initialize()
    info = await engine.get_system_info()
    assert "status" in info
    assert "embedding_model" in info


@pytest.mark.asyncio
async def test_reset_vectorstore():
    engine = RAGEngine()
    await engine.initialize()
    await engine.create_vectorstore_from_chunks(["テスト文書"])
    result = await engine.reset_vectorstore()
    assert result["status"] == "success"
