from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
import datetime
import redis
import json
import os

router = APIRouter(
    prefix="/api/canary",
    tags=["Canary Tokens"]
)

# Connect to Redis to send the alert into the DECEPTR pipeline
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_QUEUE = os.getenv("REDIS_QUEUE", "deceptr:events")

class CanaryTrigger(BaseModel):
    token_id: str
    source_ip: str | None = None
    user_agent: str | None = None

def trigger_canary_alert(token_id: str, ip: str, user_agent: str):
    """
    Push an event to Redis so the DECEPTR pipeline detects it.
    """
    event = {
        "eventid": "canary.triggered",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "src_ip": ip,
        "message": f"Honeytoken '{token_id}' was accessed outside the honeypot!",
        "system": "canary_webhook",
        "sensor": "deceptr-canary-api",
        "severity": "CRITICAL",
        "canary_token": token_id,
        "user_agent": user_agent
    }
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        r.lpush(REDIS_QUEUE, json.dumps(event))
    except Exception as e:
        print(f"[ERROR] Failed to push canary event to Redis: {e}")

@router.get("/trigger/{token_id}")
async def trigger_get(token_id: str, request: Request, background_tasks: BackgroundTasks):
    client_ip = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown")
    
    # Run pipeline notification in background
    background_tasks.add_task(trigger_canary_alert, token_id, client_ip, user_agent)
    
    return {"status": "ok", "message": "Canary acknowledged."}

@router.post("/trigger/{token_id}")
async def trigger_post(token_id: str, request: Request, background_tasks: BackgroundTasks):
    client_ip = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown")
    
    # Run pipeline notification in background
    background_tasks.add_task(trigger_canary_alert, token_id, client_ip, user_agent)
    
    return {"status": "ok", "message": "Canary acknowledged."}

@router.get("/assets/logo.png")
async def trigger_image_pixel(request: Request, background_tasks: BackgroundTasks):
    from fastapi.responses import Response
    
    client_ip = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown")
    
    # Token ID par defaut pour cette image piegee
    token_id = "sqldump_rh_logo"
    
    background_tasks.add_task(trigger_canary_alert, token_id, client_ip, user_agent)
    
    # Retourne un pixel transparent 1x1 PNG
    pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=pixel, media_type="image/png")
