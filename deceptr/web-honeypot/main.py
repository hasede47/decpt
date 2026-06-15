import os
import json
import uuid
import datetime
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import redis

app = FastAPI(title="Web Honeypot - VPN Portal")

# Setup templates
templates = Jinja2Templates(directory="templates")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "deceptr-redis-2026")
REDIS_QUEUE = os.getenv("REDIS_QUEUE", "deceptr:events")

def send_to_redis(ip: str, username: str, password: str, user_agent: str):
    """Send captured credentials to DECEPTR pipeline via Redis."""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        event = {
            "eventid": "web.login.attempt",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "src_ip": ip,
            "username": username,
            "password": password,
            "user_agent": user_agent,
            "system": "web_honeypot",
            "sensor": "deceptr-web",
            "message": f"Login attempt on VPN portal with user {username}"
        }
        r.lpush(REDIS_QUEUE, json.dumps(event))
        print(f"[!] Captured VPN login: {username} from {ip}")
    except Exception as e:
        print(f"[ERROR] Failed to connect to Redis: {e}")

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "error": False})

@app.post("/", response_class=HTMLResponse)
async def login_submit(
    request: Request, 
    background_tasks: BackgroundTasks,
    username: str = Form(""), 
    password: str = Form("")
):
    ip = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown")
    
    if username or password:
        # Send credentials asynchronously to the pipeline
        background_tasks.add_task(send_to_redis, ip, username, password, user_agent)
    
    # Always simulate a failed login to keep them guessing
    return templates.TemplateResponse("index.html", {"request": request, "error": True})
