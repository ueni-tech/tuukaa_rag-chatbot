from __future__ import annotations
import datetime as dt

from fastapi import APIRouter, HTTPException, Query, Header

from ..core.config import settings
from .embed_ingest import _get_redis


router = APIRouter(prefix="/admin/reports", tags=["Reports"])


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
        dau += int(rc.pfcount(f"hll:{day}:{tenant}") or 0)
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
