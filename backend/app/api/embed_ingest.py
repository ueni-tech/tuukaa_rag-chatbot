from __future__ import annotations
import time
import json
import hashlib
import datetime as dt
import asyncio
from uuid import uuid4
import hashlib

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
from redis import Redis
import os

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
    FeedbackRequest,
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

_rpm: dict[tuple[str, str, str], tuple[int, float]] = {}
_cost: dict[tuple[str, str], float] = {}

try:
    # 既定: gpt-4o-mini の実コスト（USD/1M tokens）を為替換算 → JPY/token（in/out 別）
    DEFAULT_USD_PER_MTOKEN_IN = 0.15
    DEFAULT_USD_PER_MTOKEN_OUT = 0.60
    _RATE = float(getattr(settings, "usd_jpy_rate", 150.0))
    _DEF_PRICE_IN = (float(DEFAULT_USD_PER_MTOKEN_IN) / 1_000_000.0) * _RATE
    _DEF_PRICE_OUT = (float(DEFAULT_USD_PER_MTOKEN_OUT) / 1_000_000.0) * _RATE
except Exception:
    # 例外時も gpt-4o-mini の in/out で換算（単位一貫性を維持）
    _RATE = float(getattr(settings, "usd_jpy_rate", 150.0))
    _DEF_PRICE_IN = (0.15 / 1_000_000.0) * _RATE
    _DEF_PRICE_OUT = (0.60 / 1_000_000.0) * _RATE

_RESP_MAX_TOKENS = 1024


# JSTの翌日0時までの残秒数を返す
def _second_until_next_jst_midnight(now: dt.datetime | None = None) -> int:
    jst = dt.timezone(dt.timedelta(hours=9))
    now = now or dt.datetime.now(jst)
    next_day = (now + dt.timedelta(days=1)).date()
    next_midnight = dt.datetime.combine(next_day, dt.time(0, 0, 0), tzinfo=jst)
    return max(1, int((next_midnight - now).total_seconds()))


