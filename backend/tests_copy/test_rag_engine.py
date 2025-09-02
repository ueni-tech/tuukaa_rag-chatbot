import pytest

from app.core.services.rag_engine import RAGEngine


@pytest.mark.asyncio
async def test_get_system_info_without_real_init():
    engine = RAGEngine()
    # 実初期化せずに実行してもクラッシュしないこと
    info = await engine.get_system_info()
    assert "status" in info
    assert info["vectorstore_ready"] in {True, False}


@pytest.mark.asyncio
async def test_search_documents_requires_vectorstore():
    engine = RAGEngine()
    with pytest.raises(RuntimeError):
        await engine.search_documents("hello")


import tempfile
from pathlib import Path

import pytest

from app.core import config
from app.core.services.rag_engine import RAGEngine


@pytest.fixture()
def temp_paths(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
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
async def test_get_system_info_without_init(temp_paths):
    engine = RAGEngine()
    info = await engine.get_system_info()
    assert info["status"] in ("initialized", "not_initialized")
    assert "embedding_model" in info


@pytest.mark.asyncio
async def test_reset_vectorstore_without_store(temp_paths):
    engine = RAGEngine()
    res = await engine.reset_vectorstore()
    assert res["status"] in ("success", "error")
