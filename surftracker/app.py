import base64
import uuid
import io
import json
import os
from datetime import datetime, date

import numpy as np
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, Dict, Any, Tuple

# ===================== CONFIG =====================
TZ = "Atlantic/Canary"
ACTUALIZACION_MIN = 10
ACTUALIZACION_MS = ACTUALIZACION_MIN * 60 * 1000
OBS_FILE = "observaciones.csv"

st.set_page_config(
    page_title="Surf Tracker",
    layout="wide",
    initial_sidebar_state="collapsed",
)
is_mobile = st.query_params.get("mobile","0") == "1"
# ===================== AUTO-REFRESH =====================
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=ACTUALIZACION_MS, key="auto_refresh_10min")
except Exception:
    components.html(
        f"<script>setTimeout(function(){{window.parent.location.reload()}}, {ACTUALIZACION_MS});</script>",
        height=0,
        width=0,
    )

# ===================== THEME / CSS =====================
APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;800;900&display=swap');

:root{
  --bg: #0e1117;
  --panel: #0b0f15;
  --card: #161b22;
  --card2:#121821;
  --ink: rgba(255,255,255,.92);
  --muted: rgba(255,255,255,.60);
  --line: rgba(255,255,255,.10);
  --line2: rgba(255,255,255,.07);
  --good: #2ecc71;
  --warn: #f1c40f;
  --bad:  #e74c3c;
  --blue: #2b7cff;
}

html, body, [data-testid="stAppViewContainer"]{
  background:
    radial-gradient(900px 520px at 15% 12%, rgba(43,124,255,.16), transparent 60%),
    radial-gradient(900px 520px at 85% 18%, rgba(0,178,255,.10), transparent 60%),
    radial-gradient(900px 520px at 60% 90%, rgba(46,204,113,.06), transparent 60%),
    var(--bg) !important;
  font-family: "Plus Jakarta Sans", ui-sans-serif, system-ui, -apple-system !important;
  color: var(--ink) !important;
}

[data-testid="stHeader"]{ background: transparent !important; }
[data-testid="stSidebar"]{
  background: var(--panel) !important;
  border-right: 1px solid var(--line2);
}

h1, h2, h3, h4 { color: var(--ink) !important; letter-spacing: -0.02em; }
.smallmuted { color: var(--muted); font-size: 12px; }
.center { text-align: center; }

.badge{
  display:inline-block;
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 900;
  font-size: 12px;
  color: #0b0f15;
}

.pill{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding: 8px 12px;
  border: 1px solid var(--line2);
  background: rgba(255,255,255,.04);
  border-radius: 999px;
  font-weight: 800;
  font-size: 12px;
  color: var(--ink);
}

.kpi{
  font-size: 30px;
  font-weight: 950;
  letter-spacing: -0.03em;
}
.subkpi{
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.card{
  border: 1px solid var(--line2);
  background: linear-gradient(180deg, rgba(255,255,255,.05), transparent 32%), var(--card);
  border-radius: 20px;
  padding: 16px;
  box-shadow: 0 12px 30px rgba(0,0,0,.25);
  min-height: 265px;
}
.card:hover{
  border-color: rgba(255,255,255,.14);
  background: linear-gradient(180deg, rgba(255,255,255,.07), transparent 32%), var(--card2);
}

.tablewrap{
  border: 1px solid var(--line2);
  background: linear-gradient(180deg, rgba(255,255,255,.04), transparent 35%), var(--card);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 12px 30px rgba(0,0,0,.25);
}

table{
  width:100%;
  border-collapse: collapse;
  table-layout: fixed;
}

th, td{
  padding: 12px 10px;
  border-bottom: 1px solid rgba(255,255,255,.06);
  text-align: center;
  color: var(--ink);
  vertical-align: middle;
  word-wrap: break-word;
}

thead th{
  font-weight: 900;
  background: rgba(43,124,255,.12);
}

.rowtitle{ font-weight: 900; }

.scorebubble{
  width: 54px;
  height: 54px;
  border-radius: 999px;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  font-weight: 950;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.10);
}

.goodbg{ background: rgba(46,204,113,.12); }
.warnbg{ background: rgba(241,196,15,.12); }
.badbg { background: rgba(231,76,60,.12); }

.section-card{
  border: 1px solid var(--line2);
  background: linear-gradient(180deg, rgba(255,255,255,.04), transparent 35%), var(--card);
  border-radius: 20px;
  padding: 16px;
}

.tabbar-note{
  color: var(--muted);
  text-align:center;
  font-size:12px;
  margin-top:-4px;
}

.dirblock{
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:2px;
  line-height:1.15;
}

.dirarrow{
  font-size:22px;
  font-weight:900;
}

.dirdeg{
  font-size:14px;
  font-weight:900;
}

.dircompass{
  font-size:12px;
  color: var(--muted);
  font-weight:800;
}

@media (max-width: 1100px){
  th, td{ padding: 10px 6px; font-size: 12px; }
  .scorebubble{ width: 44px; height: 44px; }
  .kpi{ font-size: 26px; }
  .pill{ font-size: 11px; padding: 6px 10px; }
  .dirarrow{ font-size:18px; }
}
@media (max-width: 768px){
  .card{
    min-height: auto !important;
    padding: 12px !important;
    border-radius: 16px !important;
  }

  .kpi{
    font-size: 22px !important;
  }

  .subkpi{
    font-size: 11px !important;
  }

  .pill{
    font-size: 10px !important;
    padding: 6px 8px !important;
    gap: 6px !important;
  }

  .scorebubble{
    width: 40px !important;
    height: 40px !important;
    font-size: 14px !important;
  }

  th, td{
    padding: 6px 4px !important;
    font-size: 11px !important;
  }

  .dirarrow{
    font-size: 16px !important;
  }

  .dirdeg{
    font-size: 11px !important;
  }

  .dircompass{
    font-size: 10px !important;
  }

  .tabbar-note{
    font-size: 11px !important;
  }

  h1, h2, h3{
    line-height: 1.1 !important;
  }
}
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)

# ===================== HELPERS =====================
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def ang_diff(a: float, b: float) -> float:
    a = float(a) % 360
    b = float(b) % 360
    d = abs(a - b)
    return min(d, 360 - d)

