"""
dateExtractor.py
Extrae y normaliza expresiones temporales en español a fechas concretas YYYY-MM-DD.
Soporta:
  - Rango día a día mismo mes:  "entre el 1 al 5 de octubre del 2024"  → FECHA_INICIO / FECHA_FIN
  - Rango mes a mes mismo año:  "entre enero y diciembre del 2025"      → FECHA_INICIO / FECHA_FIN
  - Rango año a año:            "entre el 2024 y 2026"                  → FECHA_INICIO / FECHA_FIN
  - Solo año:                   "en el año 2024"                        → FECHA_INICIO / FECHA_FIN
  - Mes + año:                  "octubre del 2025"                      → FECHA: 2025-10-01
  - Día + mes + año:            "15 de marzo del 2026"                  → FECHA: 2026-03-15
  - Últimos N días/sem/meses:   "últimos 5 días"                        → FECHA_INICIO / FECHA_FIN
  - Última semana / último mes: "última semana"                         → FECHA_INICIO / FECHA_FIN
  - Hace N días:                "hace 3 días"                           → FECHA_INICIO / FECHA_FIN
  - Sin última semana:          "sin contar la última semana"           → FECHA_FIN
  - Hoy / ayer:                 "hoy", "ayer"                           → FECHA
"""

import re
from datetime import date, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# Tablas de referencia
# ─────────────────────────────────────────────────────────────────────────────
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

MESES_PATTERN = '|'.join(MESES.keys())

