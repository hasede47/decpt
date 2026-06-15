"""DECEPTR API — /api/campaigns"""
from fastapi import APIRouter, Depends, Query
import aiomysql

from api.database import get_mysql_pool
from api.auth import get_current_user

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("")
async def list_campaigns(
    active_only: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    user: dict = Depends(get_current_user),
):
    pool = await get_mysql_pool()
    where = "WHERE updated_at >= NOW() - INTERVAL 1 HOUR" if active_only else ""
    offset = (page - 1) * limit

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(f"SELECT COUNT(*) AS total FROM campaigns {where}")
            total = (await cur.fetchone())["total"]

            await cur.execute(
                f"SELECT c.*, i.country_name, i.country_iso "
                f"FROM campaigns c LEFT JOIN iocs i ON i.ip_address=c.src_ip "
                f"{where} ORDER BY c.updated_at DESC LIMIT %s OFFSET %s",
                (limit, offset)
            )
            rows = await cur.fetchall()

    return {"data": rows, "total": total, "page": page, "limit": limit}
