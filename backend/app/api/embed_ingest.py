from __future__ import annotations

import re
import urllib.request
import codecs
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    UploadFile,
    File,
    Form,
    Request,
)
from fastapi.responses import StreamingResponse
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


# --- /ask の制限・課金用の簡易状態（メモリ内） ---
import asyncio
import datetime as dt
import hashlib
import json
import time

_rpm: dict[tuple[str, str, str], tuple[int, float]] = {}
_cost: dict[str, float] = {}
_DEF_PRICE = 0.002  # 仮のJPY/token 単価
_RESP_MAX_TOKENS = 1024


def _origin_allowed(origin: str | None) -> bool:
    allowed = settings.embed_allowed_origins_list
    if not origin:
        return True
    if "*" in allowed:
        return True
    return origin in allowed


# NOTE
# 汎用アップロード
# pdf/md/markdown/txt/docx/pptx/xlsx
@router.post("/upload", response_model=GenericUploadResponse)
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
        "xlsx": 10 * 1024 * 1024,
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
    elif ext == "xlsx":
        text = _normalize(dp.extract_text_from_xlsx_bytes(content))
        source_type = "xlsx"
    elif ext == "pdf":
        text = _normalize(dp.extract_text_from_pdf(content))
        source_type = "pdf"
    else:
        raise HTTPException(
            400, "未対応の拡張子です（pdf/md/markdown/txt/docx/pptx/xlsx）"
        )

    chunks = dp.split_text(text, chunk_size=cs, chunk_overlap=co)
    res = await rag.create_vectorstore_from_chunks(
        chunks,
        filename=file.filename,
        tenant=tenant,
        source_type=source_type,
        source=file.filename,
    )
    return GenericUploadResponse(**res, tenant=tenant)


# NOTE
# URLアップロード
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


@router.post("/search", response_model=SearchResponse)
async def docs_search(
    req: QuestionRequest,
    rag: RAGEngine = Depends(get_rag_engine),
    x_embed_key: str | None = Header(default=None, convert_underscores=False),
) -> SearchResponse:
    tenant = _tenant_from_key(x_embed_key)
    if not tenant:
        raise HTTPException(401, "無効な埋め込みキーです")
    docs = await rag.search_documents(req.question, req.top_k, tenant=tenant)
    items = [DocumentInfo(content=d.page_content, metadata=d.metadata) for d in docs]
    return SearchResponse(documents=items, query=req.question, total_found=len(items))