# ─────────────────────────────────────────────────────────────────────────────
# Patrones regex (orden importa: más específico primero)
# ─────────────────────────────────────────────────────────────────────────────
PATRONES = [

    # ✅ "entre el 1 al 5 de octubre del 2024" → FECHA_INICIO / FECHA_FIN
    {
        "nombre": "ENTRE_DIA_AL_DIA_MES_ANIO",
        "regex": re.compile(
            rf'entre\s+el\s+(\d{{1,2}})\s+(?:al|y)\s+(\d{{1,2}})\s+de\s+({MESES_PATTERN})\s+de(?:l)?\s+(\d{{4}})',
            re.IGNORECASE
        ),
    },

    # ✅ "entre enero y diciembre del 2025" → FECHA_INICIO: 2025-01-01 / FECHA_FIN: 2025-12-31
    {
        "nombre": "ENTRE_MES_Y_MES_ANIO",
        "regex": re.compile(
            rf'entre\s+({MESES_PATTERN})\s+y\s+({MESES_PATTERN})\s+de(?:l)?\s+(\d{{4}})',
            re.IGNORECASE
        ),
    },

    # ✅ "entre el 2024 y 2026" → FECHA_INICIO: 2024-01-01 / FECHA_FIN: 2026-12-31
    {
        "nombre": "ENTRE_ANIO_Y_ANIO",
        "regex": re.compile(
            r'entre\s+(?:el\s+)?(\d{4})\s+y\s+(\d{4})',
            re.IGNORECASE
        ),
    },

    # ✅ "en el año 2024" / "año 2024" → FECHA_INICIO: 2024-01-01 / FECHA_FIN: 2024-12-31
    {
        "nombre": "SOLO_ANIO",
        "regex": re.compile(
            r'(?:en\s+el\s+)?a[ñn]o\s+(\d{4})',
            re.IGNORECASE
        ),
    },

    # "sin contar la última semana" → FECHA_FIN = hoy - 7 días
    {
        "nombre": "SIN_ULTIMA_SEMANA",
        "regex": re.compile(
            r'sin\s+(?:contar\s+)?(?:la\s+)?[uú]ltima\s+semana',
            re.IGNORECASE
        ),
    },

    # "sin contar el último mes" → FECHA_FIN = hoy - 30 días
    {
        "nombre": "SIN_ULTIMO_MES",
        "regex": re.compile(
            r'sin\s+(?:contar\s+)?(?:el\s+)?[uú]ltimo\s+mes',
            re.IGNORECASE
        ),
    },

    # "últimos N días/semanas/meses" → rango FECHA_INICIO / FECHA_FIN
    {
        "nombre": "ULTIMOS_N_UNIDAD",
        "regex": re.compile(
            r'[uú]ltimos?\s+(\d+)\s+(d[íi]as?|semanas?|meses?)',
            re.IGNORECASE
        ),
    },

    # "hace N días/semanas/meses" → rango FECHA_INICIO / FECHA_FIN
    {
        "nombre": "HACE_N_UNIDAD",
        "regex": re.compile(
            r'hace\s+(\d+)\s+(d[íi]as?|semanas?|meses?)',
            re.IGNORECASE
        ),
    },

    # "última semana" → rango últimos 7 días
    {
        "nombre": "ULTIMA_SEMANA",
        "regex": re.compile(
            r'(?<!\bsin\s)(?<!\bsin contar\s)[uú]ltima\s+semana',
            re.IGNORECASE
        ),
    },

    # "último mes" → rango últimos 30 días
    {
        "nombre": "ULTIMO_MES",
        "regex": re.compile(
            r'(?<!\bsin\s)(?<!\bsin contar\s)[uú]ltimo\s+mes',
            re.IGNORECASE
        ),
    },

    # "15 de octubre del 2025"
    {
        "nombre": "DIA_MES_ANIO",
        "regex": re.compile(
            rf'(\d{{1,2}})\s+de\s+({MESES_PATTERN})\s+de(?:l)?\s+(\d{{4}})',
            re.IGNORECASE
        ),
    },

    # "octubre del 2025"
    {
        "nombre": "MES_ANIO",
        "regex": re.compile(
            rf'(?<!\d\s)(?<!\d\s de\s)({MESES_PATTERN})\s+de(?:l)?\s+(\d{{4}})',
            re.IGNORECASE
        ),
    },

    # "hoy"
    {
        "nombre": "HOY",
        "regex": re.compile(r'\bhoy\b', re.IGNORECASE),
    },

    # "ayer"
    {
        "nombre": "AYER",
        "regex": re.compile(r'\bayer\b', re.IGNORECASE),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _fmt(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def _ultimo_dia_mes(anio: int, mes: int) -> date:
    """Retorna el último día del mes dado."""
    if mes == 12:
        return date(anio, 12, 31)
    return date(anio, mes + 1, 1) - timedelta(days=1)

def _delta_por_unidad(n: int, unidad: str) -> timedelta:
    u = unidad.lower()
    if "semana" in u:
        return timedelta(weeks=n)
    if "mes" in u:
        return timedelta(days=n * 30)
    return timedelta(days=n)


# ─────────────────────────────────────────────────────────────────────────────
# Función principal
# ─────────────────────────────────────────────────────────────────────────────
def extraer_fechas(texto: str, hoy: date = None) -> list:
    """
    Recibe un texto y retorna una lista de entidades de fecha detectadas.
    Si se detecta un rango, retorna DOS entidades: FECHA_INICIO y FECHA_FIN.
    """
    if hoy is None:
        hoy = date.today()

    resultados  = []
    texto_lower = texto.lower()

    for patron in PATRONES:
        match = patron["regex"].search(texto_lower)
        if not match:
            continue

        nombre    = patron["nombre"]
        expresion = match.group(0)

        # ── Entre día al día mismo mes ────────────────────────────────────────
        if nombre == "ENTRE_DIA_AL_DIA_MES_ANIO":
            dia_ini = int(match.group(1))
            dia_fin = int(match.group(2))
            mes     = MESES.get(match.group(3).lower(), 1)
            anio    = int(match.group(4))
            resultados.append({"tipo": "FECHA_INICIO", "valor": _fmt(date(anio, mes, dia_ini)), "expresion": expresion})
            resultados.append({"tipo": "FECHA_FIN",    "valor": _fmt(date(anio, mes, dia_fin)), "expresion": expresion})

        # ✅ Entre mes y mes mismo año ─────────────────────────────────────────
        elif nombre == "ENTRE_MES_Y_MES_ANIO":
            mes_ini = MESES.get(match.group(1).lower(), 1)
            mes_fin = MESES.get(match.group(2).lower(), 12)
            anio    = int(match.group(3))
            resultados.append({"tipo": "FECHA_INICIO", "valor": _fmt(date(anio, mes_ini, 1)),                    "expresion": expresion})
            resultados.append({"tipo": "FECHA_FIN",    "valor": _fmt(_ultimo_dia_mes(anio, mes_fin)),            "expresion": expresion})

        # ✅ Entre año y año ───────────────────────────────────────────────────
        elif nombre == "ENTRE_ANIO_Y_ANIO":
            anio_ini = int(match.group(1))
            anio_fin = int(match.group(2))
            resultados.append({"tipo": "FECHA_INICIO", "valor": _fmt(date(anio_ini, 1, 1)),  "expresion": expresion})
            resultados.append({"tipo": "FECHA_FIN",    "valor": _fmt(date(anio_fin, 12, 31)), "expresion": expresion})

        # ✅ Solo año ──────────────────────────────────────────────────────────
        elif nombre == "SOLO_ANIO":
            anio = int(match.group(1))
            resultados.append({"tipo": "FECHA_INICIO", "valor": _fmt(date(anio, 1, 1)),   "expresion": expresion})
            resultados.append({"tipo": "FECHA_FIN",    "valor": _fmt(date(anio, 12, 31)), "expresion": expresion})

        # ── Sin última semana ─────────────────────────────────────────────────
        elif nombre == "SIN_ULTIMA_SEMANA":
            resultados.append({"tipo": "FECHA_FIN", "valor": _fmt(hoy - timedelta(weeks=1)), "expresion": expresion})

        # ── Sin último mes ────────────────────────────────────────────────────
        elif nombre == "SIN_ULTIMO_MES":
            resultados.append({"tipo": "FECHA_FIN", "valor": _fmt(hoy - timedelta(days=30)), "expresion": expresion})

        # ── Últimos N / Hace N ────────────────────────────────────────────────
        elif nombre in ("ULTIMOS_N_UNIDAD", "HACE_N_UNIDAD"):
            n, unidad = int(match.group(1)), match.group(2)
            delta     = _delta_por_unidad(n, unidad)
            resultados.append({"tipo": "FECHA_INICIO", "valor": _fmt(hoy - delta), "expresion": expresion})
            resultados.append({"tipo": "FECHA_FIN",    "valor": _fmt(hoy),         "expresion": expresion})

        # ── Última semana ─────────────────────────────────────────────────────
        elif nombre == "ULTIMA_SEMANA":
            resultados.append({"tipo": "FECHA_INICIO", "valor": _fmt(hoy - timedelta(weeks=1)), "expresion": expresion})
            resultados.append({"tipo": "FECHA_FIN",    "valor": _fmt(hoy),                      "expresion": expresion})

        # ── Último mes ────────────────────────────────────────────────────────
        elif nombre == "ULTIMO_MES":
            resultados.append({"tipo": "FECHA_INICIO", "valor": _fmt(hoy - timedelta(days=30)), "expresion": expresion})
            resultados.append({"tipo": "FECHA_FIN",    "valor": _fmt(hoy),                      "expresion": expresion})

        # ── Día + mes + año ───────────────────────────────────────────────────
        elif nombre == "DIA_MES_ANIO":
            dia, mes, anio = int(match.group(1)), MESES.get(match.group(2).lower(), 1), int(match.group(3))
            resultados.append({"tipo": "FECHA", "valor": _fmt(date(anio, mes, dia)), "expresion": expresion})

        # ── Mes + año ─────────────────────────────────────────────────────────
        elif nombre == "MES_ANIO":
            mes, anio = MESES.get(match.group(1).lower(), 1), int(match.group(2))
            resultados.append({"tipo": "FECHA", "valor": _fmt(date(anio, mes, 1)), "expresion": expresion})

        # ── Hoy ───────────────────────────────────────────────────────────────
        elif nombre == "HOY":
            resultados.append({"tipo": "FECHA", "valor": _fmt(hoy), "expresion": expresion})

        # ── Ayer ──────────────────────────────────────────────────────────────
        elif nombre == "AYER":
            resultados.append({"tipo": "FECHA", "valor": _fmt(hoy - timedelta(days=1)), "expresion": expresion})

        if resultados:
            break

    return resultados