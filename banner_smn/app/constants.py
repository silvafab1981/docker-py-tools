# -*- coding: utf-8 -*-
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Argentina/Buenos_Aires")

def normalize(s: str) -> str:
    return (s or "").strip().lower()

# Alias de entrada -> nombre SMN exacto
CITY_ALIASES = {
    "caba": "Buenos Aires",
    "capital federal": "Buenos Aires",
    "ciudad autonoma de buenos aires": "Buenos Aires",
    "ciudad autónoma de buenos aires": "Buenos Aires",
}

def map_city(name: str) -> str:
    n = normalize(name)
    return CITY_ALIASES.get(n, name)

# Etiquetas visuales (si existe, se muestra SOLO la etiqueta)
DEFAULT_LABELS = {
    "La Plata": "Prov. Bs.As.",
    "Buenos Aires": "CABA",
    "Resistencia": "Chaco",
    "Trelew": "Chubut",
    "Córdoba": "Córdoba",
    "Corrientes": "Corrientes",
    "Paraná": "Entre Ríos",
    "Formosa": "Formosa",
    "Jujuy": "Jujuy",
    "Santa Rosa": "La Pampa",
    "La Rioja": "La Rioja",
    "Mendoza": "Mendoza",
    "Posadas": "Misiones",
    "Neuquén": "Neuquén",
    "Viedma": "Río Negro",
    "Salta": "Salta",
    "San Juan": "San Juan",
    "San Luis": "San Luis",
    "Río Gallegos": "Santa Cruz",
    "Santa Fe": "Santa Fe",
    "Santiago del Estero": "S. del Estero",
    "Ushuaia": "T. del Fuego",
    "Tucumán": "Tucumán",
    "Base Marambio": "Antártida",
    "Catamarca": "Catamarca",
}

# Lista fija para el overlay (orden de rotación)
FIXED_CITIES = [
    "Buenos Aires","La Plata","Catamarca","Resistencia","Trelew","Córdoba","Corrientes","Paraná","Formosa","Jujuy",
    "Santa Rosa","La Rioja","Mendoza","Posadas","Neuquén","Viedma","Salta","San Juan","San Luis","Río Gallegos",
    "Santa Fe","Santiago del Estero","Ushuaia","Tucumán","Base Marambio"
]

# Rotación: tiempo entre tarjetas (segundos)
CYCLE_SECONDS = 5

# Cada cuántas temperaturas meter una tarjeta "VIVO"
LIVE_EVERY = 5

# Compat: defaults si llaman /api/weather sin cities
CAPITALES_AR = list(DEFAULT_LABELS.keys())

def today_str() -> str:
    return datetime.now(TZ).strftime("%Y%m%d")
