import pytest
from pathlib import Path
from app.core.document_processor import DocumentProcessor
import asyncio


@pytest.mark.asyncio
async def test_extract_text_form_pdf():
    processor = DocumentProcessor()
    # 既存のサンプルPDFがある場合のみ検証。なければスキップ（環境依存回避）。
    path = Path("uploads") / "sample.pdf"
    if not path.exists():
        pytest.skip("sample.pdf が存在しないためスキップ")
    text = await processor.extract_text_form_pdf(path)
    assert isinstance(text, str)
    assert len(text) > 0  # テキストが抽出できていること


def test_split_text():
    processor = DocumentProcessor()
    text = "これはテストです。\n\nこれは2つ目の段落です。"
    chunks = processor.split_text(text, chunk_size=1000, chunk_overlap=0)
    assert isinstance(chunks, list)
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_count_tokens():
    processor = DocumentProcessor()
    text = "テスト"
    tokens = processor.count_tokens(text)
    assert isinstance(tokens, int)
    assert tokens > 0
