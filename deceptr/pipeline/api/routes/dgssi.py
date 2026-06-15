"""
DECEPTR API — /api/dgssi/rapport
Genere le rapport d'incidents conforme a la Directive DGSSI n.001
(Direction Generale de la Securite des Systemes d'Information - Maroc)
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
import aiomysql

from api.database import get_mysql_pool
from api.auth import get_current_user

router = APIRouter(prefix="/api/dgssi", tags=["dgssi"])

GRAVITE_FR = {"CRITICAL": "CRITIQUE", "HIGH": "ELEVE", "MEDIUM": "MOYEN", "LOW": "FAIBLE"}

CATEGORIES_DGSSI = {
    "T1110": "1 - Acces non autorise",
    "T1078": "1 - Acces non autorise",
    "T1059": "5 - Intrusion / Execution",
    "T1505": "5 - Intrusion",
    "T1105": "2 - Logiciel malveillant",
    "T1021": "5 - Intrusion",
    "T1595": "4 - Collecte d'informations",
    "T1003": "6 - Fraude / Usurpation",
    "T1485": "2 - Logiciel malveillant",
    "T1082": "4 - Collecte d'informations",
}


@router.get("/rapport/json")
async def rapport_json(
    heures: int = Query(24, ge=1, le=720),
    org: str = "A completer",
    secteur: str = "Administration publique",
    rssi: str = "A completer",
    user: dict = Depends(get_current_user),
):
    """Rapport DGSSI au format JSON - pour integration CERT/MISP."""
    incidents, stats = await _build_report_data(heures)
    return {
        "rapport": {
            "version":      "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "plateforme":   "DECEPTR v1",
            "referentiel":  "Directive DGSSI n.001 - RMS Maroc",
            "periode_heures": heures,
            "organisation": {"nom": org, "secteur": secteur, "responsable": rssi},
            "statistiques": stats,
            "incidents":    incidents,
        }
    }


@router.get("/rapport", response_class=HTMLResponse)
async def rapport_html(
    heures: int = Query(24, ge=1, le=720),
    org: str = "A completer",
    secteur: str = "Administration publique",
    rssi: str = "A completer",
    user: dict = Depends(get_current_user),
):
    """Rapport DGSSI en HTML - pret a imprimer/exporter PDF."""
    incidents, stats = await _build_report_data(heures)
    html = _render_html(incidents, stats, org, secteur, rssi, heures)
    return HTMLResponse(content=html)


@router.get("/stats")
async def dgssi_stats(user: dict = Depends(get_current_user)):
    """Statistiques de conformite - tableau de bord DGSSI temps reel."""
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(severity='CRITICAL') AS critique,
                    SUM(severity='HIGH')     AS eleve,
                    SUM(severity='MEDIUM')   AS moyen,
                    SUM(severity='LOW')      AS faible,
                    COUNT(DISTINCT src_ip)   AS ips_uniques
                FROM alerts
                WHERE created_at >= NOW() - INTERVAL 7 DAY
            """)
            stats = await cur.fetchone()

            await cur.execute("""
                SELECT country_name, COUNT(*) AS count
                FROM alerts
                WHERE created_at >= NOW() - INTERVAL 7 DAY AND country_name IS NOT NULL
                GROUP BY country_name ORDER BY count DESC LIMIT 5
            """)
            top_pays = await cur.fetchall()

    return {
        "periode_heures":  168,
        "conformite":      "Directive DGSSI n.001",
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        **stats,
        "top_pays": top_pays,
    }


# Helpers ----------------------------------------------------------------------