@router.post("/ask", response_model=AnswerResponse)
async def docs_ask(
    question_req: QuestionRequest,
    request: Request,
    rag: RAGEngine = Depends(get_rag_engine),
    x_embed_key: str | None = Header(default=None, convert_underscores=False),
) -> AnswerResponse | StreamingResponse:
    tenant = _tenant_from_key(x_embed_key)
    if not tenant:
        raise HTTPException(401, "無効な埋め込みキーです")

    # Allowlist (Origin)
    origin = request.headers.get("origin") if request else None
    if not _origin_allowed(origin):
        raise HTTPException(403, "origin not allowed")

    # RPM 制限
    ip = request.client.host if request and request.client else "0.0.0.0"
    key = (ip, x_embed_key or "", "/embed/docs/ask")
    now = time.time()
    cnt, first = _rpm.get(key, (0, now))
    if now - first >= 60:
        cnt, first = 0, now
    cnt += 1
    _rpm[key] = (cnt, first)
    if cnt > max(1, settings.rate_limit_rpm):
        raise HTTPException(429, "rate limit exceeded")

    # 日次ブレーカ（事前見積り）
    jst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    day = jst.strftime("%Y-%m-%d")
    used = _cost.get(day, 0.0)
    pre_tokens = max(1, len((question_req.question or "")) // 4) + _RESP_MAX_TOKENS
    pre_est_cost = pre_tokens * _DEF_PRICE
    if (
        settings.daily_budget_jpy > 0
        and used + pre_est_cost > settings.daily_budget_jpy
    ):
        raise HTTPException(402, "daily budget exceeded")

    # 回答生成（テナント分離）
    result = await rag.generate_answer(
        question=question_req.question,
        top_k=question_req.top_k,
        model=question_req.model,
        temperature=question_req.temperature,
        tenant=tenant,
    )

    # 引用情報の縮約・重複排除
    # documents は全文、citations は参照情報のみ（title/source/page など）
    documents_items = [
        DocumentInfo(content=d["content"], metadata=d["metadata"])
        for d in result["documents"]
    ]

    seen: set[tuple[str | None, int | None, str | None]] = set()
    citations: list[DocumentInfo] = []
    for d in result["documents"]:
        m = d.get("metadata") or {}
        source = m.get("source") or m.get("filename") or m.get("url") or "unknown"
        page = m.get("page") or m.get("page_number")
        try:
            page_num = int(page) if page is not None else None
        except Exception:
            page_num = None
        key = (str(source) if source is not None else None, page_num, m.get("file_id"))
        if key in seen:
            continue
        seen.add(key)

        title = m.get("title")
        label_parts = [
            p
            for p in [
                title,
                source,
                (f"p.{page_num}" if page_num is not None else None),
            ]
            if p
        ]
        label = " - ".join(label_parts) if label_parts else str(source)

        citations.append(
            DocumentInfo(
                content=label,
                metadata={
                    "source": source,
                    "page": page_num,
                    "file_id": m.get("file_id"),
                },
            )
        )

    # コスト（日次ブレーカ）
    answer_text = result.get("answer", "")
    tokens = max(1, len((question_req.question + "\n" + answer_text)) // 4)
    jst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    day = jst.strftime("%Y-%m-%d")
    used = _cost.get(day, 0.0)
    est_cost = tokens * _DEF_PRICE
    if settings.daily_budget_jpy > 0 and used + est_cost > settings.daily_budget_jpy:
        raise HTTPException(402, "daily budget exceeded")
    _cost[day] = used + est_cost

    # JSON ログ
    def _hash(v: str) -> str:
        return hashlib.sha256(v.encode("utf-8")).hexdigest()[:16]

    log = {
        "ip": ip,
        "key_hash": _hash(x_embed_key or ""),
        "tenant": tenant,
        "question_hash": _hash(question_req.question),
        "tokens": tokens,
        "cost_jpy": round(est_cost, 4),
        "status": "ok",
    }
    print(json.dump(log, ensure_ascii=False))

    # SSE or JSON
    accept = request.headers.get("accept", "").lower() if request else ""
    if "text/event-stream" in accept:

        async def gen():
            for line in (answer_text or "").splitlines():
                yield f"data: {line}\n\n"
                await asyncio.sleep(0.01)
            payload = {
                "citations": [c.model_dump() for c in (citations or [])]
                or ["引用なし"],
                "tokens": tokens,
                "cost_jpy": round(est_cost, 4),
            }
            yield "event: citations\n"
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    return AnswerResponse(
        answer=answer_text,
        question=question_req.question,
        documents=documents_items,
        context_used=result["context_used"],
        llm_model=result["llm_model"],
        citations=citations or [DocumentInfo(content="引用なし", metadata={})],
        tokens=tokens,
        cost_jpy=round(est_cost, 4),
    )


@router.get("/documents", response_model=DocumentListResponse)
async def docs_list(
    rag: RAGEngine = Depends(get_rag_engine),
    X_embed_key: str | None = Header(default=None, convert_underscores=False),
) -> DocumentListResponse:
    tenant = _tenant_from_key(X_embed_key)
    if not tenant:
        raise HTTPException(401, "無効な埋め込みキーです")
    result = await rag.get_document_list(tenant=tenant)
    return DocumentListResponse(
        files=result["files"],
        total_files=result["total_files"],
        total_chunks=result["total_chunks"],
    )


@router.delete("/documents", response_model=DeleteDocumentResponse)
async def docs_delete(
    req: DeleteDocumentRequest,
    rag: RAGEngine = Depends(get_rag_engine),
    x_embed_key: str | None = Header(default=None, convert_underscores=False),
) -> DeleteDocumentResponse:
    tenant = _tenant_from_key(x_embed_key)
    if not tenant:
        raise HTTPException(401, "無効な埋め込みキーです")
    # tenant + filename + file_id で削除
    if req.file_id and req.filename:
        result = await rag.delete_document_by_file_id(req.file_id, tenant=tenant)
        return DeleteDocumentResponse(
            status=result["status"],
            message=result["message"],
            deleted_file_id=req.file_id,
            deleted_filename=req.filename,
            deleted_chunks=result.get("deleted_chunks"),
            remaining_files=result.get("remaining_files"),
            remaining_chunks=result.get("remaining_chunks"),
        )

    raise HTTPException(400, "filename と file_id を指定してください")


@router.get("/system/info", response_model=SystemInfoResponse)
async def docs_system_info(
    rag: RAGEngine = Depends(get_rag_engine),
) -> SystemInfoResponse:
    info = await rag.get_system_info()
    return SystemInfoResponse(
        status=info["status"],
        embedding_model=info["embedding_model"],
        vectorstore_ready=info["vectorstore_ready"],
        vector_document_count=info.get("vector_document_count"),
        collection_id=info.get("collection_id"),
    )


@router.post("/system/reset")
async def docs_system_reset(
    rag: RAGEngine = Depends(get_rag_engine),
) -> dict[str, str]:
    return await rag.reset_vectorstore()
