# -*- coding: utf-8 -*-
import csv
import io
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Iterable
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .constants import today_str, map_city

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PARSED_DIR = DATA_DIR / "parsed"
for d in (RAW_DIR, PARSED_DIR):
    d.mkdir(parents=True, exist_ok=True)

BASE_PATH = "observaciones/tiepre{date}.txt"
BASE_URLS = [
    "https://ssl.smn.gob.ar/dpd/descarga_opendata.php?file={path}",
    "http://ssl.smn.gob.ar/dpd/descarga_opendata.php?file={path}",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Compat) SMN-Overlay/1.2",
    "Accept": "text/plain,*/*",
    "Referer": "https://www.smn.gob.ar/",
}

EXPECTED_HEADER = [
    "estacion","fecha","hora","estado","visibilidad",
    "temperatura","sensacion","humedad","viento","presion"
]

def _requests_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=4, backoff_factor=0.6,
        status_forcelist=(403, 408, 429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"])
    )
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s

def target_date_str(date: Optional[str]) -> str:
    if not date:
        return today_str()
    if not re.fullmatch(r"\d{8}", date):
        raise ValueError("Formato de fecha inválido, usa YYYYMMDD")
    return date

def fetch_tiepre(date: Optional[str] = None, force: bool = False) -> Path:
    ds = target_date_str(date)
    raw_path = RAW_DIR / f"tiepre{ds}.txt"
    if raw_path.exists() and not force:
        return raw_path

    path = BASE_PATH.format(date=ds)
    sess = _requests_session()
    last_err = None
    for base in BASE_URLS:
        url = base.format(path=path)
        try:
            r = sess.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            content = r.content
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")
            raw_path.write_text(text, encoding="utf-8")
            return raw_path
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"No se pudo descargar {path}: {last_err}")

def _best_delimiter(lines: List[str]) -> Optional[str]:
    sample = [ln for ln in lines[:20] if ln.strip()]
    semis = sum(ln.count(";") for ln in sample)
    commas = sum(ln.count(",") for ln in sample)
    if semis >= max(commas, 4):
        return ";"
    if commas >= 6:
        return ","
    return None

def _split_line(line: str, delim: Optional[str]) -> List[str]:
    line = line.strip()
    if not line:
        return []
    if delim:
        return [c.strip() for c in line.split(delim)]
    parts = re.split(r"\s{2,}|\t+", line)
    return [p.strip() for p in parts if p.strip()]