async def _build_report_data(heures: int):
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(severity='CRITICAL') AS critique,
                    SUM(severity='HIGH')     AS eleve,
                    SUM(severity='MEDIUM')   AS moyen,
                    SUM(severity='LOW')      AS faible,
                    COUNT(DISTINCT src_ip)   AS ips_uniques
                FROM alerts WHERE created_at >= NOW() - INTERVAL %s HOUR
            """, (heures,))
            stats = await cur.fetchone()

            await cur.execute("""
                SELECT
                    src_ip,
                    GROUP_CONCAT(DISTINCT mitre_technique)   AS techniques,
                    GROUP_CONCAT(DISTINCT mitre_tech_name SEPARATOR ' | ') AS technique_names,
                    MAX(severity)     AS severity,
                    MAX(country_name) AS country_name,
                    MAX(country_iso)  AS country_iso,
                    MAX(abuse_score)  AS abuse_score,
                    MAX(vt_malicious) AS vt_malicious,
                    MAX(known_c2)     AS known_c2,
                    COUNT(*)          AS nb_events,
                    MIN(created_at)   AS first_seen,
                    MAX(created_at)   AS last_seen
                FROM alerts
                WHERE created_at >= NOW() - INTERVAL %s HOUR
                  AND severity IN ('HIGH','CRITICAL')
                GROUP BY src_ip
                ORDER BY nb_events DESC
                LIMIT 30
            """, (heures,))
            rows = await cur.fetchall()

    incidents = []
    for i, row in enumerate(rows, 1):
        techniques = (row["techniques"] or "").split(",")
        top_tech   = techniques[0] if techniques else "T1595"
        category   = CATEGORIES_DGSSI.get(top_tech, "4 - Collecte d'informations")
        sev        = row["severity"]
        ip_addr    = row["src_ip"]

        incidents.append({
            "reference":        "DGSSI-DECEPTR-" + datetime.now().strftime("%Y%m%d") + "-" + str(i).zfill(3),
            "date_detection":   row["first_seen"].isoformat() if row["first_seen"] else None,
            "date_notification":datetime.now(timezone.utc).isoformat(),
            "categorie_dgssi":  category,
            "niveau_gravite":   GRAVITE_FR.get(sev, "MOYEN"),
            "adresse_ip":       ip_addr,
            "pays_origine":     row["country_name"] or "Inconnu",
            "techniques_attck": row["technique_names"] or "",
            "nb_evenements":    row["nb_events"],
            "abuse_score":      row["abuse_score"],
            "vt_malicious":     row["vt_malicious"],
            "known_c2":         bool(row["known_c2"]),
            "impact": {
                "disponibilite":   "Non affecte - systeme leurre isole",
                "integrite":       "Non affecte - donnees fictives",
                "confidentialite": "Potentiellement affecte" if sev == "CRITICAL" else "Non affecte",
                "donnees_perso":   False,
            },
            "mesures_prises": [
                "Detection automatique par DECEPTR (Cyberdeception - Cowrie)",
                "Blocage recommande de l'IP " + ip_addr + " au pare-feu perimetrique",
                "Collecte et preservation des journaux d'incident (Elasticsearch)",
                "Enrichissement via VirusTotal, AbuseIPDB, Feodo Tracker",
                "Correlation MITRE ATT&CK effectuee automatiquement",
            ],
            "statut": "En cours d'investigation",
        })

    return incidents, stats


def _render_html(incidents, stats, org, secteur, rssi, heures):
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M") + " UTC"

    rows_html = ""
    for inc in incidents:
        sev = inc["niveau_gravite"]
        badge = {
            "CRITIQUE": "background:#C00000;color:#fff",
            "ELEVE":    "background:#ED7D31;color:#fff",
            "MOYEN":    "background:#FFD700;color:#333",
            "FAIBLE":   "background:#548235;color:#fff",
        }.get(sev, "")
        rows_html += (
            "<tr>"
            "<td><span style=\"" + badge + ";padding:2px 7px;font-size:10px;font-weight:700\">" + sev + "</span></td>"
            "<td style=\"font-size:11px\">" + inc["reference"] + "</td>"
            "<td>" + inc["categorie_dgssi"] + "</td>"
            "<td style=\"font-family:monospace;font-size:11px\">" + inc["adresse_ip"] + "</td>"
            "<td>" + inc["pays_origine"] + "</td>"
            "<td style=\"font-family:monospace;font-size:11px\">" + inc["techniques_attck"] + "</td>"
            "<td>" + str(inc["nb_evenements"]) + "</td>"
            "<td>" + inc["statut"] + "</td>"
            "</tr>"
        )

    total    = stats.get("total", 0) or 0
    critique = stats.get("critique", 0) or 0
    eleve    = stats.get("eleve", 0) or 0
    ips      = stats.get("ips_uniques", 0) or 0

    if incidents:
        table_html = (
            '<table class="inc">'
            '<tr><th>Gravite</th><th>Reference</th><th>Categorie DGSSI</th><th>IP Source</th>'
            '<th>Pays</th><th>ATT&CK</th><th>Evenements</th><th>Statut</th></tr>'
            + rows_html +
            '</table>'
        )
    else:
        table_html = "<p style='color:#888;font-style:italic'>Aucun incident HIGH/CRITICAL sur la periode.</p>"

    html = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"/>
<title>Rapport DGSSI - DECEPTR</title>
<style>
  body{font-family:Arial,sans-serif;font-size:13px;margin:0;background:#F0F4F8;color:#1a1a2e}
  .wrap{max-width:1100px;margin:0 auto;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.12)}
  .hdr{background:#1F4E79;color:#fff;padding:24px 36px}
  .hdr h1{font-size:20px;margin:0 0 4px}
  .hdr p{font-size:11px;opacity:.8;margin:0}
  .hdr-meta{display:flex;justify-content:space-between;align-items:flex-end;margin-top:14px}
  .hdr-meta .right{text-align:right;font-size:11px;opacity:.85;line-height:1.9}
  .hdr-title{margin-top:14px;padding-top:12px;border-top:2px solid #00B0F0;font-size:15px;font-weight:600;color:#BDD7EE}
  .section{padding:20px 36px;border-bottom:1px solid #E0E8F0}
  .section h2{font-size:12px;font-weight:700;color:#1F4E79;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #00B0F0;padding-left:10px;margin-bottom:14px}
  .cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
  .card{border:1px solid #d0dce8;border-radius:3px;padding:14px;text-align:center}
  .card .v{font-size:26px;font-weight:700;line-height:1}
  .card .l{font-size:10px;color:#666;text-transform:uppercase;margin-top:4px;letter-spacing:.06em}
  .card.red .v{color:#C00000}.card.amber .v{color:#ED7D31}.card.blue .v{color:#2E75B6}.card.green .v{color:#375623}
  .org-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px}
  .org-row{display:flex;gap:8px}
  .org-lbl{color:#5a7196;min-width:150px;font-weight:600}
  table.inc{width:100%;border-collapse:collapse;font-size:12px}
  table.inc th{background:#1F4E79;color:#fff;padding:7px 10px;text-align:left;font-size:11px;letter-spacing:.06em}
  table.inc td{padding:7px 10px;border-bottom:1px solid #eef}
  table.inc tr:hover td{background:#F2F7FF}
  .footer{padding:14px 36px;background:#1F4E79;color:#aac;font-size:10px;display:flex;justify-content:space-between}
  @media print{body{background:#fff}.wrap{box-shadow:none}}
</style>
</head>
<body>
<div class="wrap">

<div class="hdr">
  <div class="hdr-meta">
    <div>
      <h1>Rapport DGSSI - Incidents de Cybersecurite</h1>
      <p>Direction Generale de la Securite des Systemes d'Information - Royaume du Maroc</p>
    </div>
    <div class="right">
      <div>Genere le : <b>__NOW__</b></div>
      <div>Outil : DECEPTR v1 - Cyberdeception (Cowrie)</div>
      <div>Referentiel : Directive DGSSI n.001 / RMS Maroc</div>
      <div>Periode : __HEURES__ dernieres heures</div>
    </div>
  </div>
  <div class="hdr-title">__NB_INC__ incident(s) HIGH/CRITICAL - __TOTAL__ evenements totaux</div>
</div>

<div class="section">
  <h2>Informations Organisation</h2>
  <div class="org-grid">
    <div class="org-row"><span class="org-lbl">Organisation :</span><span>__ORG__</span></div>
    <div class="org-row"><span class="org-lbl">Secteur :</span><span>__SECTEUR__</span></div>
    <div class="org-row"><span class="org-lbl">Responsable securite :</span><span>__RSSI__</span></div>
    <div class="org-row"><span class="org-lbl">Outil de detection :</span><span>DECEPTR - Cowrie (T-Pot)</span></div>
  </div>
</div>

<div class="section">
  <h2>Synthese</h2>
  <div class="cards">
    <div class="card red"><div class="v">__CRIT__</div><div class="l">Critique</div></div>
    <div class="card amber"><div class="v">__ELEVE__</div><div class="l">Eleve</div></div>
    <div class="card blue"><div class="v">__IPS__</div><div class="l">IPs Malveillantes</div></div>
    <div class="card green"><div class="v">__TOTAL__</div><div class="l">Evenements Total</div></div>
  </div>
</div>

<div class="section">
  <h2>Tableau des Incidents</h2>
  __TABLE__
</div>

<div class="section">
  <h2>Recommandations</h2>
  <table style="width:100%;border-collapse:collapse;font-size:12px">
    <tr style="background:#EBF3FB"><th style="padding:8px;text-align:left;width:200px">Priorite</th><th style="padding:8px;text-align:left">Action recommandee</th></tr>
    <tr><td style="padding:7px;border-bottom:1px solid #eef;font-weight:600;color:#C00000">Immediat</td><td style="padding:7px;border-bottom:1px solid #eef">Bloquer les IP CRITIQUE au pare-feu perimetrique</td></tr>
    <tr><td style="padding:7px;border-bottom:1px solid #eef;font-weight:600;color:#ED7D31">48 heures</td><td style="padding:7px;border-bottom:1px solid #eef">Transmettre les IoCs au CERT-MA</td></tr>
    <tr><td style="padding:7px;border-bottom:1px solid #eef;font-weight:600;color:#2E75B6">1 semaine</td><td style="padding:7px;border-bottom:1px solid #eef">Mettre a jour les regles de detection selon les TTPs observes</td></tr>
    <tr><td style="padding:7px;font-weight:600;color:#375623">Long terme</td><td style="padding:7px">Etendre la couverture de cyberdeception (multi-honeypots)</td></tr>
  </table>
  <p style="margin-top:12px;font-size:11px;color:#888">Conformement a la Directive DGSSI n.001, ce rapport doit etre conserve pendant <b>5 ans</b>.</p>
</div>

<div class="footer">
  <span>DECEPTR v1 - Conforme Directive DGSSI n.001 - ISMAGI Rabat</span>
  <span>Chambre des Representants du Maroc - 2025/2026</span>
</div>

</div>
</body>
</html>"""

    html = html.replace("__NOW__", now)
    html = html.replace("__HEURES__", str(heures))
    html = html.replace("__NB_INC__", str(len(incidents)))
    html = html.replace("__TOTAL__", str(total))
    html = html.replace("__ORG__", org)
    html = html.replace("__SECTEUR__", secteur)
    html = html.replace("__RSSI__", rssi)
    html = html.replace("__CRIT__", str(critique))
    html = html.replace("__ELEVE__", str(eleve))
    html = html.replace("__IPS__", str(ips))
    html = html.replace("__TABLE__", table_html)

    return html
