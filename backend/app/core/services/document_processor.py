"""
文書処理モジュール
PDF読み込み、テキスト抽出、チャンク分割などの
文書処理に関する機能を提供するモジュール
"""

import gc
import shutil
from pathlib import Path
import io

import pypdf
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..config import settings

import asyncio


class DocumentProcessor:
    """文書処理クラス
    PDF文書の読み込み、テキスト抽出、チャンク分割を行う
    """

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.max_chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\\n\\n", "\\n", " ", ""],
            length_function=len,
        )

    async def extract_text_from_pdf(self, data: bytes) -> str:
        """PDFからテキスト抽出"""
        try:
            reader = pypdf.PdfReader(io.BytesIO(data))
            if len(reader.pages) == 0:
                raise ValueError("PDFにページが含まれていません")
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            if not text_parts:
                raise ValueError("PDFからテキストを抽出できませんでした")
            return "\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"PDF読み込みエラー: {str(e)}")

    def split_text(
        self,
        text: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> list[str]:
        """テキストをチャンクに分割"""
        if chunk_size or chunk_overlap:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size or settings.max_chunk_size,
                chunk_overlap=chunk_overlap or settings.chunk_overlap,
                separators=["\\n\\n", "\\n", " ", ""],
                length_function=len,
            )
            return splitter.split_text(text)
        return self.text_splitter.split_text(text)

    def count_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """テキストのトークン数をカウント"""
        try:
            enc = tiktoken.encoding_for_model(model)
            return len(enc.encode(text))
        except Exception:
            return len(text) // 4

    def cleanup_upload_directory(self, keep_files: list[str] | None) -> None:
        """アップロードディレクトリのクリーンアップ"""
        upload_dir = settings.upload_path
        if not upload_dir.exists():
            return
        keep_files = keep_files or []
        for file_path in upload_dir.iterdir():
            if file_path.is_file() and file_path.name not in keep_files:
                try:
                    file_path.unlink()
                except Exception:
                    pass
