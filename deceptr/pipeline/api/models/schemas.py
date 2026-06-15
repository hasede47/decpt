"""
DECEPTR API — Schémas Pydantic
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    username:     str
    role:         str


class AlertOut(BaseModel):
    id:              Optional[int] = None
    event_id:        str
    src_ip:          str
    rule_name:       str
    title:           str
    detail:          Optional[str] = None
    severity:        str
    event_type:      Optional[str] = None
    mitre_technique: Optional[str] = None
    mitre_tactic:    Optional[str] = None
    mitre_tech_name: Optional[str] = None
    risk_score:      int = 0
    country_iso:     Optional[str] = None
    country_name:    Optional[str] = None
    abuse_score:     int = 0
    vt_malicious:    int = 0
    known_c2:        bool = False
    acknowledged:    bool = False
    timestamp:       Optional[str] = None


class AcknowledgeRequest(BaseModel):
    notes: Optional[str] = None


class IoCOut(BaseModel):
    ip_address:      str
    country_iso:     Optional[str] = None
    country_name:    Optional[str] = None
    city:            Optional[str] = None
    abuse_score:     int = 0
    vt_malicious:    int = 0
    known_c2:        bool = False
    mitre_technique: Optional[str] = None
    max_severity:    str = "LOW"
    max_risk_score:  int = 0
    hit_count:       int = 0
    first_seen:      Optional[str] = None
    last_seen:       Optional[str] = None


class CampaignOut(BaseModel):
    src_ip:       str
    techniques:   Optional[str] = None
    event_count:  int = 0
    max_severity: str = "LOW"
    started_at:   Optional[str] = None
    updated_at:   Optional[str] = None


class DashboardStats(BaseModel):
    total_alerts:     int = 0
    alerts_24h:       int = 0
    total_critical:   int = 0
    total_high:       int = 0
    total_iocs:       int = 0
    total_c2:         int = 0
    total_attackers:  int = 0
    active_campaigns: int = 0
