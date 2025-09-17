# -*- coding: utf-8 -*-
from pathlib import Path
from typing import List, Optional
# --- Health / Liveness ---
import time

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .utils import (
    fetch_tiepre, parse_tiepre_to_json, load_parsed, filter_by_cities, unique_cities,
    ensure_parsed_current,   # <-- NUEVO
)
from .constants import CAPITALES_AR, today_str, FIXED_CITIES, DEFAULT_LABELS, CYCLE_SECONDS, LIVE_EVERY

BASE_DIR = Path(__file__).resolve().parents[1]
START_TS = time.time()

app = FastAPI(title="SMN TiePre Overlay API", version="1.6")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/api/tiepre/download")
def api_download(date: Optional[str] = None, force: bool = False):
    try:
        path = fetch_tiepre(date, force=force)
        return {"ok": True, "file": str(path), "date": date or today_str()}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.get("/api/tiepre/parse")
def api_parse(date: Optional[str] = None, force: bool = False):
    try:
        path = parse_tiepre_to_json(date, force=force)
        return {"ok": True, "file": str(path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tiepre")
def api_tiepre(date: Optional[str] = None):
    try:
        ensure_parsed_current(date)  # <-- verifica/actualiza
        return JSONResponse(load_parsed(date))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cities")
def api_cities(date: Optional[str] = None):
    try:
        ensure_parsed_current(date)  # <-- verifica/actualiza
        return {"date": date or today_str(), "cities": unique_cities(load_parsed(date))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weather")
def api_weather(
    cities: List[str] = Query(default=None, description="Lista de ciudades (?cities=A&cities=B) o una sola string separada por comas"),
    date: Optional[str] = None
):
    try:
        ensure_parsed_current(date)  # <-- verifica/actualiza

        if not cities:
            from .constants import CAPITALES_AR as DEFAULTS
            cities = DEFAULTS
        norm_list: List[str] = []
        for c in cities:
            norm_list.extend([s.strip() for s in str(c).split(",") if s.strip()])

        data = filter_by_cities(load_parsed(date), norm_list)
        return {"date": date or today_str(), "items": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Config del overlay para el front
@app.get("/api/overlay/config")
def api_overlay_config():
    return {"cities": FIXED_CITIES, "labels": DEFAULT_LABELS, "cycle": CYCLE_SECONDS, "live_every": LIVE_EVERY}

# Sirve el overlay fijo sin parámetros
@app.get("/overlay.html")
def overlay_html():
    html_path = BASE_DIR / "static" / "overlay.html"
    return FileResponse(html_path)

app.get("/health", include_in_schema=False)
@app.head("/health", include_in_schema=False)
def health():
    return {"status": "ok", "uptime": round(time.time() - START_TS, 1)}

# (Opcional) Readiness real: verifica/actualiza el dataset del día
from .utils import ensure_parsed_current
from fastapi.responses import JSONResponse

@app.get("/ready", include_in_schema=False)
def ready():
    try:
        ensure_parsed_current(None)
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=503)
    

@app.get("/banner.html")
def banner_html():
    return FileResponse(BASE_DIR / "static" / "banner.html")