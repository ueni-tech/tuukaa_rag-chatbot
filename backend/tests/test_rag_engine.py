import tempfile
from pathlib import Path

import pytest

from app.core import config
from app.core.services.rag_engine import RAGEngine


@pytest.mark.asyncio
async def test_get_system_info_without_real_init():
    engin = RAGEngine()
    info = await engin.get_system_info()
    assert "status" in info
    assert info["vectorstore_ready"] in {True, False}


@pytest.mark.asyncio
async def test_search_documents_requires_vectorstore():
    engine = RAGEngine()
    with pytest.raises(RuntimeError):
        await engine.search_documents("hello")
