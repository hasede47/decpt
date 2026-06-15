"""
DECEPTR API v1 — FastAPI
Expose les alertes, IoCs, attaquants, campagnes et le rapport DGSSI.

Lancement : uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
Documentation : http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import auth, alerts, iocs, attackers, campaigns, dgssi, canary

app = FastAPI(
    title="DECEPTR API",
    description="Plateforme de Cyberdeception - Chambre des Representants du Maroc",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(alerts.router)
app.include_router(iocs.router)
app.include_router(attackers.router)
app.include_router(campaigns.router)
app.include_router(dgssi.router)
app.include_router(canary.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "platform": "DECEPTR"}


@app.get("/")
async def root():
    return {
        "name": "DECEPTR API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth":      "/api/auth/login",
            "alerts":    "/api/alerts",
            "iocs":      "/api/iocs",
            "attackers": "/api/attackers",
            "campaigns": "/api/campaigns",
            "dgssi":     "/api/dgssi/rapport",
            "canary":    "/api/canary/trigger",
        }
    }
