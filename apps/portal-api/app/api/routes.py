import json
import os
import httpx

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.integrations.grafana import build_embed_url
from app.schemas.dashboard import DashboardCreate, DashboardRead, LayoutRead, LayoutUpdate
from app.services.dashboard_service import (
    create_dashboard,
    delete_dashboard,
    get_layout,
    list_dashboards,
    upsert_layout,
)

router = APIRouter()
SENTINEL_API_URL = os.getenv("SENTINEL_API_URL", "http://sentinel-engine:8000")


def _normalize_stats(stats_payload, incidents_payload):
    if not isinstance(stats_payload, dict):
        stats_payload = {}
    if not isinstance(incidents_payload, list):
        incidents_payload = []

    # Supports both teammate schema and legacy dashboard schema.
    total_alerts = stats_payload.get("total_alerts", stats_payload.get("total", 0))
    total_lines = stats_payload.get("total_lines", total_alerts)
    active_incidents = stats_payload.get("active_incidents", stats_payload.get("incident_count", len(incidents_payload)))

    top_incidents = stats_payload.get("top_incidents")
    if not isinstance(top_incidents, list):
        top_incidents = [
            {
                "source_ip": i.get("ip", "unknown"),
                "category": (i.get("types") or ["Unknown"])[0],
                "path": "-",
                "count": i.get("alert_count", 0),
            }
            for i in incidents_payload[:5]
        ]

    return {
        "total_lines": total_lines,
        "total_alerts": total_alerts,
        "active_incidents": active_incidents,
        "top_incidents": top_incidents,
    }


def _normalize_alerts(alerts_payload):
    # Handles both list response and {items:[...]} response variants.
    if isinstance(alerts_payload, dict):
        items = alerts_payload.get("items", [])
    elif isinstance(alerts_payload, list):
        items = alerts_payload
    else:
        items = []

    out = []
    for a in items[:10]:
        out.append({
            "category": a.get("category", a.get("type", "Unknown")),
            "severity": a.get("severity", "INFO"),
            "path": a.get("path", "-"),
            "source_ip": a.get("source_ip", a.get("ip", "-")),
        })
    return out

@router.get("/health")
def health():
    return {"status": "ok", "service": "portal-api"}

@router.get("/api/summary")
async def summary():
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            stats = await client.get(f"{SENTINEL_API_URL}/api/stats")
            alerts = await client.get(f"{SENTINEL_API_URL}/api/alerts")
            incidents = await client.get(f"{SENTINEL_API_URL}/api/incidents")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"sentinel unavailable: {exc}")

    stats_payload = stats.json()
    alerts_payload = alerts.json()
    incidents_payload = incidents.json()

    return {
        "stats": _normalize_stats(stats_payload, incidents_payload),
        "recent_alerts": _normalize_alerts(alerts_payload),
    }

@router.get("/api/dashboards", response_model=list[DashboardRead])
def dashboards(db: Session = Depends(get_db)):
    return list_dashboards(db)

@router.post("/api/dashboards", response_model=DashboardRead)
def add_dashboard(payload: DashboardCreate, db: Session = Depends(get_db)):
    return create_dashboard(db, payload)

@router.delete("/api/dashboards/{dashboard_id}")
def remove_dashboard(dashboard_id: int, db: Session = Depends(get_db)):
    ok = delete_dashboard(db, dashboard_id)
    if not ok:
        raise HTTPException(status_code=404, detail="dashboard not found")
    return {"deleted": True}

@router.get("/api/layouts/{page_name}")
def read_layout(page_name: str, db: Session = Depends(get_db)):
    item = get_layout(db, page_name)
    if not item:
        return {"page_name": page_name, "layout_json": {"widgets": []}}
    return {"page_name": item.page_name, "layout_json": json.loads(item.layout_json)}

@router.put("/api/layouts/{page_name}")
def write_layout(page_name: str, payload: LayoutUpdate, db: Session = Depends(get_db)):
    item = upsert_layout(db, page_name, json.dumps(payload.layout_json))
    return {"page_name": item.page_name, "layout_json": json.loads(item.layout_json)}

@router.get("/api/embed-preview")
def embed_preview(grafana_uid: str, panel_id: str | None = None):
    return {"embed_url": build_embed_url(grafana_uid, panel_id)}