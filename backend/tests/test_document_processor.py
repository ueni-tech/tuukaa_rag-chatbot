from app.core.services.document_processor import DocumentProcessor


def test_split_text_default():
    dp = DocumentProcessor()
    text = "A" * 1000
    chunks = dp.split_text(text)
    assert isinstance(chunks, list)
    assert len(chunks) >= 1


def test_extract_text_from_txt_bytes_utf8():
    dp = DocumentProcessor()
    data = "こんにちは".encode("utf-8")
    text = dp.extract_text_from_txt_bytes(data)
    assert "こんにちは" in text
