from __future__ import annotations
import datetime as dt

from fastapi import APIRouter, HTTPException, Query, Header
from typing import Any
from pydantic import BaseModel, Field

from sqlalchemy import exc

from ..core.config import settings
from .embed_ingest import _get_redis


router = APIRouter(prefix="/admin/reports", tags=["Reports"])


class InferredQuestions(BaseModel):
    """LLMが推定した質問のリスト"""

    questions: list[str] = Field(
        description="RAG AIチャットボットの利用者が入力したと推測される質問3つ",
        min_length=3,
        max_length=3,
    )


def _daterange(start: dt.date, end: dt.date):
    cur = start
    while cur <= end:
        yield cur
        cur = cur + dt.timedelta(days=1)


@router.get("/summary")
async def summary(
    tenant: str = Query(...),
    start: str = Query(..., description="YYYY-MM-DD"),
    end: str = Query(..., description="YYYY-MM-DD"),
    x_admin_api_secret: str = Header(default="", convert_underscores=True),
):
    if x_admin_api_secret != settings.admin_api_secret:
        raise HTTPException(401, "unauthorized")
    if tenant not in settings.embed_api_keys_map:
        raise HTTPException(400, "unknown tenant")
    try:
        d0 = dt.datetime.strptime(start, "%Y-%m-%d").date()
        d1 = dt.datetime.strptime(end, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(400, "invalid date format")
    if d1 < d0:
        raise HTTPException(400, "end before start")

    rc = _get_redis()
    if not rc:
        return {
            "questions": 0,
            "unique_users": 0,
            "resolved_rate": None,
            "zero_hit_rate": None,
            "tokens": 0,
            "cost_jpy": 0,
            "top_docs": [],
            "period": {"from": start, "to": end},
            "tenant": tenant,
        }

    total_q = 0
    total_tokens = 0.0
    total_cost = 0.0
    total_hit = 0
    total_zero = 0
    dau = 0
    fb_yes = 0
    fb_no = 0
    docs_top: dict[str, int] = {}

    for d in _daterange(d0, d1):
        # 日付オブジェトを文字列に変換
        day = d.strftime("%Y-%m-%d")
        total_q += int(rc.get(f"metrics:{day}:{tenant}:count") or 0)
        dau += int(rc.pfcount(f"hll:{day}:{tenant}:clients") or 0)
        total_tokens = float(rc.get(f"tokens:{day}:{tenant}") or 0)
        total_cost += float(rc.get(f"cost:{day}:{tenant}") or 0)
        h = rc.hgetall(f"docs:{day}:{tenant}") or {}
        total_hit += int(h.get("hit", 0) or 0)
        total_zero += int(h.get("zero_hit", 0) or 0)
        fb = rc.hgetall(f"feedback:{day}:{tenant}") or {}
        fb_yes += int(fb.get("yes", 0) or 0)
        fb_no += int(fb.get("no", 0) or 0)
        top = rc.hgetall(f"docs_top:{day}:{tenant}") or {}
        for k, v in top.items():
            docs_top[k] = docs_top.get(k, 0) + int(v or 0)

    resolved_rate = None
    if fb_yes + fb_no > 0:
        resolved_rate = fb_yes / (fb_yes + fb_no)
    zero_hit_rate = None
    if (total_hit + total_zero) > 0:
        zero_hit_rate = total_zero / (total_hit + total_zero)

    top_docs = sorted(
        [{"id": k, "count": v} for k, v in docs_top.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:5]

    return {
        "questions": total_q,
        "unique_users": dau,
        "resolved_rate": resolved_rate,
        "zero_hit_rate": zero_hit_rate,
        "tokens": total_tokens,
        "cost_jpy": total_cost,
        "top_docs": top_docs,
        "period": {"from": start, "to": end},
        "tenant": tenant,
    }


@router.get("/summary/evidence")
async def summary_evidence(
    tenant: str = Query(...),
    start: str = Query(..., description="YYYY-MM-DD"),
    end: str = Query(..., description="YYYY-MM-DD"),
    x_admin_api_secret: str = Header(default="", convert_underscores=True),
) -> dict[str, Any]:
    """上位チャンクに基づきエビデンスカードと推定質問"""
    if x_admin_api_secret != settings.admin_api_secret:
        raise HTTPException(401, "unauthorized")
    if tenant not in settings.embed_api_keys_map:
        raise HTTPException(400, "unknown tenant")
    try:
        d0 = dt.datetime.strptime(start, "%Y-%m-%d").date()
        d1 = dt.datetime.strptime(end, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(400, "invalid date format")
    if d1 < d0:
        raise HTTPException(400, "end before start")

    rc = _get_redis()
    if not rc:
        return {
            "tenant": tenant,
            "period": {"from": start, "to": end},
            "evidences": [],
            "inferred_question": None,
            "paraphrases": [],
            "common_keywords": [],
        }

    # 期間内のチャンクトップを集計
    chunks_top: dict[str, int] = {}
    for d in _daterange(d0, d1):
        day = d.strftime("%Y-%m-%d")
        h = rc.hgetall(f"chunks_top:{day}:{tenant}") or {}
        for k, v in h.items():
            chunks_top[k] = chunks_top.get(k, 0) + int(v or 0)

    # 上位10件（keyは"{file_id}:{chunk_index}"）
    pairs: list[tuple[str, int, int]] = []
    for key, cnt in chunks_top.items():
        try:
            fid, cidx = key.rsplit(":", 1)
            pairs.append((fid, int(cidx), int(cnt)))
        except Exception:
            continue
    pairs.sort(key=lambda x: x[2], reverse=True)
    top_pairs = pairs[:10]

    # RAG から内容取得
    from ..core.web.dependencies import get_rag_engine

    rag = get_rag_engine()
    chunks = await rag.get_chunks_by_file_and_index(
        [(fid, cidx) for fid, cidx, _ in top_pairs], tenant=tenant
    )

    # 抜粋とキーワード抽出（簡易）
    import re

    def _sentences(text: str) -> list[str]:
        text = re.sub(r"\s+", " ", text or "").strip()
        s = re.split(r"(?<=[。.!?])\s+", text)
        return [x.strip() for x in s if x.strip()]

    def _top_sentences(text: str, n: int = 6) -> list[str]:
        sents = _sentences(text)
        sents.sort(key=lambda x: len(x), reverse=True)
        return sents[:n]

    def _keywords(text: str, k: int = 5) -> list[str]:
        words = re.findall(r"[\wァ-ヶー一-龠々]+", text or "")
        freq: dict[str, int] = {}
        for w in words:
            if len(w) <= 1:
                continue
            freq[w] = freq.get(w, 0) + 1
        keys = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in keys[:k]]

    evidences: list[dict[str, Any]] = []
    for (fid, cidx, cnt), ch in zip(top_pairs, chunks):
        md = ch.get("metadata", {})
        fname = md.get("filename") or md.get("source") or "unknown"
        content = ch.get("content", "")
        evidences.append(
            {
                "title": f"{fname}｜#{cidx}",
                "source": {"file_id": fid, "chunk_index": cidx, "filename": fname},
                "hit_count": cnt,
                "excerpt": _top_sentences(content, 6),
                "keywords": _keywords(content, 5),
                "fulltext": content,
            }
        )

    all_text = "\n".join([e["fulltext"] for e in evidences])
    common_keywords = _keywords(all_text, 10)

    # LLMで推定質問（Structured Output使用）
    inferred_question: list[str] = []
    try:
        rag2 = get_rag_engine()
        llm, _ = rag2._get_llm(None, None, None)

        # Structured Outputを使用してLLMに構造化された出力を強制
        llm_with_structure = llm.with_structured_output(InferredQuestions)

        prompt = (
            "以下のチャンク抜粋はRAG AIチャットボットのコンテキストとして利用されたチャンクを、"
            "利用された回数の多い順に並べたものです。\n\n"
            "これらのチャンク抜粋から、RAG AIチャットボットの利用者が入力したと推測される質問を"
            "日本語で正確に3つ考えてください。\n\n"
            "チャンク抜粋:\n---\n"
            + "\n\n".join(["\n".join(e["excerpt"]) for e in evidences])
        )

        result = await llm_with_structure.ainvoke(prompt)
        inferred_question = result.questions
    except Exception as e:
        # ログ出力して、デバッグを容易にする
        print(f"Failed to infer questions: {e}")
        pass

    return {
        "tenant": tenant,
        "period": {"from": start, "to": end},
        "evidences": evidences,
        "inferred_question": inferred_question,
        "common_keywords": common_keywords,
    }
