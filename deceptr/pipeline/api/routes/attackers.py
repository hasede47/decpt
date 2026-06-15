"""DECEPTR API — /api/attackers"""
from fastapi import APIRouter, Depends, Query
import aiomysql

from api.database import get_mysql_pool
from api.auth import get_current_user

router = APIRouter(prefix="/api/attackers", tags=["attackers"])


@router.get("")
async def list_attackers(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
    user: dict = Depends(get_current_user),
):
    pool = await get_mysql_pool()
    offset = (page - 1) * limit
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT COUNT(*) AS total FROM attackers")
            total = (await cur.fetchone())["total"]

            await cur.execute("""
                SELECT a.*, i.country_name, i.country_iso, i.max_severity, i.max_risk_score
                FROM attackers a
                LEFT JOIN iocs i ON i.ip_address = a.ip_address
                ORDER BY a.last_seen DESC LIMIT %s OFFSET %s
            """, (limit, offset))
            rows = await cur.fetchall()

    return {"data": rows, "total": total, "page": page, "limit": limit}