def _get_redis() -> Redis | None:
    url = settings.redis_connection_url
    if not url:
        return None
    try:
        client = Redis.from_url(url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


# NOTE
# 汎用アップロード
# pdf/md/markdown/txt/docx/pptx/xlsx
@router.post("/upload", response_model=GenericUploadResponse)
async def ingest_any_file(
    file: UploadFile = File(...),
    chunk_size: int | None = Form(None),
    chunk_overlap: int | None = Form(None),
    rag: RAGEngine = Depends(get_rag_engine),
    x_embed_key: str | None = Header(default=None, convert_underscores=True),
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
    x_embed_key: str | None = Header(default=None, convert_underscores=True),
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
        raise HTTPException(400, "本文抽出に失敗しました")

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
    x_embed_key: str | None = Header(default=None, convert_underscores=True),
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
    x_embed_key: str | None = Header(default=None, convert_underscores=True),
    x_admin_api_secret: str | None = Header(default=None, convert_underscores=True),
    x_test_environment: str | None = Header(default=None, convert_underscores=True),
) -> AnswerResponse | StreamingResponse:
    tenant = _tenant_from_key(x_embed_key)
    if not tenant:
        raise HTTPException(401, "無効な埋め込みキーです")

    is_admin = bool(
        x_admin_api_secret
        and x_admin_api_secret == getattr(settings, "admin_api_secret", None)
    )

    # テスト環境フラグをチェック（Redis集計をスキップ）
    is_test = x_test_environment == "true"

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

    # 日次ブレーカ（事前見積り、管理者はバイパス）
    if not is_admin:
        jst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
        day = jst.strftime("%Y-%m-%d")
        # MODEL_PRICING: in/out を分離し、RAGの参照文書も入力側に加算
        selected_model = (question_req.model or settings.default_model or "").strip()
        inout = settings.model_pricing_inout_map.get(selected_model)
        if inout is None:
            usd_in = usd_out = None
        else:
            usd_in, usd_out = inout
        if usd_in is None:
            jpy_in = _DEF_PRICE_IN
        else:
            jpy_in = float(usd_in) * float(getattr(settings, "usd_jpy_rate", 150.0))
        if usd_out is None:
            jpy_out = _DEF_PRICE_OUT
        else:
            jpy_out = float(usd_out) * float(getattr(settings, "usd_jpy_rate", 150.0))

        max_out = question_req.max_output_tokens or getattr(
            settings, "default_max_output_tokens", _RESP_MAX_TOKENS
        )

        # 入力見積: 質問 + 参照文書(後で実際に取得するため、ここでは概算: 質問長のk倍)
        # 事前見積は保守的に質問長×2 をRAGコンテキスト概算とする
        qlen = len((question_req.question or ""))
        # question + approx(context)
        input_est_tokens = max(1, (qlen + 2 * qlen) // 4)
        output_est_tokens = max_out
        pre_est_cost = input_est_tokens * jpy_in + output_est_tokens * jpy_out
        rc = _get_redis()
        if rc:
            key = f"cost:{day}:{tenant}"
            used = float(rc.get(key) or 0.0)
        else:
            used = _cost.get((day, tenant), 0.0)

        if (
            settings.daily_budget_jpy > 0
            and used + pre_est_cost > settings.daily_budget_jpy
        ):
            raise HTTPException(402, "本日の使用上限に達しました")

    # 回答生成（テナント分離）
    result = await rag.generate_answer(
        question=question_req.question,
        top_k=question_req.top_k,
        model=question_req.model,
        temperature=question_req.temperature,
        tenant=tenant,
        max_output_tokens=question_req.max_output_tokens,
    )

    # 参照文書の情報を構築
    documents_items = [
        DocumentInfo(content=d["content"], metadata=d["metadata"])
        for d in result["documents"]
    ]

    # コスト（日次ブレーカ） 実績: 入力(質問+実際のcontext) と 出力(回答) を分離
    answer_text = result.get("answer", "")
    context_used = result.get("context_used", "")
    # tiktokenで実測（モデルは指定があればそれを使用、なければ既定）
    try:
        import tiktoken

        model_for_encoding = (
            question_req.model or settings.default_model or ""
        ).strip() or "gpt-4o-mini"
        try:
            enc = tiktoken.encoding_for_model(model_for_encoding)
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")
        input_tokens = max(
            1,
            len(
                enc.encode((question_req.question or "") + "\n" + (context_used or ""))
            ),
        )
        output_tokens = max(1, len(enc.encode(answer_text or "")))
    except Exception:
        # フォールバック（概算）
        input_tokens = max(1, len((question_req.question + "\n" + context_used)) // 4)
        output_tokens = max(1, len(answer_text) // 4)
    jst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    day = jst.strftime("%Y-%m-%d")
    # 事後計上: in/out 単価で合計
    selected_model = (question_req.model or settings.default_model or "").strip()
    inout = settings.model_pricing_inout_map.get(selected_model)
    if inout is None:
        usd_in = usd_out = None
    else:
        usd_in, usd_out = inout
    if usd_in is None:
        jpy_in = _DEF_PRICE_IN
    else:
        jpy_in = float(usd_in) * float(getattr(settings, "usd_jpy_rate", 150.0))
    if usd_out is None:
        jpy_out = _DEF_PRICE_OUT
    else:
        jpy_out = float(usd_out) * float(getattr(settings, "usd_jpy_rate", 150.0))

    est_cost = input_tokens * jpy_in + output_tokens * jpy_out

    # コスト記録（管理者またはテスト環境の場合はスキップ）
    if not is_admin and not is_test:
        rc = _get_redis()
        if rc:
            key = f"cost:{day}:{tenant}"
            used = float(rc.get(key) or 0.0)
            if (
                settings.daily_budget_jpy > 0
                and used + est_cost > settings.daily_budget_jpy
            ):
                raise HTTPException(402, "本日の使用上限に達しました")
            pipe = rc.pipeline()
            pipe.incrbyfloat(key, est_cost)
            pipe.ttl(key)
            _, ttl = pipe.execute()
            if ttl == -1:
                rc.expire(key, _second_until_next_jst_midnight(jst))
        else:
            used = _cost.get((day, tenant), 0.0)
            if (
                settings.daily_budget_jpy > 0
                and used + est_cost > settings.daily_budget_jpy
            ):
                raise HTTPException(402, "本日の予算を超過しました")
            _cost[(day, tenant)] = used + est_cost

    # JSON ログ（機密情報マスキング強化）
    def _hash(v: str) -> str:
        return hashlib.sha256(v.encode("utf-8")).hexdigest()[:16]

    log = {
        "ip_hash": _hash(ip),  # IPアドレスもハッシュ化
        "key_hash": _hash(x_embed_key or ""),
        "tenant": tenant,
        "question_hash": _hash(question_req.question),  # 質問の実テキストは記録しない
        "tokens": input_tokens + output_tokens,
        "cost_jpy": round(est_cost, 4),
        "status": "ok",
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    print(json.dumps(log, ensure_ascii=False))

    message_id = question_req.message_id or str(uuid4()).replace("-", "")
    client_id = (
        question_req.client_id
        or hashlib.sha256((request.client.host or "").encode()).hexdigest()[:16]
    )
    doc_count = len(documents_items)
    zero_hit = 1 if doc_count == 0 else 0

    # Redis集計（管理者またはテスト環境の場合はスキップ）
    if not is_admin and not is_test:
        rc = _get_redis()
        jst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
        day = jst.strftime("%Y-%m-%d")
        if rc:
            pipe = rc.pipeline()
            pipe.incr(f"metrics:{day}:{tenant}:count", 1)
            pipe.pfadd(f"hll:{day}:{tenant}:clients", client_id)
            pipe.incrbyfloat(
                f"tokens:{day}:{tenant}", float(input_tokens + output_tokens)
            )
            pipe.hincrby(f"docs:{day}:{tenant}", "zero_hit", zero_hit)
            pipe.hincrby(f"docs:{day}:{tenant}", "hit", 1 - zero_hit)
            for d in documents_items[:10]:
                fid = d.metadata.get("file_id") or d.metadata.get("source") or "unknown"
                pipe.hincrby(f"docs_top:{day}:{tenant}", fid, 1)
                cidx = d.metadata.get("chunk_index")
                if cidx is not None:
                    pipe.hincrby(f"chunks_top:{day}:{tenant}", f"{fid}:{cidx}", 1)
            pipe.lpush(
                f"logs:ask:{tenant}",
                json.dumps(
                    {
                        "ts": int(time.time()),
                        "tenant": tenant,
                        "message_id": message_id,
                        "event": "ask",
                        "tokens": int(input_tokens + output_tokens),
                        "cost_jpy": round(est_cost, 4),
                        "doc_count": doc_count,
                        "status": "ok",
                    },
                    ensure_ascii=False,
                ),
            )
            pipe.ltrim(f"logs:ask:{tenant}", 0, 1000)
            pipe.execute()

    # SSE or JSON
    accept = request.headers.get("accept", "").lower() if request else ""
    if "text/event-stream" in accept:

        async def gen():
            # 初回ハートビート（SSEコメント）
            try:
                yield ":\n\n"
            except Exception:
                return
            last_hb = time.monotonic()
            for line in (answer_text or "").splitlines():
                yield f"data: {line}\n\n"
                # 心拍を一定間隔で送信
                now = time.monotonic()
                if now - last_hb >= 5.0:
                    yield ":\n\n"
                    last_hb = now
                await asyncio.sleep(0.01)
            payload = {
                "tokens": input_tokens + output_tokens,
                "cost_jpy": round(est_cost, 4),
            }
            yield "event: citations\n"
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    return AnswerResponse(
        answer=answer_text,
        question=question_req.question,
        documents=documents_items,
        llm_model=result["llm_model"],
        tokens=input_tokens + output_tokens,
        cost_jpy=round(est_cost, 4),
    )


@router.get("/documents", response_model=DocumentListResponse)
async def docs_list(
    rag: RAGEngine = Depends(get_rag_engine),
    x_embed_key: str | None = Header(default=None, convert_underscores=True),
) -> DocumentListResponse:
    tenant = _tenant_from_key(x_embed_key)
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
    x_embed_key: str | None = Header(default=None, convert_underscores=True),
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


@router.post("/feedback")
async def docs_feedback(
    payload: FeedbackRequest,
    x_embed_key: str | None = Header(default=None, convert_underscores=True),
    x_admin_api_secret: str | None = Header(default=None, convert_underscores=True),
    x_test_environment: str | None = Header(default=None, convert_underscores=True),
):
    tenant = _tenant_from_key(x_embed_key)
    if not tenant:
        raise HTTPException(401, "無効な埋め込みキーです")

    is_admin = bool(
        x_admin_api_secret
        and x_admin_api_secret == getattr(settings, "admin_api_secret", None)
    )

    # テスト環境フラグをチェック（Redis集計をスキップ）
    is_test = x_test_environment == "true"

    resolved = payload.resolved
    message_id = payload.message_id
    if not message_id:
        raise HTTPException(400, "message_id は必須です")

    # Redis集計（管理者またはテスト環境の場合はスキップ）
    if not is_admin and not is_test:
        rc = _get_redis()
        jst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
        day = jst.strftime("%Y-%m-%d")
        if rc:
            rc.hincrby(f"feedback:{day}:{tenant}", "yes" if resolved else "no", 1)
            rc.lpush(
                f"logs:feedback:{tenant}",
                json.dumps(
                    {
                        "ts": int(time.time()),
                        "tenant": tenant,
                        "message_id": message_id,
                        "event": "feedback",
                        "resolved": resolved,
                        "client_id": payload.client_id,
                        "session_id": payload.session_id,
                    },
                    ensure_ascii=False,
                ),
            )
            rc.ltrim(f"logs:feedback:{tenant}", 0, 1000)
    return {"status": "ok"}


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
