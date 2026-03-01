import streamlit as st
import requests
import pandas as pd
import json
import re

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def limpiar_nombre(nombre: str) -> str:
    """Elimina artefactos de la IA: pipes, asteriscos, guiones, listas, etc."""
    nombre = nombre.strip()
    nombre = re.sub(r'[`*_]', '', nombre)
    nombre = nombre.strip('|').strip()
    nombre = re.sub(r'^[\d]+[.)]\s*', '', nombre)
    nombre = re.sub(r'^[-•–]\s*', '', nombre)
    nombre = nombre.strip('"\'')
    return nombre.strip()

def extraer_json_de_texto(texto: str) -> dict:
    """Extrae el primer objeto JSON válido ignorando todo el ruido alrededor."""
    inicio = texto.find('{')
    fin    = texto.rfind('}')
    if inicio != -1 and fin != -1:
        try:
            return json.loads(texto[inicio:fin + 1])
        except json.JSONDecodeError:
            pass
    return {}

PALABRAS_RUIDO = {
    "aquí", "aqui", "los", "las", "a continuación", "continuacion",
    "disclaimer", "siguiente", "resultado", "resultados", "valores",
    "columna", "tabla", "here", "the", "following", "distinct",
    "query", "sql", "select", "from", "limit", "nota", "note",
    "importante", "son:", "son", "participants", "participant",
    "names", "name", "países", "paises", "teams", "team",
    "lista", "list", "estos", "estas", "únicos", "unicos"
}

@st.cache_data(show_spinner="📡 Cargando participantes desde Denodo…", ttl=300)
def obtener_participantes(base_url: str, username: str, password: str,
                          nombre_vista: str) -> list[str]:
    """
    Obtiene los valores únicos de participant_name directamente
    de la vista indicada (admin.basketball, admin.football, etc.).
    """
    payload = {
        "question": (
            f"Necesito los valores únicos que existen en la columna participant_name "
            f"de la vista {nombre_vista}. "
            f"Dame los primeros 50 valores distintos que encuentres. "
            f"RESPONDE ÚNICAMENTE con los valores, uno por línea, "
            f"sin numeración, sin guiones, sin markdown, sin explicaciones, "
            f"sin texto introductorio, sin texto al final."
        )
    }

    try:
        r = requests.post(
            f"{base_url.rstrip('/')}/answerDataQuestion",
            json=payload,
            auth=(username, password),
            timeout=45
        )
        r.raise_for_status()
        texto = r.json().get("answer", "")

        nombres = []
        for linea in texto.split("\n"):
            limpio = limpiar_nombre(linea)
            if (len(limpio) > 1
                    and "|" not in limpio
                    and limpio.lower() not in PALABRAS_RUIDO
                    and not any(limpio.lower().startswith(p) for p in PALABRAS_RUIDO)
                    and "disclaimer" not in limpio.lower()
                    and not limpio.isdigit()):
                nombres.append(limpio)

        unicos = sorted(list(dict.fromkeys(n for n in nombres if n)))
        return unicos if len(unicos) >= 2 else []
    except Exception:
        return []


# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Olympic Investor · Paris 2024",
    page_icon="💰",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:ital,wght@0,300;0,400;0,600;1,400&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp {
    background: radial-gradient(ellipse at 20% 0%, #0d1f12 0%, #060d0a 50%, #020508 100%);
    color: #e0f0e8;
}
section[data-testid="stSidebar"] {
    background: #050e08;
    border-right: 1px solid rgba(255,255,255,0.05);
}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stRadio label {
    color: rgba(160,220,180,0.7) !important;
    font-size: 13px !important;
    letter-spacing: 0.05em;
}
input, textarea {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(80,200,120,0.2) !important;
    border-radius: 8px !important;
    color: #e0f0e8 !important;
}
input:focus, textarea:focus {
    border-color: rgba(80,200,120,0.5) !important;
    box-shadow: 0 0 0 2px rgba(80,200,120,0.08) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1db954 0%, #0d8a3a 100%) !important;
    border: none !important; border-radius: 10px !important; color: #001a08 !important;
    font-family: 'Bebas Neue', sans-serif !important; font-size: 22px !important;
    letter-spacing: 0.12em !important; padding: 14px 0 !important;
    box-shadow: 0 4px 28px rgba(29,185,84,0.4) !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 36px rgba(29,185,84,0.6) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:not([kind="primary"]) {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(80,200,120,0.2) !important;
    border-radius: 8px !important;
    color: #a0dcb4 !important;
    transition: all 0.2s ease !important;
}
.stDataFrame {
    border: 1px solid rgba(80,200,120,0.15) !important;
    border-radius: 10px !important; overflow: hidden !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.03) !important;
    border-color: rgba(80,200,120,0.2) !important;
    color: #e0f0e8 !important;
}
hr { border-color: rgba(80,200,120,0.1) !important; }

div[data-testid="stRadio"] > div { display: flex; gap: 10px; flex-wrap: wrap; }
div[data-testid="stRadio"] label {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(80,200,120,0.2);
    border-radius: 30px !important;
    padding: 8px 22px !important;
    cursor: pointer; transition: all 0.2s;
    font-size: 14px !important;
    color: #a0dcb4 !important;
}
div[data-testid="stRadio"] label:hover {
    border-color: rgba(80,200,120,0.5);
    background: rgba(80,200,120,0.06);
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:24px 0 12px;'>
        <div style='font-size:42px;'>💹</div>
        <div style='font-family:"Bebas Neue",sans-serif;font-size:16px;letter-spacing:.15em;
                    color:#1db954;margin-top:8px;'>SDK CONNECTION</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")

    base_url = st.text_input("🔗 URL Denodo AI SDK", value="http://localhost:8008")
    username = st.text_input("👤 Usuario", value="admin")
    password = st.text_input("🔑 Contraseña", value="admin", type="password")

    st.markdown("---")
    if st.button("🔌 Probar conexión", use_container_width=True):
        try:
            r = requests.get(f"{base_url.rstrip('/')}/docs", timeout=4)
            st.success("✅ SDK conectado") if r.status_code < 500 else st.error("❌ SDK no responde")
        except Exception:
            st.error("❌ No se puede conectar")

    st.markdown("---")
    st.markdown("""<div style='font-size:11px;color:rgba(120,180,140,.35);text-align:center;line-height:1.7;'>
        HackUDC 2026 · Denodo AI SDK<br>París 2024 Olympic Games<br>Sports Investment Engine
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# HERO
# ─────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:48px 0 20px;'>
    <div style='font-size:54px;margin-bottom:16px;'>💰&nbsp;🏅&nbsp;💰</div>
    <div style='font-family:"Bebas Neue",sans-serif;font-size:68px;letter-spacing:.04em;
                background:linear-gradient(90deg,#1db954,#a8ff78,#ffffff,#ffd060);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                background-clip:text;line-height:1;margin-bottom:12px;'>
        OLYMPIC INVESTOR
    </div>
    <div style='font-family:"Bebas Neue",sans-serif;font-size:18px;letter-spacing:.28em;
                color:rgba(160,220,180,.45);margin-bottom:22px;'>
        PARIS 2024 · SPORTS TALENT INTELLIGENCE
    </div>
    <div style='max-width:640px;margin:0 auto;font-size:15px;color:rgba(180,220,200,.65);
                line-height:1.8;padding:0 20px;'>
        Actúas como un <b style='color:#a8ff78;'>inversor en talento deportivo</b>.
        Selecciona dos competidores, analiza su rendimiento real en París 2024
        y obtén una <b style='color:#ffd060;'>recomendación de inversión fundamentada</b>
        que maximice tu retorno según métricas competitivas objetivas.
    </div>
</div>
""", unsafe_allow_html=True)

# Badges de datasets disponibles
c1, c2, c3, c4 = st.columns(4)
for col, emoji, label, vista in [
    (c1, "🏀", "Basketball",   "admin.basketball"),
    (c2, "⚽", "Football",     "admin.football"),
    (c3, "🏐", "Volleyball",   "admin.volleyball"),
]:
    col.markdown(f"""
    <div style='text-align:center;background:rgba(29,185,84,.06);
                border:1px solid rgba(29,185,84,.14);border-radius:10px;padding:12px 6px;'>
        <div style='font-size:24px;margin-bottom:4px;'>{emoji}</div>
        <div style='font-family:"Bebas Neue",sans-serif;font-size:13px;
                    color:#1db954;letter-spacing:.08em;'>{label}</div>
        <div style='font-size:10px;color:rgba(160,220,180,.3);margin-top:3px;
                    font-family:monospace;'>{vista}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")


# ─────────────────────────────────────────
# BLOQUE 1 — DEPORTE
# ─────────────────────────────────────────
st.markdown("""<div style='font-family:"Bebas Neue",sans-serif;font-size:22px;
            letter-spacing:.12em;color:#1db954;margin-bottom:10px;'>
    ① DISCIPLINA OLÍMPICA</div>""", unsafe_allow_html=True)

deportes = {
    "🏀  Basketball":   "admin.basketball",
    "⚽  Football":     "admin.football",
    "🏐  Volleyball":   "admin.volleyball",
}

deporte_label     = st.radio("Deporte", list(deportes.keys()), horizontal=True,
                               label_visibility="collapsed")
nombre_vista_base = deportes[deporte_label]

st.markdown("---")


# ─────────────────────────────────────────
# BLOQUE 2 — PARTICIPANTES
# ─────────────────────────────────────────
st.markdown("""<div style='font-family:"Bebas Neue",sans-serif;font-size:22px;
            letter-spacing:.12em;color:#1db954;margin-bottom:10px;'>
    ② SELECCIONA LOS COMPETIDORES A COMPARAR</div>""", unsafe_allow_html=True)

# Badge de vista activa
st.markdown(f"""
<div style='display:inline-flex;align-items:center;gap:8px;
            background:rgba(29,185,84,.07);border:1px solid rgba(29,185,84,.18);
            border-radius:20px;padding:5px 16px;margin-bottom:14px;'>
    <span style='width:7px;height:7px;background:#1db954;border-radius:50%;
                 box-shadow:0 0 6px #1db954;display:inline-block;'></span>
    <span style='font-size:12px;color:#a0dcb4;'>Vista activa:</span>
    <code style='font-size:12px;color:#1db954;background:transparent;'>{nombre_vista_base}</code>
    <span style='font-size:11px;color:rgba(160,220,180,.35);'>· participant_name</span>
</div>
""", unsafe_allow_html=True)

lista = obtener_participantes(base_url, username, password, nombre_vista_base)

if not lista:
    st.warning(
        f"⚠️ No se pudieron cargar participantes de `{nombre_vista_base}`. "
        "Verifica que Denodo está corriendo y que la vista existe."
    )
    lista = ["Competidor A", "Competidor B"]
else:
    st.markdown(f"""<div style='font-size:11px;color:rgba(29,185,84,.55);margin-bottom:10px;'>
        ✓ {len(lista)} participantes cargados desde <code style='color:#1db954;
        background:rgba(29,185,84,.08);padding:1px 5px;border-radius:3px;'>{nombre_vista_base}</code>
    </div>""", unsafe_allow_html=True)

col_a, col_vs, col_b = st.columns([5, 1, 5])

with col_a:
    st.markdown("""<div style='font-family:"Bebas Neue",sans-serif;font-size:12px;
                letter-spacing:.1em;color:rgba(0,200,100,.65);margin-bottom:6px;'>
        ◈ CANDIDATO A — CARTERA VERDE</div>""", unsafe_allow_html=True)
    entidad_a = st.selectbox("Competidor A", lista, key="ea_sel",
                              label_visibility="collapsed")

with col_vs:
    st.markdown("""<div style='display:flex;justify-content:center;align-items:center;
                height:76px;font-family:"Bebas Neue",sans-serif;font-size:36px;
                color:rgba(255,210,0,.65);padding-top:18px;'>VS</div>""",
                unsafe_allow_html=True)

with col_b:
    st.markdown("""<div style='font-family:"Bebas Neue",sans-serif;font-size:12px;
                letter-spacing:.1em;color:rgba(255,100,80,.65);margin-bottom:6px;'>
        ◈ CANDIDATO B — CARTERA ROJA</div>""", unsafe_allow_html=True)
    idx_b     = min(1, len(lista) - 1)
    entidad_b = st.selectbox("Competidor B", lista, index=idx_b, key="eb_sel",
                              label_visibility="collapsed")

st.markdown("---")


# ─────────────────────────────────────────
# BLOQUE 3 — PERFIL DE INVERSIÓN
# ─────────────────────────────────────────
st.markdown("""<div style='font-family:"Bebas Neue",sans-serif;font-size:22px;
            letter-spacing:.12em;color:#1db954;margin-bottom:6px;'>
    ③ PERFIL DE INVERSIÓN
    <span style='font-size:13px;color:rgba(120,180,140,.45);font-family:"DM Sans",sans-serif;
                 letter-spacing:0;font-weight:300;'>(opcional — personaliza tu estrategia de retorno)</span>
</div>""", unsafe_allow_html=True)

st.markdown("""<div style='font-size:12px;color:rgba(160,220,180,.4);margin-bottom:8px;'>
    Como inversor, ¿qué factores priorizas para maximizar tu retorno sobre el talento deportivo?
</div>""", unsafe_allow_html=True)

criterio = st.text_area(
    "perfil",
    placeholder=(
        "Ej: Busco el competidor con mayor consistencia en fases eliminatorias y menor riesgo de "
        "derrota temprana. Priorizo rendimiento sostenido sobre actuaciones aisladas brillantes. "
        "Me interesa el activo con mejor ratio victoria/derrota como garantía de rentabilidad a largo plazo."
    ),
    height=90,
    label_visibility="collapsed"
)

criterio_prompt = (
    criterio.strip() if criterio.strip()
    else (
        "Maximizar retorno de inversión basado en rendimiento deportivo general, "
        "consistencia competitiva, tasa de victorias y menor riesgo de resultados adversos"
    )
)

st.markdown("---")


# ─────────────────────────────────────────
# BOTÓN ANALIZAR
# ─────────────────────────────────────────
_, col_btn, _ = st.columns([2, 5, 2])
with col_btn:
    analizar = st.button("📈 ANALIZAR INVERSIÓN", type="primary", use_container_width=True)


# ─────────────────────────────────────────
# MOTOR DE ANÁLISIS
# ─────────────────────────────────────────
if analizar:
    if entidad_a == entidad_b:
        st.error("⚠️ Selecciona dos competidores distintos para comparar.")
        st.stop()

    ea = limpiar_nombre(entidad_a)
    eb = limpiar_nombre(entidad_b)

    st.markdown("---")
    st.markdown(f"""
    <div style='text-align:center;font-family:"Bebas Neue",sans-serif;font-size:30px;
                letter-spacing:.1em;color:#a8ff78;margin-bottom:10px;'>
        📊 PROCESANDO DUE DILIGENCE DEPORTIVA…
    </div>
    <div style='text-align:center;font-size:13px;color:rgba(160,220,180,.4);margin-bottom:20px;'>
        Vista: <code style='color:#1db954;'>{nombre_vista_base}</code>
        &nbsp;·&nbsp; Comparando: <b>{ea}</b> vs <b>{eb}</b>
    </div>
    """, unsafe_allow_html=True)

    prog   = st.progress(0)
    status = st.empty()

    # ── DETECTOR DE PERFIL INVERSOR ──────────────────────────────────────
    def detectar_perfil(texto: str) -> dict:
        """
        Analiza el texto del criterio y devuelve el perfil de inversión
        con su lógica de scoring y terminología específica.
        """
        t = texto.lower()

        # Palabras clave por perfil
        PERFILES = {
            "riesgo": {
                "keywords": ["riesgo", "risk", "segur", "conservador", "publicitari",
                             "brand", "imagen", "reputaci", "asimétric", "protec",
                             "derrota", "perd", "evit"],
                "nombre":    "Inversor Conservador — Minimización de Riesgo",
                "emoji":     "🛡️",
                "metrica_principal": "tasa_derrota",
                "descripcion_metrica": "menor tasa de derrotas",
                "pesos": {"win_rate": 0.3, "loss_rate_inv": 0.5, "volumen": 0.2},
                "logica": lambda wa, la, ta, wb, lb, tb: (
                    # Gana quien tiene MENOS derrotas (invertido: más alto = mejor)
                    (1 - la/ta), (1 - lb/tb)
                ),
                "template_rec": lambda g, p, sg, sp, dif, wins_g, total_g, rate_g, wins_p, total_p, rate_p, criterio: (
                    f"INVERTIR EN {g.upper()} — PERFIL DE BAJO RIESGO. "
                    f"Con solo una tasa de derrota del {round((1 - rate_g/100)*100, 1):.1f}% "
                    f"frente al {round((1 - rate_p/100)*100, 1):.1f}% de {p}, {g} representa "
                    f"la opción con menor exposición a resultados adversos. "
                    f"Para una inversión publicitaria o de imagen de marca, "
                    f"la probabilidad de asociación con derrotas es {dif:.1f}pp inferior. "
                    f"Riesgo reducido = protección del capital reputacional."
                ),
                "analisis_ganador": lambda e, w, l, t, r: (
                    f"Tasa de derrota del {round(l/t*100, 1):.1f}% — el activo más seguro del mercado. "
                    f"Solo {l} derrotas en {t} encuentros. Bajo riesgo de exposición negativa de marca. "
                    f"Perfil ideal para inversores con aversión al riesgo reputacional."
                ),
                "analisis_perdedor": lambda e, w, l, t, r: (
                    f"Tasa de derrota del {round(l/t*100, 1):.1f}% — riesgo elevado para patrocinio. "
                    f"{l} derrotas en {t} encuentros conllevan mayor probabilidad de exposición negativa. "
                    f"Requiere prima de riesgo adicional para justificar la inversión."
                ),
            },
            "volumen": {
                "keywords": ["audiencia", "exposici", "visibilidad", "mercado", "fans",
                             "seguidor", "volume", "partidos", "presencia", "alcance",
                             "impacto", "mediatico", "mediatica"],
                "nombre":    "Inversor de Audiencia — Maximización de Exposición",
                "emoji":     "📡",
                "metrica_principal": "partidos_jugados",
                "descripcion_metrica": "mayor presencia competitiva",
                "pesos": {"win_rate": 0.3, "volumen": 0.5, "loss_rate_inv": 0.2},
                "logica": lambda wa, la, ta, wb, lb, tb: (
                    # Gana quien juega MÁS partidos (más exposición mediática)
                    max_t := max(ta, tb, 1),
                    ta / max_t * 0.5 + wa/ta * 0.5,
                    tb / max_t * 0.5 + wb/tb * 0.5,
                )[-2:],
                "template_rec": lambda g, p, sg, sp, dif, wins_g, total_g, rate_g, wins_p, total_p, rate_p, criterio: (
                    f"INVERTIR EN {g.upper()} — MÁXIMA EXPOSICIÓN MEDIÁTICA. "
                    f"Con {total_g} encuentros disputados frente a {total_p} de {p}, "
                    f"{g} ofrece {total_g - total_p} apariciones adicionales en medios. "
                    f"Mayor volumen de partidos = mayor retorno en impresiones publicitarias "
                    f"y cobertura mediática. Retorno por exposición superior en {round(total_g/max(total_p,1)*100-100, 1):.1f}%."
                ),
                "analisis_ganador": lambda e, w, l, t, r: (
                    f"Con {t} partidos disputados, ofrece la mayor cobertura mediática disponible. "
                    f"{w} victorias ({r}%) garantizan además un contexto ganador para las marcas patrocinadoras. "
                    f"Activo de alta visibilidad con rendimiento sólido."
                ),
                "analisis_perdedor": lambda e, w, l, t, r: (
                    f"Con {t} partidos, la presencia mediática es más limitada que su rival. "
                    f"Menor volumen de apariciones reduce el potencial de retorno en exposición. "
                    f"Válido para presupuestos de menor escala con objetivos locales."
                ),
            },
            "dominancia": {
                "keywords": ["dominan", "aplast", "superiorid", "top", "mejor",
                             "elite", "premier", "excelenci", "campe", "champion",
                             "maximo", "máximo", "potenci"],
                "nombre":    "Inversor Premium — Activo de Élite",
                "emoji":     "👑",
                "metrica_principal": "ratio_wl",
                "descripcion_metrica": "mayor ratio victorias/derrotas",
                "pesos": {"win_rate": 0.6, "loss_rate_inv": 0.3, "volumen": 0.1},
                "logica": lambda wa, la, ta, wb, lb, tb: (
                    wa / max(la, 0.5),  # ratio W/L, evita div/0
                    wb / max(lb, 0.5)
                ),
                "template_rec": lambda g, p, sg, sp, dif, wins_g, total_g, rate_g, wins_p, total_p, rate_p, criterio: (
                    f"INVERTIR EN {g.upper()} — ACTIVO DE ÉLITE VERIFICADO. "
                    f"Ratio victorias/derrotas de {round(wins_g/max(total_g-wins_g, 0.5), 2):.2f}x "
                    f"frente a {round(wins_p/max(total_p-wins_p, 0.5), 2):.2f}x de {p}. "
                    f"{g} representa el activo premium: máximo rendimiento, "
                    f"máxima asociación con el éxito deportivo. "
                    f"Para posicionamiento de marca en el segmento élite, es la única opción viable."
                ),
                "analisis_ganador": lambda e, w, l, t, r: (
                    f"Ratio W/L de {round(w/max(l, 0.5), 2):.2f}x — rendimiento de élite certificado. "
                    f"{w} victorias vs {l} derrotas: el activo dominante de esta comparativa. "
                    f"Asociación con este competidor proyecta excelencia y liderazgo de marca."
                ),
                "analisis_perdedor": lambda e, w, l, t, r: (
                    f"Ratio W/L de {round(w/max(l, 0.5), 2):.2f}x — por debajo del estándar élite. "
                    f"No alcanza el umbral de dominancia necesario para un posicionamiento premium. "
                    f"Apto para estrategias de nicho o mercados secundarios."
                ),
            },
        }

        # Detectar perfil por keywords
        perfil_detectado = None
        max_matches = 0
        for nombre_perfil, cfg in PERFILES.items():
            matches = sum(1 for kw in cfg["keywords"] if kw in t)
            if matches > max_matches:
                max_matches = matches
                perfil_detectado = nombre_perfil

        # Default: rendimiento general (win rate puro)
        if perfil_detectado is None or max_matches == 0:
            return {
                "nombre":    "Inversor de Rendimiento — Tasa de Victoria",
                "emoji":     "📊",
                "metrica_principal": "tasa_victoria",
                "descripcion_metrica": "mayor tasa de victorias",
                "logica": lambda wa, la, ta, wb, lb, tb: (wa/ta, wb/tb),
                "template_rec": lambda g, p, sg, sp, dif, wins_g, total_g, rate_g, wins_p, total_p, rate_p, criterio: (
                    f"INVERTIR EN {g.upper()}. "
                    f"Con {wins_g} victorias en {total_g} partidos ({rate_g}% de efectividad), "
                    f"supera a {p} ({rate_p}%) en {dif:.1f} puntos porcentuales. "
                    f"Mayor tasa de victoria = menor riesgo = mayor retorno esperado sobre la inversión."
                ),
                "analisis_ganador": lambda e, w, l, t, r: (
                    f"Tasa de victoria del {r}% sobre {t} encuentros — rendimiento superior al rival. "
                    f"Perfil consistente con {w} victorias que justifica la inversión. "
                    f"Activo con retorno esperado positivo según métricas objetivas."
                ),
                "analisis_perdedor": lambda e, w, l, t, r: (
                    f"Tasa de victoria del {r}% sobre {t} encuentros — por debajo del competidor. "
                    f"Las {l} derrotas representan mayor volatilidad en el retorno esperado. "
                    f"Se recomienda como activo secundario o complementario en cartera."
                ),
            }

        return PERFILES[perfil_detectado]


    def llamada_stats(sdk_url, auth, vista, entidad, timeout=90):
        """Una sola llamada por entidad: wins, losses, total."""
        q = (
            f"In the view {vista}, for rows where participant_name = '{entidad}': "
            f"count rows where result_wlt = 'W', "
            f"count rows where result_wlt = 'L', "
            f"and count total rows. "
            f"Reply with exactly three integers separated by commas: wins,losses,total"
        )
        r = requests.post(
            f"{sdk_url}/answerDataQuestion",
            json={"question": q},
            auth=auth,
            timeout=timeout
        )
        r.raise_for_status()
        texto = r.json().get("answer", "")
        nums  = [int(n) for n in re.findall(r'\b(\d+)\b', texto)]
        if len(nums) >= 3:
            w, l, t = nums[0], nums[1], nums[2]
        elif len(nums) == 2:
            w, l, t = nums[0], nums[1], nums[0] + nums[1]
        elif len(nums) == 1:
            w, l, t = nums[0], 0, nums[0]
        else:
            w, l, t = 0, 0, 1
        t = t or (w + l) or 1
        return w, l, t, texto

    auth   = (username, password)
    sdk    = base_url.rstrip('/')
    perfil = detectar_perfil(criterio_prompt)

    try:
        # ── FASE 1: METADATOS ─────────────────────────────
        status.markdown("🔍 **Fase 1/3** — Explorando esquema de la vista…")
        prog.progress(10)
        try:
            meta_r    = requests.post(
                f"{sdk}/answerMetadataQuestion",
                json={"question": f"What columns exist in the view {nombre_vista_base}?"},
                auth=auth, timeout=30
            )
            estrategia = meta_r.json().get("answer", "Schema consultado.")[:200]
        except Exception:
            estrategia = "Schema por defecto."
        prog.progress(20)

        # ── FASE 2: STATS ENTIDAD A ───────────────────────
        status.markdown(f"📊 **Fase 2/3** — Analizando **{ea}** [{perfil['emoji']} {perfil['nombre']}]…")
        wins_a, loss_a, total_a, raw_a = llamada_stats(sdk, auth, nombre_vista_base, ea)
        rate_a = round(wins_a / total_a * 100, 1)
        prog.progress(55)

        # ── FASE 3: STATS ENTIDAD B ───────────────────────
        status.markdown(f"📊 **Fase 3/3** — Analizando **{eb}** [{perfil['emoji']} {perfil['nombre']}]…")
        wins_b, loss_b, total_b, raw_b = llamada_stats(sdk, auth, nombre_vista_base, eb)
        rate_b = round(wins_b / total_b * 100, 1)
        prog.progress(80)

        # ── SCORING BASADO EN PERFIL ──────────────────────
        score_a, score_b = perfil["logica"](wins_a, loss_a, total_a, wins_b, loss_b, total_b)
        ganador_calc  = ea if score_a >= score_b else eb
        perdedor_calc = eb if score_a >= score_b else ea

        wins_g   = wins_a  if ganador_calc == ea else wins_b
        loss_g   = loss_a  if ganador_calc == ea else loss_b
        total_g  = total_a if ganador_calc == ea else total_b
        rate_g   = rate_a  if ganador_calc == ea else rate_b

        wins_p   = wins_b  if ganador_calc == ea else wins_a
        loss_p   = loss_b  if ganador_calc == ea else loss_a
        total_p  = total_b if ganador_calc == ea else total_a
        rate_p   = rate_b  if ganador_calc == ea else rate_a

        diferencia_rate = abs(rate_a - rate_b)
        diferencia_score = abs(score_a - score_b)

        # Textos de análisis diferenciados por perfil
        analisis_a_txt = (
            perfil["analisis_ganador"](ea, wins_a, loss_a, total_a, rate_a)
            if ganador_calc == ea else
            perfil["analisis_perdedor"](ea, wins_a, loss_a, total_a, rate_a)
        )
        analisis_b_txt = (
            perfil["analisis_ganador"](eb, wins_b, loss_b, total_b, rate_b)
            if ganador_calc == eb else
            perfil["analisis_perdedor"](eb, wins_b, loss_b, total_b, rate_b)
        )

        recomendacion_txt = perfil["template_rec"](
            ganador_calc, perdedor_calc,
            score_a if ganador_calc == ea else score_b,
            score_b if ganador_calc == ea else score_a,
            diferencia_rate,
            wins_g, total_g, rate_g,
            wins_p, total_p, rate_p,
            criterio_prompt
        )

        ratio_txt = (
            f"{perfil['emoji']} Métrica clave: {perfil['descripcion_metrica']} · "
            f"{ganador_calc} {round(score_a if ganador_calc == ea else score_b, 3):.3f} "
            f"vs {perdedor_calc} {round(score_b if ganador_calc == ea else score_a, 3):.3f}"
        )

        justif_txt = (
            f"Perfil detectado: «{perfil['nombre']}». "
            f"Bajo este criterio, la métrica determinante es {perfil['descripcion_metrica']}. "
            f"{ganador_calc} obtiene un score de {round(score_a if ganador_calc == ea else score_b, 3):.3f} "
            f"frente al {round(score_b if ganador_calc == ea else score_a, 3):.3f} de {perdedor_calc}. "
            f"El ganador cambia respecto al simple win-rate si el perfil prioriza métricas distintas."
        )

        datos_ia = {
            "entidad_a": {
                "nombre": ea,
                "stats": f"{wins_a}W · {loss_a}L · {total_a} partidos · {rate_a}%",
                "metricas": {
                    "victorias":     wins_a,
                    "derrotas":      loss_a,
                    "total_partidos": total_a,
                    "tasa_victoria": f"{rate_a}%",
                    f"score_{perfil['metrica_principal']}": round(score_a, 3),
                },
                "valoracion_inversion": analisis_a_txt,
            },
            "entidad_b": {
                "nombre": eb,
                "stats": f"{wins_b}W · {loss_b}L · {total_b} partidos · {rate_b}%",
                "metricas": {
                    "victorias":     wins_b,
                    "derrotas":      loss_b,
                    "total_partidos": total_b,
                    "tasa_victoria": f"{rate_b}%",
                    f"score_{perfil['metrica_principal']}": round(score_b, 3),
                },
                "valoracion_inversion": analisis_b_txt,
            },
            "decision_inversion":  ganador_calc,
            "ratio_comparativo":   ratio_txt,
            "justificacion_perfil": justif_txt,
            "recomendacion_final": recomendacion_txt,
        }

        resultado_raw = {"raw_a": raw_a, "raw_b": raw_b}
        prog.progress(100)
        status.markdown("✅ **Due diligence completada**")

        # Extraer campos
        nombre_a   = limpiar_nombre(datos_ia.get("entidad_a", {}).get("nombre", ea))
        stats_a    = datos_ia.get("entidad_a", {}).get("stats", "—")
        analisis_a = datos_ia.get("entidad_a", {}).get("valoracion_inversion", "")
        metricas_a = datos_ia.get("entidad_a", {}).get("metricas", {})

        nombre_b   = limpiar_nombre(datos_ia.get("entidad_b", {}).get("nombre", eb))
        stats_b    = datos_ia.get("entidad_b", {}).get("stats", "—")
        analisis_b = datos_ia.get("entidad_b", {}).get("valoracion_inversion", "")
        metricas_b = datos_ia.get("entidad_b", {}).get("metricas", {})

        decision   = limpiar_nombre(datos_ia.get("decision_inversion", "—"))
        ratio      = datos_ia.get("ratio_comparativo", "")
        justif     = datos_ia.get("justificacion_perfil", "")
        recomend   = datos_ia.get("recomendacion_final", "No disponible.")

        # ── CABECERA VS ───────────────────────────────────
        st.markdown("---")
        # Badge de perfil detectado
        st.markdown(f"""
        <div style='text-align:center;margin-bottom:16px;'>
            <span style='display:inline-block;background:rgba(29,185,84,.1);
                         border:1px solid rgba(29,185,84,.3);border-radius:20px;
                         padding:6px 18px;font-size:12px;color:#1db954;letter-spacing:.08em;'>
                {perfil['emoji']} PERFIL DETECTADO: {perfil['nombre'].upper()}
                &nbsp;·&nbsp; Métrica clave: <b>{perfil['descripcion_metrica']}</b>
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style='text-align:center;font-family:"Bebas Neue",sans-serif;
                    font-size:52px;letter-spacing:.05em;margin-bottom:24px;'>
            <span style='color:#00c864;'>{nombre_a.upper()}</span>
            <span style='color:#ffd060;margin:0 22px;
                         text-shadow:0 0 30px rgba(255,208,0,.5);'>VS</span>
            <span style='color:#ff6450;'>{nombre_b.upper()}</span>
        </div>
        """, unsafe_allow_html=True)

        # ── TARJETAS ──────────────────────────────────────
        col_l, col_c, col_r = st.columns([5, 1, 5])

        def pills_html(metricas: dict, bg: str, border: str, text: str) -> str:
            out = ""
            for k, v in metricas.items():
                if v is not None:
                    out += (
                        f"<span style='display:inline-block;background:{bg};"
                        f"border:1px solid {border};border-radius:20px;"
                        f"padding:3px 11px;font-size:11px;color:{text};margin:2px;font-weight:600;'>"
                        f"{k.replace('_',' ').title()}: {v}</span>"
                    )
            return out

        with col_l:
            p = pills_html(metricas_a,
                           "rgba(0,200,100,.1)", "rgba(0,200,100,.25)", "#64dcb4")
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,rgba(0,200,100,.1),rgba(0,80,40,.04));
                        border:1px solid rgba(0,200,100,.25);border-radius:14px;
                        padding:22px 24px;min-height:270px;'>
                <div style='font-family:"Bebas Neue",sans-serif;font-size:14px;
                            letter-spacing:.1em;color:#00c864;margin-bottom:6px;'>
                    ◈ {nombre_a.upper()}
                </div>
                <div style='font-family:"Bebas Neue",sans-serif;font-size:22px;
                            color:#fff;margin-bottom:12px;line-height:1.25;'>{stats_a}</div>
                <div style='display:flex;flex-wrap:wrap;gap:4px;margin-bottom:14px;'>{p}</div>
                <div style='font-size:13px;color:#a0e8c0;line-height:1.65;
                            border-top:1px solid rgba(0,200,100,.12);padding-top:12px;'>
                    {analisis_a}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_c:
            st.markdown("""<div style='display:flex;justify-content:center;align-items:center;
                        min-height:270px;font-family:"Bebas Neue",sans-serif;font-size:28px;
                        color:rgba(255,208,0,.45);'>VS</div>""", unsafe_allow_html=True)

        with col_r:
            p = pills_html(metricas_b,
                           "rgba(255,100,80,.1)", "rgba(255,100,80,.25)", "#ff9080")
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,rgba(255,100,80,.1),rgba(120,20,10,.04));
                        border:1px solid rgba(255,100,80,.25);border-radius:14px;
                        padding:22px 24px;min-height:270px;'>
                <div style='font-family:"Bebas Neue",sans-serif;font-size:14px;
                            letter-spacing:.1em;color:#ff6450;margin-bottom:6px;'>
                    ◈ {nombre_b.upper()}
                </div>
                <div style='font-family:"Bebas Neue",sans-serif;font-size:22px;
                            color:#fff;margin-bottom:12px;line-height:1.25;'>{stats_b}</div>
                <div style='display:flex;flex-wrap:wrap;gap:4px;margin-bottom:14px;'>{p}</div>
                <div style='font-size:13px;color:#ffb8a8;line-height:1.65;
                            border-top:1px solid rgba(255,100,80,.12);padding-top:12px;'>
                    {analisis_b}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── VEREDICTO ─────────────────────────────────────
        st.markdown("---")

        if decision and decision != "—":
            st.markdown(f"""
            <div style='text-align:center;background:linear-gradient(135deg,
                        rgba(255,208,0,.08),rgba(255,160,0,.03));
                        border:1px solid rgba(255,208,0,.22);border-radius:16px;
                        padding:30px;margin-bottom:20px;'>
                <div style='font-family:"Bebas Neue",sans-serif;font-size:13px;
                            letter-spacing:.22em;color:rgba(255,208,0,.45);margin-bottom:10px;'>
                    VEREDICTO DE INVERSIÓN
                </div>
                <div style='font-family:"Bebas Neue",sans-serif;font-size:54px;
                            letter-spacing:.04em;color:#ffd060;
                            text-shadow:0 0 40px rgba(255,208,0,.3);margin-bottom:10px;'>
                    💰 {decision.upper()}
                </div>
                {f'<div style="font-size:14px;color:rgba(255,208,0,.55);">{ratio}</div>' if ratio else ''}
            </div>
            """, unsafe_allow_html=True)

        # ── PERFIL APLICADO ───────────────────────────────
        if justif:
            st.markdown(f"""
            <div style='background:rgba(29,185,84,.05);border:1px solid rgba(29,185,84,.16);
                        border-radius:10px;padding:14px 18px;margin-bottom:16px;'>
                <div style='font-size:10px;letter-spacing:.15em;
                            color:rgba(29,185,84,.45);margin-bottom:6px;'>
                    PERFIL DE INVERSIÓN APLICADO
                </div>
                <div style='font-size:12px;color:rgba(160,220,180,.4);
                            font-style:italic;margin-bottom:8px;'>
                    «{criterio_prompt[:130]}{'…' if len(criterio_prompt) > 130 else ''}»
                </div>
                <div style='font-size:14px;color:#a8e8c0;line-height:1.65;'>{justif}</div>
            </div>
            """, unsafe_allow_html=True)

        # ── RECOMENDACIÓN FINAL ───────────────────────────
        st.markdown("""<div style='font-family:"Bebas Neue",sans-serif;font-size:22px;
                    letter-spacing:.1em;color:#1db954;margin-bottom:10px;'>
            📋 RECOMENDACIÓN DE INVERSIÓN</div>""", unsafe_allow_html=True)
        st.success(recomend)

        # ── EXPANDIBLES ───────────────────────────────────
        with st.expander("🔬 Fase 1 — Esquema consultado"):
            st.markdown(f"**Respuesta del Data Marketplace:** {estrategia}")
            st.markdown(f"**Campos utilizados:** `result_wlt`, `participant_name`")

        with st.expander("🤖 Respuestas brutas del SDK (debug)"):
            st.markdown(f"**{ea}:** `{resultado_raw['raw_a'][:300]}`")
            st.markdown(f"**{eb}:** `{resultado_raw['raw_b'][:300]}`")

    except Exception as e:
        prog.progress(0)
        status.empty()
        st.error(f"❌ Error al conectar con el SDK de Denodo: {e}")
        st.markdown(f"""
        <div style='background:rgba(255,80,60,.07);border:1px solid rgba(255,80,60,.2);
                    border-radius:10px;padding:16px 20px;font-size:13px;
                    color:#ffaaaa;margin-top:8px;'>
            <b>💡 Diagnóstico:</b><br>
            • <b>Read timed out</b> → Aumenta el timeout o usa un modelo más rápido.<br>
            • Vista consultada: <code>{nombre_vista_base}</code><br>
            • Participante A: <code>{ea}</code> · Participante B: <code>{eb}</code>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center;padding:20px 0;'>
    <div style='font-size:22px;margin-bottom:8px;'>💹 🏅 💹</div>
    <div style='font-size:11px;color:rgba(120,180,140,.28);letter-spacing:.12em;'>
        HackUDC 2026 · OLYMPIC INVESTOR · Powered by Denodo AI SDK · París 2024
    </div>
</div>
""", unsafe_allow_html=True)