"""DECEPTR API — /api/alerts"""
from fastapi import APIRouter, Depends, HTTPException, Query
import aiomysql

from api.database import get_mysql_pool, get_es, EVENT_INDEX_PATTERN
from api.auth import get_current_user
from api.models.schemas import AcknowledgeRequest

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
    severity: str | None = None,
    src_ip: str | None = None,
    hours: int = Query(24, ge=0),
    user: dict = Depends(get_current_user),
):
    pool = await get_mysql_pool()
    where = ["1=1"]
    params: list = []

    if severity:
        where.append("severity=%s")
        params.append(severity.upper())
    if src_ip:
        where.append("src_ip=%s")
        params.append(src_ip)
    if hours > 0:
        where.append("created_at >= NOW() - INTERVAL %s HOUR")
        params.append(hours)

    where_sql = " AND ".join(where)
    offset = (page - 1) * limit

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"SELECT COUNT(*) AS total FROM alerts WHERE {where_sql}", params
            )
            total = (await cur.fetchone())["total"]

            await cur.execute(
                f"SELECT * FROM alerts WHERE {where_sql} "
                f"ORDER BY created_at DESC LIMIT %s OFFSET %s",
                params + [limit, offset]
            )
            rows = await cur.fetchall()

    return {
        "data": rows, "total": total, "page": page, "limit": limit,
        "pages": (total + limit - 1) // limit if limit else 1
    }


@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("CALL get_dashboard_stats();")
            stats = await cur.fetchone()
    return stats


@router.get("/timeline")
async def get_timeline(hours: int = 24, user: dict = Depends(get_current_user)):
    """Histogramme horaire des événements (Elasticsearch)."""
    es = get_es()
    resp = await es.search(
        index=EVENT_INDEX_PATTERN,
        body={
            "size": 0,
            "query": {"range": {"timestamp": {"gte": f"now-{hours}h"}}},
            "aggs": {
                "by_hour": {
                    "date_histogram": {"field": "timestamp", "fixed_interval": "1h"}
                }
            }
        }
    )
    buckets = resp.get("aggregations", {}).get("by_hour", {}).get("buckets", [])
    return [{"ts": b["key_as_string"], "count": b["doc_count"]} for b in buckets]


@router.patch("/{alert_id}/acknowledge")
async def acknowledge(alert_id: int, req: AcknowledgeRequest,
                      user: dict = Depends(get_current_user)):
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            rows = await cur.execute(
                "UPDATE alerts SET acknowledged=1, acknowledged_by=%s, "
                "acknowledged_at=NOW(), notes=%s WHERE id=%s",
                (user["username"], req.notes, alert_id)
            )
    if rows == 0:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    return {"status": "ok"}
