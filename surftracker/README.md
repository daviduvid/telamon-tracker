# Surf Tracker Privado (Streamlit)

Dashboard privado de surf que consume:
- Open-Meteo Marine (olas/swell)
- Open-Meteo Weather (viento)

Lee los spots desde `spots_private.json` (sin hardcodear spots en el código) y calcula un score por spot.

## 1) Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Configurar spots privados

Crea tu archivo privado copiando el ejemplo:

```bash
cp spots_private.example.json spots_private.json
```

Formato esperado por spot:

```json
[
  {
    "name": "Mi Spot",
    "latitude": 28.123,
    "longitude": -15.456,
    "timezone": "Atlantic/Canary",
    "preferences": {
      "ideal_wave_height_m": [0.8, 2.5],
      "ideal_period_s": [9, 16],
      "ideal_swell_direction_deg": 320,
      "offshore_wind_direction_deg": 90,
      "max_wind_speed_kmh": 25
    }
  }
]
```

Campos obligatorios:
- `name`
- `latitude`
- `longitude`

Campos opcionales:
- `timezone` (por defecto `auto`)
- `preferences.*`

## 3) Ejecutar

```bash
streamlit run app.py
```

## Notas

- Se usa caching básico con `@st.cache_data`:
  - Spots: TTL 1 hora
  - APIs Open-Meteo: TTL 15 minutos
- El score (0-100) combina altura/periodo de ola, dirección de swell y viento (intensidad/dirección).
