"""DECEPTR API — /api/auth"""
from fastapi import APIRouter, HTTPException, Depends
import aiomysql

from api.database import get_mysql_pool
from api.auth import verify_password, create_access_token, get_current_user
from api.models.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username=%s AND active=1",
                (req.username,)
            )
            user = await cur.fetchone()

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET last_login=NOW() WHERE id=%s", (user["id"],))

    token = create_access_token(user["username"], user["role"])
    return TokenResponse(access_token=token, username=user["username"], role=user["role"])


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user
