from __future__ import annotations

import re
import urllib.request
import codecs
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from ..core.config import settings
from ..core.web.dependencies import get_rag_engine
from ..core.services.rag_engine import RAGEngine
from ..core.services.document_processor import DocumentProcessor

from ..models.schemas import (
    QuestionRequest,
    SearchResponse,
    DocumentInfo,
    AnswerResponse,
    DocumentListResponse,
    DeleteDocumentRequest,
    DeleteDocumentResponse,
    SystemInfoResponse,
    UrlRequest,
    GenericUploadResponse,
)

router = APIRouter(prefix="/embed/docs", tags=["EmbedDocs"])

dp = DocumentProcessor()


def _tenant_from_key(key: str | None) -> str | None:
    if not key:
        return None
    for tenant, k in settings.embed_api_keys_map.items():
        if k == key:
            return tenant
    return None


def _normalize(text: str) -> str:
    text = re.sub(r"\r\n|\r|\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _strip_tags(html: str) -> str:
    html = re.sub(
        r"\s*<\s*(script|style)\b[\s\S]*?<\s*/\s*\1\s*>\s*",
        " ",
        html,
        flags=re.I,
    )
    html = re.sub(
        r"\s*<\s*noscript\b[\s\S]*?<\s*/\s*noscript\s*>\s*",
        " ",
        html,
        flags=re.I,
    )
    return _normalize(re.sub(r"<[^>]+>", " ", html))


@router.post("/url")
async def ingest_url(
    p: UrlRequest,
    rag: RAGEngine = Depends(get_rag_engine),
    x_embed_key: str | None = Header(default=None, convert_underscores=False),
) -> dict[str, Any]:
    tenant = _tenant_from_key(x_embed_key)
    if not tenant:
        raise HTTPException(401, "無効な埋め込みキーです")
    try:
        with urllib.request.urlopen(p.url, timeout=20) as r:
            MAX_BYTES = 2 * 1024 * 1024
            cl = r.headers.get("Content-Length")
            if cl:
                try:
                    if int(cl) > MAX_BYTES:
                        raise HTTPException(413, "本文が大きすぎます")
                except ValueError:
                    pass

            buf = r.read(MAX_BYTES + 1)
            if len(buf) > MAX_BYTES:
                raise HTTPException(413, "本文が大きすぎます")

            enc = None
            try:
                enc = r.headers.get_content_charset()
            except Exception:
                pass
            if not enc:
                if buf.startswith(codecs.BOM_UTF8):
                    enc = "utf-8-sig"
                else:
                    enc = "utf-8"

            html = bytes(buf).decode(enc, errors="replace")
    except Exception as e:
        raise HTTPException(400, f"URL取得に失敗: {e}")

    text = _strip_tags(html)
    if not text:
        raise HTTPException(400, f"本文抽出に失敗しました")

    chunk_size = p.chunk_size or settings.max_chunk_size
    chunk_overlap = p.chunk_overlap or settings.chunk_overlap
    chunks = dp.split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    res = await rag.create_vectorstore_from_chunks(
        chunks, filename=p.url, tenant=tenant, source_type="url", source=p.url
    )
    return {**res, "tenant": tenant}


# NOTE
# 汎用アップロード
# pdf/md/markdown/txt/docx/pptx
@router.post("/upload", response_class=GenericUploadResponse)
async def ingest_any_file(
    file: UploadFile = File(...),
    chunk_size: int | None = Form(None),
    chunk_overlap: int | None = Form(None),
    rag: RAGEngine = Depends(get_rag_engine),
    x_embed_key: str | None = Header(default=None, convert_underscores=False),
) -> GenericUploadResponse:
    tenant = _tenant_from_key(x_embed_key)
    if not tenant:
        raise HTTPException(401, "無効な埋め込みキーです")

    fname = (file.filename or "").lower()
    ext = fname.rsplit(".", 1)[-1] if "." in fname else ""

    MAX = {
        "pdf": 10 * 1024 * 1024,
        "docx": 10 * 1024 * 1024,
        "pptx": 10 * 1024 * 1024,
        "md": 2 * 1024 * 1024,
        "markdown": 2 * 1024 * 1024,
        "txt": 2 * 1024 * 1024,
    }
    content = await file.read()
    max_bytes = MAX.get(ext, 2 * 1024 * 1024)
    if len(content) > max_bytes:
        raise HTTPException(413, "ファイルサイズ上限を超えています")

    cs = chunk_size or settings.max_chunk_size
    co = chunk_overlap or settings.chunk_overlap

    text = None
    if ext in ("md", "markdown"):
        enc = "utf-8-sig" if content.startswith(codecs.BOM_UTF8) else "utf-8"
        text = _normalize(content.decode(enc, errors="replace"))
        source_type = "markdown"
    elif ext == "txt":
        text = _normalize(dp.extract_text_from_txt_bytes(content))
        source_type = "text"
    elif ext == "docx":
        text = _normalize(dp.extract_text_from_docx_bytes(content))
        source_type = "docx"
    elif ext == "pptx":
        text = _normalize(dp.extract_text_from_pptx_bytes(content))
        source_type = "pptx"
    elif ext == "pdf":
        text = _normalize(dp.extract_text_from_pdf(content))
        source_type = "pdf"
    else:
        raise HTTPException(400, "未対応の拡張子です（pdf/md/markdown/txt/docx/pptx）")

    chunks = dp.split_text(text, chunk_size=cs, chunk_overlap=co)
    res = await rag.create_vectorstore_from_chunks(
        chunks,
        filename=file.filename,
        tenant=tenant,
        source_type=source_type,
        source=file.filename,
    )
    return GenericUploadResponse(**res, tenant=tenant)