def _looks_like_header(tokens: List[str]) -> bool:
    if not tokens:
        return False
    cols = " ".join(t.lower() for t in tokens)
    keywords = ("estacion","estación","provincia","fecha","hora",
                "temperatura","humedad","presion","presión","viento",
                "visibilidad","estado","sensacion","sensación")
    kw_hits = sum(1 for k in keywords if k in cols)
    digit_hits = sum(1 for t in tokens if re.search(r"\d", t))
    return kw_hits >= 3 and digit_hits <= max(1, len(tokens)//4)

def _to_float(x: str) -> Optional[float]:
    try:
        return float(str(x).replace(",", ".").strip())
    except Exception:
        return None

def parse_tiepre_to_json(date: Optional[str] = None, force: bool = False) -> Path:
    ds = target_date_str(date)
    parsed_path = PARSED_DIR / f"tiepre{ds}.json"
    if parsed_path.exists() and not force:
        return parsed_path

    raw_path = fetch_tiepre(ds)
    text = raw_path.read_text(encoding="utf-8", errors="ignore").strip()
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise RuntimeError("El archivo descargado está vacío")

    delim = _best_delimiter(lines)
    first_tokens = _split_line(lines[0], delim)
    has_header = _looks_like_header(first_tokens)

    data_rows: List[List[str]] = []
    for ln in (lines[1:] if has_header else lines):
        tokens = _split_line(ln, delim)
        if tokens:
            data_rows.append(tokens)

    records: List[Dict] = []
    for toks in data_rows:
        rec = {
            "estacion": "",
            "fecha": "",
            "hora": "",
            "estado": "",
            "visibilidad": "",
            "temperatura": None,
            "sensacion": None,
            "humedad": None,
            "viento": "",
            "presion": None,
        }
        if len(toks) >= 10:
            v = toks[:10]
            rec.update({
                "estacion": v[0], "fecha": v[1], "hora": v[2], "estado": v[3],
                "visibilidad": v[4], "temperatura": _to_float(v[5]), "sensacion": _to_float(v[6]),
                "humedad": int(_to_float(v[7]) or 0) if v[7] else None, "viento": v[8], "presion": _to_float(v[9]),
            })
        else:
            rec["estacion"] = toks[0]
            for t in toks:
                if re.fullmatch(r"\d{1,2}:\d{2}", t):
                    rec["hora"] = t; break
            floats = [f for f in (_to_float(t) for t in toks) if f is not None]
            if floats: rec["temperatura"] = floats[0]
            for t in toks:
                if " km" in t.lower():
                    rec["visibilidad"] = t; break
        records.append(rec)

    # normalización
    norm = []
    for r in records:
        rr = dict(r)
        for k in ("estacion","provincia","estado","viento","visibilidad","fecha","hora"):
            if k in rr and isinstance(rr[k], str):
                rr[k] = re.sub(r"\s+", " ", rr[k]).strip()
        norm.append(rr)

    parsed_path.write_text(json.dumps(norm, ensure_ascii=False, indent=2), encoding="utf-8")
    return parsed_path

# ---------- selección estricta por ciudad ----------
import unicodedata as _ud

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = _ud.normalize("NFKD", s)
    s = "".join(ch for ch in s if not _ud.combining(ch))
    return s

def _matches_station_exact(name: str, targets: List[str]) -> bool:
    nn = _norm(name)
    for t in targets:
        nt = _norm(map_city(t))
        if nn == nt:
            return True
    return False

def load_parsed(date: Optional[str] = None):
    path = parse_tiepre_to_json(date)
    return json.loads(path.read_text(encoding="utf-8"))

def filter_by_cities(records, cities: List[str]):
    out = []
    for r in records:
        name = r.get("estacion") or r.get("nombre") or r.get("ciudad") or ""
        if _matches_station_exact(name, list(cities)):
            out.append({
                "ciudad": name,
                "provincia": r.get("provincia", ""),
                "temperatura": r.get("temperatura"),
                "humedad": r.get("humedad"),
                "estado": r.get("estado"),
                "hora": r.get("hora"),
            })
    return out

def unique_cities(records):
    names, seen = [], set()
    for r in records:
        name = r.get("estacion") or r.get("nombre") or r.get("ciudad")
        if name and name not in seen:
            names.append(name); seen.add(name)
    return names

# ---------- NUEVO: verificación/refresh horario del TXT y del JSON ----------
def _minutes_old(path: Path) -> float:
    try:
        return (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).total_seconds() / 60.0
    except FileNotFoundError:
        return 1e9  # muy viejo / no existe

def _download_tiepre_text(ds: str) -> str:
    """Descarga el texto del día a memoria (sin escribir)."""
    sess = _requests_session()
    path = BASE_PATH.format(date=ds)
    last_err = None
    for base in BASE_URLS:
        url = base.format(path=path)
        try:
            r = sess.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            try:
                return r.content.decode("utf-8")
            except UnicodeDecodeError:
                return r.content.decode("latin-1")
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"No se pudo descargar {path}: {last_err}")

def ensure_tiepre_fresh(date: Optional[str] = None, ttl_minutes: int = 55) -> Path:
    """
    Garantiza que el TXT del día exista y no sea más viejo que ttl_minutes.
    Si está viejo o cambió el contenido, actualiza el archivo local.
    """
    ds = target_date_str(date)
    raw_path = RAW_DIR / f"tiepre{ds}.txt"

    need_refresh = (not raw_path.exists()) or (_minutes_old(raw_path) > ttl_minutes)
    if need_refresh:
        new_text = _download_tiepre_text(ds)
        old_text = ""
        if raw_path.exists():
            try:
                old_text = raw_path.read_text(encoding="utf-8")
            except Exception:
                old_text = raw_path.read_text(errors="ignore")
        if new_text != old_text:
            raw_path.write_text(new_text, encoding="utf-8")
    return raw_path

def ensure_parsed_current(date: Optional[str] = None) -> Path:
    """
    Asegura que el JSON esté al día respecto al TXT. Re-parsea si es necesario.
    """
    ds = target_date_str(date)
    raw_path = ensure_tiepre_fresh(ds)
    parsed_path = PARSED_DIR / f"tiepre{ds}.json"
    if (not parsed_path.exists()) or (parsed_path.stat().st_mtime < raw_path.stat().st_mtime):
        parse_tiepre_to_json(ds, force=True)
    return parsed_path
