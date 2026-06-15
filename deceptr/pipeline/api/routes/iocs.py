"""DECEPTR API — /api/iocs"""
from fastapi import APIRouter, Depends, Query
import aiomysql

from api.database import get_mysql_pool
from api.auth import get_current_user

router = APIRouter(prefix="/api/iocs", tags=["iocs"])


@router.get("")
async def list_iocs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
    min_abuse: int = 0,
    known_c2: bool | None = None,
    user: dict = Depends(get_current_user),
):
    pool = await get_mysql_pool()
    where = ["1=1"]
    params: list = []

    if min_abuse > 0:
        where.append("abuse_score >= %s")
        params.append(min_abuse)
    if known_c2 is not None:
        where.append("known_c2 = %s")
        params.append(int(known_c2))

    where_sql = " AND ".join(where)
    offset = (page - 1) * limit

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(f"SELECT COUNT(*) AS total FROM iocs WHERE {where_sql}", params)
            total = (await cur.fetchone())["total"]
            await cur.execute(
                f"SELECT * FROM iocs WHERE {where_sql} "
                f"ORDER BY max_risk_score DESC, last_seen DESC LIMIT %s OFFSET %s",
                params + [limit, offset]
            )
            rows = await cur.fetchall()

    return {"data": rows, "total": total, "page": page, "limit": limit}


@router.get("/{ip}")
async def get_ioc(ip: str, user: dict = Depends(get_current_user)):
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM iocs WHERE ip_address=%s", (ip,))
            ioc = await cur.fetchone()

            await cur.execute(
                "SELECT * FROM attackers WHERE ip_address=%s", (ip,)
            )
            attacker = await cur.fetchone()

            await cur.execute(
                "SELECT rule_name, title, severity, mitre_technique, created_at "
                "FROM alerts WHERE src_ip=%s ORDER BY created_at DESC LIMIT 20",
                (ip,)
            )
            alerts = await cur.fetchall()

    if not ioc:
        return {"error": "IP non trouvée"}

    return {"ioc": ioc, "attacker_profile": attacker, "recent_alerts": alerts}
