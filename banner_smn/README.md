# SMN TiePre Banner API

Mini API con FastAPI que:
1) descarga el TXT `tiepreYYYYMMDD.txt` del SMN (por fecha, hoy por defecto),
2) cachea en `data/`,
3) parsea a JSON,
4) expone endpoints para filtrar por localidades y un overlay HTML simple.

## Estructura
```
weather_smn/
├─ app/
│  ├─ main.py
│  ├─ utils.py
│  ├─ constants.py
│  └─ __init__.py
├─ static/
│  ├─ overlay.html
│  └─ smn-overlay.css
├─ data/               # cache local
├─ requirements.txt
└─ README.md
```

## Uso
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Endpoints
- `GET /api/tiepre/download?date=YYYYMMDD&force=false`
- `GET /api/tiepre/parse?date=YYYYMMDD&force=false`
- `GET /api/tiepre?date=YYYYMMDD`
- `GET /api/cities?date=YYYYMMDD`
- `GET /api/weather?cities=Capital%20Federal,La%20Plata&date=YYYYMMDD`

### Overlay
Abrí en OBS (Browser Source):
```
http://localhost:8000/overlay?cities=Capital%20Federal,La%20Plata&scale=1
```

> Fecha por defecto: hoy (timezone America/Argentina/Buenos_Aires). Usa `YYYYMMDD` para fechas históricas.