def deg_to_compass(deg: float) -> str:
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    i = int(((float(deg) % 360) + 11.25) // 22.5) % 16
    return dirs[i]

def deg_to_arrow(deg: float) -> str:
    arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    i = int(((float(deg) % 360) + 22.5) // 45) % 8
    return arrows[i]

def format_direction_html(deg: float) -> str:
    if pd.isna(deg):
        return "—"
    deg = float(deg) % 360
    return f"""
    <div class="dirblock">
      <div class="dirarrow">{deg_to_arrow(deg)}</div>
      <div class="dirdeg">{deg:.0f}°</div>
      <div class="dircompass">{deg_to_compass(deg)}</div>
    </div>
    """

def viento_estado(wdir: float, offshore_dir: float) -> Tuple[str, str]:
    d = ang_diff(wdir, offshore_dir)
    if d <= 35:
        return ("OFF", "good")
    if d <= 85:
        return ("LADO", "warn")
    return ("ON", "bad")

def estrellas(score10: float) -> str:
    s = int(round(clamp(score10 / 2.0, 0, 5)))
    return "★"*s + "☆"*(5-s)

def rating(score10: float) -> str:
    if score10 >= 8.5:
        return "PERFECTO"
    if score10 >= 7.0:
        return "MUY BIEN"
    if score10 >= 5.5:
        return "SURFEABLE"
    if score10 >= 4.0:
        return "REGULAR"
    return "FLOJO"

def color_score(score10: float) -> str:
    if score10 >= 8.5:
        return "#2ecc71"
    if score10 >= 7.0:
        return "#27ae60"
    if score10 >= 5.5:
        return "#f1c40f"
    if score10 >= 4.0:
        return "#e67e22"
    return "#e74c3c"

def circular_mean_deg(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna().values
    if len(s) == 0:
        return float("nan")
    rad = np.deg2rad(s)
    x = np.cos(rad).mean()
    y = np.sin(rad).mean()
    ang = (np.rad2deg(np.arctan2(y, x)) + 360) % 360
    return float(ang)

def nearest_row_by_time(df: pd.DataFrame, target_ts: pd.Timestamp) -> Optional[pd.Series]:
    if df.empty or "time" not in df.columns:
        return None
    x = df.copy()
    x = x.dropna(subset=["time"])
    if x.empty:
        return None
    idx = (x["time"] - target_ts).abs().idxmin()
    return x.loc[idx]

# ===================== TELAMON: MAREA =====================
def detectar_mareas_llenas(df: pd.DataFrame, min_gap_hours: int = 4) -> pd.DatetimeIndex:
    if df.empty or "tide" not in df.columns:
        return pd.DatetimeIndex([])
    s = df.set_index("time")["tide"].astype(float).dropna()
    if s.empty:
        return pd.DatetimeIndex([])
    peaks = s[(s.shift(1) < s) & (s.shift(-1) < s)].index

    kept, last = [], None
    for t in peaks:
        if last is None or (t - last) >= pd.Timedelta(hours=min_gap_hours):
            kept.append(t)
            last = t
    return pd.DatetimeIndex(kept)

def telamon_en_ventana(t: pd.Timestamp, tide_val: float, mareas_llenas: pd.DatetimeIndex) -> bool:
    try:
        tide_val = float(tide_val)
    except Exception:
        return False

    if pd.isna(tide_val) or tide_val <= 0.75:
        return False
    if mareas_llenas is None or len(mareas_llenas) == 0:
        return False

    nearest = mareas_llenas[abs(mareas_llenas - t).argmin()]
    start = nearest - pd.Timedelta(minutes=90)
    end = nearest + pd.Timedelta(minutes=60)
    return (t >= start) and (t <= end)

# ===================== OBSERVACIONES =====================

def github_cfg():
    return {
        "token": st.secrets["github_token"],
        "owner": st.secrets["github_owner"],
        "repo": st.secrets["github_repo"],
        "path": st.secrets["github_csv_path"],
    }

def github_headers():
    cfg = github_cfg()
    return {
        "Authorization": f"Bearer {cfg['token']}",
        "Accept": "application/vnd.github+json",
    }

def columnas_observaciones():
    return [
        "id","timestamp","spot","mi_nota_10","comentario",
        "score_parte_10","main_h","main_per","main_dir",
        "wind_spd","wind_dir","tide","w_state"
    ]

def cargar_observaciones() -> pd.DataFrame:
    cfg = github_cfg()
    url = f"https://api.github.com/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"

    r = requests.get(url, headers=github_headers())

    if r.status_code == 404:
        return pd.DataFrame(columns=columnas_observaciones())

    payload = r.json()
    raw = base64.b64decode(payload["content"]).decode("utf-8")

    df = pd.read_csv(io.StringIO(raw))

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df


def guardar_observacion_repo(df: pd.DataFrame):

    cfg = github_cfg()
    url = f"https://api.github.com/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"

    r = requests.get(url, headers=github_headers())

    sha = None
    if r.status_code == 200:
        sha = r.json()["sha"]

    csv_data = df.to_csv(index=False)

    content = base64.b64encode(csv_data.encode()).decode()

    payload = {
        "message": "update observaciones",
        "content": content,
    }

    if sha:
        payload["sha"] = sha

    requests.put(url, headers=github_headers(), json=payload)


def migrar_observaciones(df: pd.DataFrame) -> pd.DataFrame:

    required = {
        "id": "",
        "timestamp": pd.NaT,
        "spot": "",
        "mi_nota_10": np.nan,
        "comentario": "",
        "score_parte_10": np.nan,
        "main_h": np.nan,
        "main_per": np.nan,
        "main_dir": np.nan,
        "wind_spd": np.nan,
        "wind_dir": np.nan,
        "tide": np.nan,
        "w_state": "",
    }

    out = df.copy()

    for col, default in required.items():
        if col not in out.columns:
            out[col] = default

    return out


def guardar_observacion(
    spot: str,
    mi_nota_10: float,
    comentario: str,
    when_ts: pd.Timestamp,
    snapshot: Optional[Dict[str, Any]] = None,
):

    df = migrar_observaciones(cargar_observaciones())

    snap = snapshot or {}

    nueva = pd.DataFrame([{
        "id": str(uuid.uuid4()),
        "timestamp": when_ts.isoformat(),
        "spot": str(spot),
        "mi_nota_10": float(mi_nota_10),
        "comentario": str(comentario),
        "score_parte_10": snap.get("score_parte_10", np.nan),
        "main_h": snap.get("main_h", np.nan),
        "main_per": snap.get("main_per", np.nan),
        "main_dir": snap.get("main_dir", np.nan),
        "wind_spd": snap.get("wind_spd", np.nan),
        "wind_dir": snap.get("wind_dir", np.nan),
        "tide": snap.get("tide", np.nan),
        "w_state": snap.get("w_state", ""),
    }])

    df2 = pd.concat([df, nueva], ignore_index=True)

    guardar_observacion_repo(df2)

def actualizar_observacion(session_id: str, nuevos_datos: Dict[str, Any]) -> None:
    df = migrar_observaciones(cargar_observaciones())

    if df.empty or "id" not in df.columns:
        raise ValueError("No hay observaciones para actualizar.")

    mask = df["id"].astype(str) == str(session_id)
    if not mask.any():
        raise ValueError("No se encontró la sesión.")

    for k, v in nuevos_datos.items():
        if k in df.columns:
            df.loc[mask, k] = v

    guardar_observacion_repo(df)

def borrar_observacion(session_id: str) -> None:
    df = migrar_observaciones(cargar_observaciones())

    if df.empty or "id" not in df.columns:
        raise ValueError("No hay observaciones para borrar.")

    df = df[df["id"].astype(str) != str(session_id)].copy()
    guardar_observacion_repo(df)
    
def distancia_condiciones(row: pd.Series, target: Dict[str, Any]) -> float:
    penalties = []
    weights = {
        "main_h": 2.2,
        "main_per": 1.7,
        "main_dir": 1.5,
        "wind_spd": 1.6,
        "wind_dir": 1.4,
        "tide": 1.2,
        "score_parte_10": 1.4,
    }

    scales = {
        "main_h": 0.8,
        "main_per": 4.0,
        "main_dir": 45.0,
        "wind_spd": 20.0,
        "wind_dir": 50.0,
        "tide": 0.5,
        "score_parte_10": 2.0,
    }

    for col, weight in weights.items():
        a = pd.to_numeric(row.get(col, np.nan), errors="coerce")
        b = pd.to_numeric(target.get(col, np.nan), errors="coerce")
        if pd.isna(a) or pd.isna(b):
            continue

        if "dir" in col:
            diff = ang_diff(float(a), float(b)) / scales[col]
        else:
            diff = abs(float(a) - float(b)) / scales[col]
        penalties.append(weight * diff)

    if isinstance(row.get("w_state", ""), str) and isinstance(target.get("w_state", ""), str):
        if row.get("w_state", "") != "" and target.get("w_state", "") != "":
            penalties.append(0.8 if row["w_state"] != target["w_state"] else 0.0)

    if not penalties:
        return float("inf")

    return float(sum(penalties))

def predecir_mi_nota_por_similares(
    spot: str,
    target: Dict[str, Any],
    min_obs: int = 3,
    k: int = 7,
) -> Dict[str, Any]:
    obs = migrar_observaciones(cargar_observaciones())
    if obs.empty:
        return {"pred_10": None, "n_obs": 0, "modo": "sin_historial"}

    obs["spot"] = obs["spot"].astype(str)
    obs["mi_nota_10"] = pd.to_numeric(obs["mi_nota_10"], errors="coerce")
    obs = obs.dropna(subset=["mi_nota_10"])

    obs_same = obs[obs["spot"].str.lower() == str(spot).lower()].copy()

    feature_cols = ["score_parte_10", "main_h", "main_per", "main_dir", "wind_spd", "wind_dir", "tide"]
    usable = obs_same.dropna(subset=["mi_nota_10"]).copy()
    usable["_dist"] = usable.apply(lambda r: distancia_condiciones(r, target), axis=1)
    usable = usable.replace([np.inf, -np.inf], np.nan).dropna(subset=["_dist"]).sort_values("_dist")

    if len(usable) < min_obs:
        return {"pred_10": None, "n_obs": int(len(usable)), "modo": "insuficiente"}

    vecinos = usable.head(k).copy()
    vecinos["_w"] = 1.0 / (vecinos["_dist"] + 0.25)
    pred = float(np.average(vecinos["mi_nota_10"], weights=vecinos["_w"]))

    return {
        "pred_10": clamp(pred, 0.0, 10.0),
        "n_obs": int(len(vecinos)),
        "modo": "similares",
    }

def score_combinado(
    score_parte_10: float,
    spot: str,
    target: Dict[str, Any],
    peso_parte: float,
) -> Dict[str, Any]:
    hist = predecir_mi_nota_por_similares(spot=spot, target=target)

    if hist["pred_10"] is None:
        return {
            "score_final_10": float(score_parte_10),
            "mi_pred_10": None,
            "n_obs": hist["n_obs"],
            "modo": hist["modo"],
        }

    peso_parte = float(clamp(peso_parte, 0.0, 1.0))
    final = peso_parte * float(score_parte_10) + (1.0 - peso_parte) * float(hist["pred_10"])

    return {
        "score_final_10": float(clamp(final, 0.0, 10.0)),
        "mi_pred_10": float(hist["pred_10"]),
        "n_obs": int(hist["n_obs"]),
        "modo": hist["modo"],
    }

# ===================== SPOTS =====================
from pathlib import Path

@st.cache_data(ttl=60)
def cargar_spots(path: str = "spots_private.json"):
    base_dir = Path(__file__).parent
    file_path = base_dir / path

    with open(file_path, "r", encoding="utf-8") as f:
        spots = json.load(f)

    if not isinstance(spots, list) or len(spots) == 0:
        raise ValueError("spots_private.json debe ser una lista con al menos 1 spot.")

    norm = []
    for s in spots:
        name = str(s.get("name", "Spot"))
        lat = s.get("latitude", s.get("lat"))
        lon = s.get("longitude", s.get("lon"))
        if lat is None or lon is None:
            raise ValueError(f"El spot '{name}' no tiene latitude/longitude (o lat/lon).")

        prefs = s.get("preferences", {})
        required = [
            "ideal_wave_height_m",
            "ideal_period_s",
            "ideal_swell_direction_deg",
            "offshore_wind_direction_deg",
            "max_wind_speed_kmh",
        ]
        for k in required:
            if k not in prefs:
                raise ValueError(f"En preferences falta '{k}' para el spot '{name}'.")

        norm.append({
            "name": name,
            "latitude": float(lat),
            "longitude": float(lon),
            "timezone": s.get("timezone", TZ),
            "preferences": prefs,
        })
    return norm

# ===================== FETCH =====================
@st.cache_data(ttl=600)
def obtener_datos(lat: float, lon: float, tz: str, days: int = 7) -> pd.DataFrame:
    marine_r = requests.get(
        "https://marine-api.open-meteo.com/v1/marine",
        params={
            "latitude": lat,
            "longitude": lon,
            "forecast_days": days,
            "timezone": tz,
            "hourly": [
                "wave_height",
                "wave_direction",
                "wave_period",
                "swell_wave_height",
                "swell_wave_direction",
                "swell_wave_period",
                "secondary_swell_wave_height",
                "secondary_swell_wave_direction",
                "secondary_swell_wave_period",
                "sea_level_height_msl",
            ],
        },
        timeout=25,
    )
    marine_r.raise_for_status()
    marine = marine_r.json()

    weather_r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "forecast_days": days,
            "timezone": tz,
            "hourly": ["wind_speed_10m", "wind_direction_10m"],
        },
        timeout=25,
    )
    weather_r.raise_for_status()
    weather = weather_r.json()

    df = pd.DataFrame({
        "time": marine["hourly"]["time"],
        "wave_h": marine["hourly"]["wave_height"],
        "wave_dir": marine["hourly"]["wave_direction"],
        "wave_per": marine["hourly"]["wave_period"],
        "swell_h": marine["hourly"]["swell_wave_height"],
        "swell_dir": marine["hourly"]["swell_wave_direction"],
        "swell_per": marine["hourly"]["swell_wave_period"],
        "swell2_h": marine["hourly"]["secondary_swell_wave_height"],
        "swell2_dir": marine["hourly"]["secondary_swell_wave_direction"],
        "swell2_per": marine["hourly"]["secondary_swell_wave_period"],
        "tide": marine["hourly"]["sea_level_height_msl"],
        "wind_spd": weather["hourly"]["wind_speed_10m"],
        "wind_dir": weather["hourly"]["wind_direction_10m"],
    })

    t = pd.to_datetime(df["time"], errors="coerce")
    if getattr(t.dt, "tz", None) is None:
        t = t.dt.tz_localize(tz)
    else:
        t = t.dt.tz_convert(tz)
    df["time"] = t
    return df

# ===================== SWELL “RODEA ISLA” =====================
def puntos_direccion_swell(sdir: float, ideal_deg: float) -> float:
    d = ang_diff(sdir, ideal_deg)
    if d <= 40:
        return 3.0
    if d <= 70:
        return 1.0
    return 0.0

def puntos_swell_secundario(sdir: float, per: float, prefs: Dict[str, Any], primary_points: float) -> float:
    if "secondary_swell_direction_deg" not in prefs:
        return 0.0

    sec_dir = float(prefs.get("secondary_swell_direction_deg"))
    window = float(prefs.get("secondary_swell_window_deg", 40))
    min_per = float(prefs.get("secondary_swell_min_period_s", 11))
    max_score = float(prefs.get("secondary_swell_max_score", 2.0))
    only_if_primary_bad = bool(prefs.get("secondary_swell_only_if_primary_bad", True))

    if per < min_per:
        return 0.0
    if only_if_primary_bad and primary_points >= 1.0:
        return 0.0

    d2 = ang_diff(sdir, sec_dir)
    if d2 <= window:
        w = clamp(1.0 - (d2 / window), 0.0, 1.0)
        return max_score * (0.6 + 0.4 * w)
    return 0.0

# ===================== SCORE =====================
def score_fila(r: pd.Series, prefs: Dict[str, Any], spot_name: str, telamon_highs: Optional[pd.DatetimeIndex]):
    hmin, hmax = prefs["ideal_wave_height_m"]
    pmin, pmax = prefs["ideal_period_s"]
    ideal_swell = float(prefs["ideal_swell_direction_deg"])
    offshore = float(prefs["offshore_wind_direction_deg"])
    max_wind = float(prefs["max_wind_speed_kmh"])

    h = float(r["swell_h"]) if not pd.isna(r["swell_h"]) else float(r["wave_h"])
    per = float(r["swell_per"]) if not pd.isna(r["swell_per"]) else float(r["wave_per"])
    sdir = float(r["swell_dir"]) if not pd.isna(r["swell_dir"]) else float(r["wave_dir"])

    sc = 0.0

    if hmin <= h <= hmax:
        sc += 4
    elif h >= hmin * 0.8 and h <= hmax * 1.2:
        sc += 2

    if pmin <= per <= pmax:
        sc += 4
    elif per >= pmin * 0.8 and per <= pmax * 1.2:
        sc += 2

    p_primary = puntos_direccion_swell(sdir, ideal_swell)
    sc += p_primary
    sc += puntos_swell_secundario(sdir, per, prefs, p_primary)

    w_lbl, w_cls = viento_estado(float(r["wind_dir"]), offshore)
    if w_lbl == "OFF":
        sc += 4
    elif w_lbl == "LADO":
        sc += 2

    wind_spd = float(r["wind_spd"])
    if wind_spd <= max_wind:
        sc += 2
    elif wind_spd <= max_wind * 1.2:
        sc += 1
    else:
        sc -= 2

    score10 = clamp((sc / 19.0) * 10.0, 0.0, 10.0)

    en_ventana = True
    if spot_name.strip().lower() == "telamon":
        highs = telamon_highs if telamon_highs is not None else pd.DatetimeIndex([])
        en_ventana = telamon_en_ventana(r["time"], float(r["tide"]), highs)
        if not en_ventana:
            score10 *= 0.55

    score10 = clamp(score10, 0.0, 10.0)
    return score10, rating(score10), w_lbl, w_cls, h, per, sdir, en_ventana

# ===================== AGREGADOS =====================
def df_to_3h(df: pd.DataFrame, tz: str) -> pd.DataFrame:
    if df.empty:
        return df

    dfx = df.copy()
    dfx["lt"] = dfx["time"].dt.tz_convert(tz)
    dfx = dfx.set_index("lt").sort_index()
    g = dfx.resample("3H", label="left", closed="left")

    out = pd.DataFrame({
        "t": g.size().index,
        "main_h": g["main_h"].max(),
        "main_per": g["main_per"].max(),
        "wind_spd": g["wind_spd"].max(),
        "tide": g["tide"].mean(),
        "score10": g["score10"].max(),
        "rating": g["rating"].first(),
        "w_state": g["w_state"].first(),
        "w_cls": g["w_cls"].first(),
        "en_ventana": g["en_ventana"].first(),
    }).reset_index(drop=True)

    out["main_dir"] = g["main_dir"].apply(circular_mean_deg).values
    out["wind_dir"] = g["wind_dir"].apply(circular_mean_deg).values
    return out

def df_to_daily(df: pd.DataFrame, tz: str) -> pd.DataFrame:
    if df.empty:
        return df

    dfx = df.copy()
    dfx["lt"] = dfx["time"].dt.tz_convert(tz)
    dfx["day"] = dfx["lt"].dt.date
    g = dfx.groupby("day")

    out = pd.DataFrame({
        "day": list(g.size().index),
        "score_max": g["score10"].max(),
        "score_mean": g["score10"].mean(),
        "ola_max": g["main_h"].max(),
        "per_max": g["main_per"].max(),
        "wind_max": g["wind_spd"].max(),
        "tide_mean": g["tide"].mean(),
        "dir_ola": g["main_dir"].apply(circular_mean_deg),
        "dir_viento": g["wind_dir"].apply(circular_mean_deg),
    }).reset_index(drop=True)

    return out

# ===================== RENDER TABLAS =====================
def render_3h_table(df3: pd.DataFrame, spot_name: str) -> None:
    if df3.empty:
        st.info("Sin datos para mostrar.")
        return

    rows = []
    for _, r in df3.iterrows():
        t0 = pd.Timestamp(r["t"])
        t1 = t0 + pd.Timedelta(hours=3)
        horas = f"{t0.strftime('%H:%M')}–{t1.strftime('%H:%M')}"

        score10 = float(r["score10"])
        bcol = color_score(score10)
        wcls = str(r["w_cls"])
        wbg = "goodbg" if wcls == "good" else ("warnbg" if wcls == "warn" else "badbg")

        tel = "—"
        if spot_name.strip().lower() == "telamon":
            ok = bool(r.get("en_ventana", False)) and float(r.get("tide", 0)) > 0.75
            tel = "✅" if ok else "⛔"

        main_dir_html = format_direction_html(r["main_dir"])

        wind_dir_txt = "—"
        if not pd.isna(r["wind_dir"]):
            wind_dir_txt = f"{deg_to_arrow(float(r['wind_dir']))} {deg_to_compass(float(r['wind_dir']))} · {float(r['wind_dir']):.0f}°"

        rows.append(f"""
<tr>
  <td class="rowtitle">{horas}</td>
  <td>
    <span class="scorebubble" style="border-color:{bcol};">{score10:.1f}</span><br/>
    <span class="smallmuted">{estrellas(score10)} · {rating(score10)}</span>
  </td>
  <td>
    <span style="font-weight:900;">{float(r["main_h"]):.1f} m</span><br/>
    <span class="smallmuted">{float(r["main_per"]):.0f} s</span>
  </td>
  <td>{main_dir_html}</td>
  <td class="{wbg}">
    <b>{float(r["wind_spd"]):.0f} km/h</b><br/>
    <span class="smallmuted">{wind_dir_txt}</span><br/>
    <span class="smallmuted"><b>{r["w_state"]}</b></span>
  </td>
  <td>
    <b>{float(r["tide"]):.2f} m</b><br/>
    <span class="smallmuted">marea</span>
  </td>
  <td>{tel}</td>
</tr>
""")

    table = f"""
<div class="tablewrap">
  <table>
    <thead>
      <tr>
        <th style="width:10%;">Tramo</th>
        <th style="width:16%;">Score</th>
        <th style="width:14%;">Altura<br/>Periodo</th>
        <th style="width:18%;">Dirección ola</th>
        <th style="width:22%;">Viento</th>
        <th style="width:12%;">Marea</th>
        <th style="width:8%;">Tel.</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</div>
"""
    st.markdown(table, unsafe_allow_html=True)

def render_daily_table(dfd: pd.DataFrame) -> None:
    if dfd.empty:
        st.info("Sin datos para mostrar.")
        return

    rows = []
    for _, r in dfd.iterrows():
        day = pd.to_datetime(r["day"]).strftime("%d/%m/%Y")
        smax = float(r["score_max"])
        scol = color_score(smax)

        dir_ola_html = format_direction_html(r["dir_ola"])

        dir_viento_txt = "—"
        if not pd.isna(r["dir_viento"]):
            dir_viento_txt = f"{deg_to_arrow(float(r['dir_viento']))} {deg_to_compass(float(r['dir_viento']))} · {float(r['dir_viento']):.0f}°"

        rows.append(f"""
<tr>
  <td class="rowtitle">{day}</td>
  <td>
    <span class="badge" style="background:{scol};">{smax:.1f}</span><br/>
    <span class="smallmuted">media {float(r["score_mean"]):.1f}</span>
  </td>
  <td>
    <b>{float(r["ola_max"]):.1f} m</b><br/>
    <span class="smallmuted">{float(r["per_max"]):.0f} s</span>
  </td>
  <td>{dir_ola_html}</td>
  <td>
    <b>{float(r["wind_max"]):.0f} km/h</b><br/>
    <span class="smallmuted">{dir_viento_txt}</span>
  </td>
  <td>
    <b>{float(r["tide_mean"]):.2f} m</b><br/>
    <span class="smallmuted">media</span>
  </td>
</tr>
""")

    table = f"""
<div class="tablewrap">
  <table>
    <thead>
      <tr>
        <th style="width:18%;">Día</th>
        <th style="width:18%;">Score</th>
        <th style="width:16%;">Ola</th>
        <th style="width:16%;">Dir ola</th>
        <th style="width:20%;">Viento</th>
        <th style="width:12%;">Marea</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</div>
"""
    st.markdown(table, unsafe_allow_html=True)

# ===================== STATE =====================
if "route" not in st.session_state:
    st.session_state["route"] = "home"
if "selected_spot" not in st.session_state:
    st.session_state["selected_spot"] = None

# ===================== HEADER =====================
st.markdown(
    f"""
<div class="center">
  <div style="font-size:42px;font-weight:950;letter-spacing:-0.04em;">🌊 Surf Tracker</div>
  <div class="smallmuted">Auto-refresh cada {ACTUALIZACION_MIN} min · {pd.Timestamp.now(tz=TZ).strftime('%a %H:%M')}</div>
</div>
""",
    unsafe_allow_html=True,
)
st.write("")

if is_mobile:
    st.markdown(
        """
<div class="section-card" style="margin-bottom:12px;">
  <div style="font-size:18px;font-weight:900;">📱 Modo móvil</div>
  <div class="smallmuted">Vista compacta para consultar rápido spots, registrar sesión y revisar historial.</div>
</div>
""",
        unsafe_allow_html=True,
    )

# ===================== SPOTS =====================
spots = cargar_spots()

ban_names = {"El Fronton", "El Frontón", "La Cicer", "Cicer"}
spots = [s for s in spots if s["name"].strip() not in ban_names]
spots = sorted(
    spots,
    key=lambda s: (0 if s["name"].strip().lower() == "telamon" else 1, s["name"].lower()),
)

peso_parte_default = 0.45
now = pd.Timestamp.now(tz=TZ)

def compute_best_list(dias: int, horas_home: int, peso_parte: float):
    out = []

    for s in spots:
        try:
            df_full = obtener_datos(s["latitude"], s["longitude"], s["timezone"], days=dias)
        except Exception:
            continue

        df = df_full[df_full["time"] >= now].head(horas_home).copy()
        if df.empty:
            continue

        telamon_highs = None
        if s["name"].strip().lower() == "telamon":
            df_for_highs = df_full[df_full["time"] >= (now - pd.Timedelta(hours=3))].head(max(horas_home, 72))
            telamon_highs = detectar_mareas_llenas(df_for_highs)

        prefs = s["preferences"]
        scored = df.apply(
            lambda r: score_fila(r, prefs, s["name"], telamon_highs),
            axis=1,
            result_type="expand",
        )
        df[["score10", "rating", "w_state", "w_cls", "main_h", "main_per", "main_dir", "en_ventana"]] = scored

        best = df.sort_values("score10", ascending=False).iloc[0]
        ahora = df.iloc[0]

        target = {
            "score_parte_10": float(best["score10"]),
            "main_h": float(best["main_h"]),
            "main_per": float(best["main_per"]),
            "main_dir": float(best["main_dir"]),
            "wind_spd": float(best["wind_spd"]),
            "wind_dir": float(best["wind_dir"]),
            "tide": float(best["tide"]),
            "w_state": str(best["w_state"]),
        }

        comb = score_combinado(
            score_parte_10=float(best["score10"]),
            spot=s["name"],
            target=target,
            peso_parte=peso_parte,
        )

        out.append({
            "name": s["name"],
            "tz": s["timezone"],
            "lat": s["latitude"],
            "lon": s["longitude"],
            "prefs": prefs,
            "df": df_full,
            "best": best,
            "nowrow": ahora,
            "score_final": float(comb["score_final_10"]),
            "n_obs": comb["n_obs"],
            "mi_pred": comb["mi_pred_10"],
            "modo_hist": comb["modo"],
        })

    out = sorted(out, key=lambda x: float(x["score_final"]), reverse=True)
    return out

def open_spot(name: str):
    st.session_state["selected_spot"] = name
    st.session_state["route"] = "spot"
    st.rerun()

def close_spot():
    st.session_state["selected_spot"] = None
    st.session_state["route"] = "home"
    st.rerun()

def render_spot_page(item: dict):
    spot = item["name"]
    tz = item["tz"]
    prefs = item["prefs"]
    df_full = item["df"].copy()

    st.markdown("---")
    top = st.columns([1, 5, 1])

    with top[0]:
        if st.button("⬅️ Volver", use_container_width=True):
            close_spot()

    with top[1]:
        st.markdown(
            f"""
<div class="center">
  <div style="font-size:34px;font-weight:950;letter-spacing:-0.03em;">{spot}</div>
  <div class="smallmuted">
    Ideal: {prefs['ideal_swell_direction_deg']}° ({deg_to_compass(prefs['ideal_swell_direction_deg'])}) ·
    Offshore: {prefs['offshore_wind_direction_deg']}° ({deg_to_compass(prefs['offshore_wind_direction_deg'])})
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.write("")

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        day_offset = st.selectbox("Día", list(range(0, 7)), format_func=lambda x: "Hoy" if x == 0 else f"+{x} días")
    with c2:
        view = st.radio("Vista", ["Cada 3 horas", "Diario"], horizontal=True)
    with c3:
        st.markdown(
            f"<div class='smallmuted center' style='padding-top:28px;'>Previsión hasta 7 días · {TZ}</div>",
            unsafe_allow_html=True,
        )

    start_day = (pd.Timestamp.now(tz=TZ).normalize() + pd.Timedelta(days=int(day_offset))).tz_convert(tz)
    end_day = start_day + pd.Timedelta(days=1)

    df_day = df_full[(df_full["time"] >= start_day) & (df_full["time"] < end_day)].copy()
    if df_day.empty:
        st.info("No hay datos para ese día.")
        return

    telamon_highs = detectar_mareas_llenas(df_full) if spot.strip().lower() == "telamon" else None
    scored = df_day.apply(lambda r: score_fila(r, prefs, spot, telamon_highs), axis=1, result_type="expand")
    df_day[["score10", "rating", "w_state", "w_cls", "main_h", "main_per", "main_dir", "en_ventana"]] = scored

    best = df_day.sort_values("score10", ascending=False).iloc[0]

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"<div class='center'><div class='kpi'>{float(best['score10']):.1f}</div><div class='subkpi'>Mejor score</div></div>",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"<div class='center'><div class='kpi'>{float(best['main_h']):.1f}m</div><div class='subkpi'>Altura mejor</div></div>",
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"<div class='center'><div class='kpi'>{float(best['main_per']):.0f}s</div><div class='subkpi'>Periodo mejor</div></div>",
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"<div class='center'><div class='kpi'>{float(best['wind_spd']):.0f}</div><div class='subkpi'>Viento (km/h)</div></div>",
            unsafe_allow_html=True,
        )

    st.write("")

    target = {
        "score_parte_10": float(best["score10"]),
        "main_h": float(best["main_h"]),
        "main_per": float(best["main_per"]),
        "main_dir": float(best["main_dir"]),
        "wind_spd": float(best["wind_spd"]),
        "wind_dir": float(best["wind_dir"]),
        "tide": float(best["tide"]),
        "w_state": str(best["w_state"]),
    }
    pred = predecir_mi_nota_por_similares(spot=spot, target=target)

    if pred["pred_10"] is not None:
        st.markdown(
            f"<div class='smallmuted center'>🧠 Con condiciones parecidas, tu nota esperada ronda <b>{pred['pred_10']:.1f}/10</b> · basándose en {pred['n_obs']} sesiones similares.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='smallmuted center'>🧠 Aún no hay suficientes sesiones parecidas en este spot para aprender tu criterio.</div>",
            unsafe_allow_html=True,
        )

    st.write("")

    if view == "Cada 3 horas":
        df3 = df_to_3h(df_day, tz)
        render_3h_table(df3, spot)
    else:
        df_all = df_full.copy()
        scored_all = df_all.apply(lambda r: score_fila(r, prefs, spot, telamon_highs), axis=1, result_type="expand")
        df_all[["score10", "rating", "w_state", "w_cls", "main_h", "main_per", "main_dir", "en_ventana"]] = scored_all
        dfd = df_to_daily(df_all, tz).head(7)
        render_daily_table(dfd)

    st.write("")
    with st.expander("📈 Gráficas (extra)", expanded=False):
        st.line_chart(
            df_day.set_index("time")[["main_h", "main_per", "wind_spd", "tide"]].rename(
                columns={
                    "main_h": "Altura",
                    "main_per": "Periodo",
                    "wind_spd": "Viento",
                    "tide": "Marea",
                }
            )
        )

# ===================== TABS =====================
tab_mejores, tab_olas, tab_reg, tab_hist, tab_mapa = st.tabs(
    ["🏆 Mejores olas", "🌊 Olas", "✍️ Registrar sesión", "📊 Historial", "🗺️ Mapa"]
)

# ===================== TAB MEJORES =====================
with tab_mejores:
    best_list = compute_best_list(
        dias=7,
        horas_home=24,
        peso_parte=peso_parte_default,
    )

    if not best_list:
        st.warning("No hay datos para mostrar ahora mismo.")
    else:
        st.markdown("### TOP 3 ahora")
        st.markdown("<div class='tabbar-note'>Las tres mejores opciones del momento, ajustadas con tu histórico de condiciones parecidas.</div>", unsafe_allow_html=True)
        st.write("")

       cols = st.columns(1 if is_mobile else 3)
       
       for i, item in enumerate(best_list[:3]):
           with cols[0] if is_mobile else cols[i]:
                b = item["best"]
                n = item["nowrow"]
                score = float(item["score_final"])
                bcol = color_score(score)

                tel = ""
                if item["name"].strip().lower() == "telamon":
                    ok = bool(b["en_ventana"]) and float(b["tide"]) > 0.75
                    tel = f" · {'✅ Ventana' if ok else '⛔ Fuera'}"

                pred_txt = f"· tu nota esperada {item['mi_pred']:.1f}/10" if item["mi_pred"] is not None else "· aún sin aprendizaje"

                st.markdown(
                    f"""
<div class="card">
  <div style="display:flex;justify-content:center;gap:10px;align-items:center;">
    <div style="font-weight:950;font-size:18px;">{item["name"]}</div>
    <span class="badge" style="background:{bcol};">{rating(score)}</span>
  </div>

  <div class="center" style="margin-top:8px;">
    <div class="kpi">{score:.1f}<span style="font-size:14px;color:var(--muted);font-weight:800;">/10</span></div>
    <div class="subkpi">Final personalizado · mejor en {b["time"].strftime('%a %H:%M')}{tel}</div>
  </div>

  <div class="center" style="margin-top:10px; display:flex;justify-content:center;gap:10px;flex-wrap:wrap;">
    <span class="pill">🌊 {float(b["main_h"]):.1f}m · {float(b["main_per"]):.0f}s</span>
    <span class="pill">🧭 {deg_to_arrow(float(b["main_dir"]))} {float(b["main_dir"]):.0f}° {deg_to_compass(float(b["main_dir"]))}</span>
  </div>

  <div class="center" style="margin-top:10px; display:flex;justify-content:center;gap:10px;flex-wrap:wrap;">
    <span class="pill">🌬️ {float(n["wind_spd"]):.0f} km/h · {deg_to_arrow(float(n["wind_dir"]))} {float(n["wind_dir"]):.0f}° {deg_to_compass(float(n["wind_dir"]))} · <b>{n["w_state"]}</b></span>
    <span class="pill">🌖 {float(n["tide"]):.2f}m</span>
  </div>

  <div class="center" style="margin-top:10px;" class="smallmuted">
    🎯 Parte {float(b["score10"]):.1f}/10 {pred_txt}
  </div>
</div>
""",
                    unsafe_allow_html=True,
                )

                if st.button("Ver parte", key=f"best_open_{item['name']}", use_container_width=True):
                    open_spot(item["name"])

# ===================== TAB OLAS =====================
with tab_olas:
    st.markdown("### Spots")
    st.markdown(
        "<div class='tabbar-note'>Aquí ves todos los spots y puedes abrir su parte completo.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    with st.expander("⚙️ Ajustes (opcional)", expanded=False):
        dias = st.slider("Días de previsión", 1, 7, 7)
        horas_home = st.slider("Horas para ranking", 6, 72, 24, step=3)
        st.markdown("#### 🎯 Personalización")
        peso_parte = st.slider("Peso del parte frente a mi histórico aprendido", 0.0, 1.0, 0.45, 0.05)

        st.markdown("---")
        if st.button("🔄 Recargar spots"):
            st.cache_data.clear()
            st.rerun()

    if "dias" not in locals():
        dias, horas_home, peso_parte = 7, 24, 0.45

    all_list = compute_best_list(
        dias=dias,
        horas_home=horas_home,
        peso_parte=peso_parte,
    )

    if not all_list:
        st.warning("No hay datos para mostrar ahora mismo.")
    else:
        cols = st.columns(1 if is_mobile else 3)
        for i, item in enumerate(all_list):
            with cols[0] if is_mobile else cols[i % 3]:
                b = item["best"]
                n = item["nowrow"]
                score = float(item["score_final"])
                bcol = color_score(score)

                tel = ""
                if item["name"].strip().lower() == "telamon":
                    ok = bool(b["en_ventana"]) and float(b["tide"]) > 0.75
                    tel = f" · {'✅ Ventana' if ok else '⛔ Fuera'}"

                pred_txt = f"· tu nota esperada {item['mi_pred']:.1f}/10" if item["mi_pred"] is not None else "· aún sin aprendizaje"

                st.markdown(
                    f"""
<div class="card">
  <div style="display:flex;justify-content:center;gap:10px;align-items:center;">
    <div style="font-weight:950;font-size:18px;">{item["name"]}</div>
    <span class="badge" style="background:{bcol};">{rating(score)}</span>
  </div>

  <div class="center" style="margin-top:8px;">
    <div class="kpi">{score:.1f}<span style="font-size:14px;color:var(--muted);font-weight:800;">/10</span></div>
    <div class="subkpi">Final personalizado · mejor en {b["time"].strftime('%a %H:%M')}{tel}</div>
  </div>

  <div class="center" style="margin-top:10px; display:flex;justify-content:center;gap:10px;flex-wrap:wrap;">
    <span class="pill">🌊 {float(b["main_h"]):.1f}m · {float(b["main_per"]):.0f}s</span>
    <span class="pill">🧭 {deg_to_arrow(float(b["main_dir"]))} {float(b["main_dir"]):.0f}° {deg_to_compass(float(b["main_dir"]))}</span>
  </div>

  <div class="center" style="margin-top:10px; display:flex;justify-content:center;gap:10px;flex-wrap:wrap;">
    <span class="pill">🌬️ {float(n["wind_spd"]):.0f} km/h · {deg_to_arrow(float(n["wind_dir"]))} {float(n["wind_dir"]):.0f}° {deg_to_compass(float(n["wind_dir"]))} · <b>{n["w_state"]}</b></span>
    <span class="pill">🌖 {float(n["tide"]):.2f}m</span>
  </div>

  <div class="center" style="margin-top:10px;" class="smallmuted">
    🎯 Parte {float(b["score10"]):.1f}/10 {pred_txt}
  </div>
</div>
""",
                    unsafe_allow_html=True,
                )

                if st.button("Ver parte", key=f"all_open_{item['name']}", use_container_width=True):
                    open_spot(item["name"])

# ===================== TAB REGISTRAR =====================
with tab_reg:
    st.markdown("### Registrar sesión")
    st.markdown(
        "<div class='tabbar-note'>Guarda tu nota y además se registrará una foto de las condiciones para que la app aprenda de ti.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    nombres = [s["name"] for s in spots]
    c1, c2, c3, c4 = st.columns([2, 1, 1, 2])

    with c1:
        spot_sel = st.selectbox("Spot", nombres, index=0)
    with c2:
        mi_nota = st.number_input("Mi nota (1–10)", min_value=1.0, max_value=10.0, value=7.0, step=0.5)
    with c3:
        hora = st.time_input("Hora", value=datetime.now().time().replace(second=0, microsecond=0))
    with c4:
        fecha = st.date_input("Fecha", value=date.today())

    comentario = st.text_input(
        "Comentario (opcional)",
        placeholder="viento cruzado, series limpias, marea alta...",
    )

    spot_obj = next((s for s in spots if s["name"] == spot_sel), None)
    snapshot_preview = None

    if spot_obj is not None:
        try:
            df_reg = obtener_datos(spot_obj["latitude"], spot_obj["longitude"], spot_obj["timezone"], days=7).copy()
            telamon_highs_reg = detectar_mareas_llenas(df_reg) if spot_sel.strip().lower() == "telamon" else None
            scored_reg = df_reg.apply(
                lambda r: score_fila(r, spot_obj["preferences"], spot_sel, telamon_highs_reg),
                axis=1,
                result_type="expand",
            )
            df_reg[["score10", "rating", "w_state", "w_cls", "main_h", "main_per", "main_dir", "en_ventana"]] = scored_reg

            dt = datetime.combine(fecha, hora)
            when_ts = pd.Timestamp(dt).tz_localize(TZ)
            row_near = nearest_row_by_time(df_reg, when_ts)

            if row_near is not None:
                snapshot_preview = {
                    "score_parte_10": float(row_near["score10"]),
                    "main_h": float(row_near["main_h"]),
                    "main_per": float(row_near["main_per"]),
                    "main_dir": float(row_near["main_dir"]),
                    "wind_spd": float(row_near["wind_spd"]),
                    "wind_dir": float(row_near["wind_dir"]),
                    "tide": float(row_near["tide"]),
                    "w_state": str(row_near["w_state"]),
                    "time": row_near["time"],
                }

                st.markdown(
                    f"""
<div class="section-card">
  <div style="font-weight:900; margin-bottom:8px;">Foto de condiciones que se guardará</div>
  <div class="smallmuted">
    Hora más cercana: {pd.Timestamp(snapshot_preview["time"]).strftime('%d/%m %H:%M')} ·
    Parte {snapshot_preview["score_parte_10"]:.1f}/10 ·
    Ola {snapshot_preview["main_h"]:.1f}m {snapshot_preview["main_per"]:.0f}s ·
    Dir {deg_to_arrow(snapshot_preview["main_dir"])} {deg_to_compass(snapshot_preview["main_dir"])} {snapshot_preview["main_dir"]:.0f}° ·
    Viento {snapshot_preview["wind_spd"]:.0f} km/h · {deg_to_arrow(snapshot_preview["wind_dir"])} {deg_to_compass(snapshot_preview["wind_dir"])} {snapshot_preview["wind_dir"]:.0f}° ·
    {snapshot_preview["w_state"]} ·
    Marea {snapshot_preview["tide"]:.2f}m
  </div>
</div>
""",
                    unsafe_allow_html=True,
                )
        except Exception:
            snapshot_preview = None

    admin_key_input = st.text_input("Clave admin", type="password")
    if st.button("💾 Guardar", use_container_width=True):
        dt = datetime.combine(fecha, hora)
        when_ts = pd.Timestamp(dt).tz_localize(TZ)
        guardar_observacion(
            spot=spot_sel,
            mi_nota_10=mi_nota,
            comentario=comentario,
            when_ts=when_ts,
            snapshot=snapshot_preview,
        )
        st.success("Guardado ✅")

# ===================== TAB HISTORIAL =====================
with tab_hist:
    st.markdown("### Historial de sesiones")
    st.markdown(
        "<div class='tabbar-note'>Aquí ves tus notas y, si existen, también las condiciones que la app ha usado para aprender.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    obs = migrar_observaciones(cargar_observaciones())
        
    admin_key_hist = st.text_input("Clave admin para editar/borrar", type="password", key="hist_admin")

    if not obs.empty:
        obs["timestamp"] = pd.to_datetime(obs["timestamp"], errors="coerce", utc=True).dt.tz_convert(TZ)
        obs = obs.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False)

        opciones = obs.apply(
            lambda r: f"{r['timestamp'].strftime('%d/%m/%Y %H:%M')} · {r['spot']} · nota {float(r['mi_nota_10']):.1f}",
            axis=1
        ).tolist()

        ids = obs["id"].astype(str).tolist()

        st.markdown("### Editar o borrar sesión")
        idx_sel = st.selectbox("Selecciona una sesión", range(len(opciones)), format_func=lambda i: opciones[i])
        fila_sel = obs.iloc[idx_sel]

        col1, col2, col3 = st.columns(3)
        with col1:
            nuevo_spot = st.text_input("Spot", value=str(fila_sel["spot"]), key="edit_spot")
        with col2:
            nueva_nota = st.number_input(
                "Mi nota",
                min_value=1.0,
                max_value=10.0,
                value=float(fila_sel["mi_nota_10"]),
                step=0.5,
                key="edit_nota"
            )
        with col3:
            nuevo_comentario = st.text_input(
                "Comentario",
                value=str(fila_sel["comentario"]) if pd.notna(fila_sel["comentario"]) else "",
                key="edit_comment"
            )

        cedit, cdel = st.columns(2)

        with cedit:
            if st.button("✏️ Guardar cambios", use_container_width=True):
                if admin_key_hist != st.secrets["admin_key"]:
                    st.error("Clave admin incorrecta")
                else:
                    try:
                        actualizar_observacion(
                            session_id=ids[idx_sel],
                            nuevos_datos={
                                "spot": nuevo_spot,
                                "mi_nota_10": nueva_nota,
                                "comentario": nuevo_comentario,
                            }
                        )
                        st.success("Sesión actualizada ✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo actualizar: {e}")

        with cdel:
            if st.button("🗑️ Borrar sesión", use_container_width=True):
                if admin_key_hist != st.secrets["admin_key"]:
                    st.error("Clave admin incorrecta")
                else:
                    try:
                        borrar_observacion(ids[idx_sel])
                        st.success("Sesión borrada ✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo borrar: {e}")
    if obs.empty:
        st.info("Aún no has guardado sesiones.")
    else:
        obs["timestamp"] = pd.to_datetime(obs["timestamp"], errors="coerce", utc=True).dt.tz_convert(TZ)
        obs = obs.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False)

        pretty = obs.copy()
        pretty["Fecha y hora"] = pretty["timestamp"].dt.strftime("%d/%m/%Y %H:%M")
        pretty["Spot"] = pretty["spot"].astype(str)
        pretty["Mi nota"] = pretty["mi_nota_10"].astype(float).map(lambda x: f"{x:.1f}")
        pretty["Comentario"] = pretty["comentario"].fillna("").astype(str)

        def fmt_cond(r):
            try:
                if pd.isna(r["main_h"]) or pd.isna(r["wind_spd"]):
                    return "—"
                return (
                    f"Ola {float(r['main_h']):.1f}m {float(r['main_per']):.0f}s · "
                    f"{deg_to_compass(float(r['main_dir']))} {float(r['main_dir']):.0f}° · "
                    f"Viento {float(r['wind_spd']):.0f} km/h {deg_to_compass(float(r['wind_dir']))} {float(r['wind_dir']):.0f}° · "
                    f"Marea {float(r['tide']):.2f}m"
                )
            except Exception:
                return "—"

        pretty["Condiciones"] = pretty.apply(fmt_cond, axis=1)
        pretty = pretty[["Fecha y hora", "Spot", "Mi nota", "Condiciones", "Comentario"]]

        rows = []
        for _, r in pretty.iterrows():
            rows.append(f"""
<tr>
  <td class="rowtitle">{r['Fecha y hora']}</td>
  <td>{r['Spot']}</td>
  <td><span class="badge" style="background: rgba(43,124,255,.85); color:#0b0f15;">{r['Mi nota']}</span></td>
  <td style="text-align:left;">{r['Condiciones']}</td>
  <td style="text-align:left;">{r['Comentario']}</td>
</tr>
""")

        table = f"""
<div class="tablewrap">
  <table>
    <thead>
      <tr>
        <th style="width:16%;">Fecha y hora</th>
        <th style="width:14%;">Spot</th>
        <th style="width:10%;">Mi nota</th>
        <th style="width:35%;">Condiciones</th>
        <th style="width:25%;">Comentario</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</div>
"""
        st.markdown(table, unsafe_allow_html=True)

        st.write("")
        st.download_button(
            "⬇️ Descargar historial (CSV)",
            data=obs.to_csv(index=False).encode("utf-8"),
            file_name="observaciones.csv",
            mime="text/csv",
        )

# ===================== TAB MAPA =====================
with tab_mapa:
    st.markdown("### Mapa")
    st.info("🗺️ Próximamente: mapa interactivo con spots.")

# ===================== VISTA SPOT =====================
if st.session_state.get("route") == "spot" and st.session_state.get("selected_spot"):
    all_list = compute_best_list(
        dias=7,
        horas_home=24,
        peso_parte=peso_parte_default,
    )

    selected_name = st.session_state["selected_spot"]
    item = next((x for x in all_list if x["name"] == selected_name), None)

    if item is None:
        st.warning("No encuentro el spot seleccionado. Recarga spots.")
    else:
        render_spot_page(item)
