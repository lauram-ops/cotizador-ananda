# -*- coding: utf-8 -*-
"""
Ananda Kino — Herramienta de venta (mercado + plusvalía + rentas + cotización)
-------------------------------------------------------------------------------
A diferencia del cotizador oficial (solo condiciones de compra), esta app
incluye argumentos de venta: comparativa contra el mercado, proyección de
plusvalía por lista de precios, y un simulador de rentas ajustable. El PDF
que genera se lo puede llevar el cliente.

Estructura del repositorio esperada:
    app.py              (este archivo)
    requirements.txt
    logo.png            (logo de Ananda, fondo transparente)
"""

import base64
import math
from datetime import date, datetime

import streamlit as st
from fpdf import FPDF

with open("logo.png", "rb") as _f:
    LOGO_B64 = base64.b64encode(_f.read()).decode("ascii")

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(page_title="Ananda Kino | Preventa", page_icon="💎", layout="wide")

BRAND = "#4D6D80"
LOGO_C = "#658597"
SOFT = "#E9F0F3"
INK = "#16232C"
MUTED = "#5C6D78"
LINE = "#DDE5EA"
DARK = "#2E4B5E"  # énfasis fuerte (precio final, cifras clave)
MED = "#7F9CAB"   # énfasis medio
LIGHT = "#B7C7CE" # barras secundarias / comparación

st.markdown(f"""
<style>
.stApp {{ background: #F3F6F8; }}
.badge-lista {{
    display:inline-block; background:{BRAND}; color:#fff; font-weight:800;
    font-size:15px; letter-spacing:.5px; padding:5px 14px; border-radius:8px;
}}
.section-title {{
    background:{SOFT}; padding:12px 16px; border-radius:8px; border-left:6px solid {BRAND};
    color:{BRAND}; font-size:19px; font-weight:800; margin:22px 0 14px;
}}
.fin-card {{
    background:#fff; padding:12px; border-radius:10px; border:1px solid {LINE};
    text-align:center; height:100%;
}}
.fin-label {{ font-size:11px; color:{MUTED}; text-transform:uppercase; letter-spacing:.8px; margin-bottom:5px; }}
.fin-val {{ font-size:19px; font-weight:900; color:{BRAND}; }}
.fin-discount {{ font-size:17px; font-weight:700; color:{INK}; }}
.fin-final {{ font-size:20px; font-weight:900; color:{DARK}; }}
.fin-future {{ font-size:19px; font-weight:900; color:{MED}; }}
.house-box {{ background:{SOFT}; border-radius:10px; padding:14px 16px; margin-bottom:10px; }}
.house-t {{ font-weight:700; color:{INK}; }}
.house-s {{ font-size:13px; color:{MUTED}; margin-top:3px; }}
.chip {{ display:inline-block; background:#E3F2FD; color:{BRAND}; padding:6px 12px;
         border-radius:15px; font-weight:700; font-size:13px; margin:3px; }}
.disclaimer {{ font-size:12px; color:{MUTED}; border-top:1px solid {LINE}; padding-top:8px; margin-top:10px; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# DATOS DEL PROYECTO — LISTA DE PRECIOS 2 (vigente desde el 18-sep-2026)
# ==============================================================================
# desplante = m² de planta baja del prototipo (Memorándum Ananda): A = 82.04, C = 74.12
GRUPOS = [
    # (desde, hasta, priv, terreno, constr, precio, activo, desplante)
    (1,  4,  147, 239.32, 128.8, 3518249, False, 82.04),
    (5,  11, 161, 262.11, 128.8, 3518249, False, 82.04),
    (23, 29, 161, 262.11, 128.8, 3518249, True,  82.04),
    (30, 33, 147, 239.32, 128.8, 3460569, True,  82.04),
    (34, 37, 133, 216.53, 120.8, 3299724, True,  74.12),
    (38, 44, 161, 262.11, 128.8, 3518249, True,  82.04),
]
VENDIDOS = {23, 29, 44}
VENTAS_POR_LISTA = 3
INCREMENTO_SIGUIENTE = 1.03
LISTA_TXT = "Lista de precios 2 (septiembre 2026)"
LISTA_BADGE = "LISTA 2 · SEP 2026"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def entrega_de(n):
    if 23 <= n <= 33:
        return {"txt": "septiembre 2027", "y": 2027, "m": 9}
    if (34 <= n <= 44) or (1 <= n <= 11):
        return {"txt": "marzo 2028", "y": 2028, "m": 3}
    return {"txt": "septiembre 2028", "y": 2028, "m": 9}


LOTES = {}
for desde, hasta, priv, terreno, constr, precio, activo, desplante in GRUPOS:
    for n in range(desde, hasta + 1):
        LOTES[n] = {
            "n": n, "priv": priv, "terreno": terreno, "constr": constr,
            "patio": round(priv - desplante, 2), "precio": precio, "activo": activo,
            "vendido": n in VENDIDOS, "entrega": entrega_de(n),
        }

MATRIZ = {
    95: [10.5, 10.5, 10.5, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.75, 6.5, 6.25],
    90: [9.5, 9.5, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.75, 5.5, 5.25],
    80: [8.5, 8.5, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.75, 4.5, 4.25],
    70: [7.5, 7.5, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.75, 3.5, 3.25],
    60: [6.5, 6.5, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3, 2.75, 2.5, 2.25],
    50: [5.5, 5.5, 5.5, 5, 4.5, 4, 3.5, 3, 2.5, 2, 1.75, 1.5, 1.25],
    40: [4.5, 4.5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.25],
    30: [3.5, 3.5, 3.5, 3, 2.5, 2, 1.5, 1, 0.5],
    25: [2.5, 2.5, 2.5, 2, 1.5, 1, 0.5],
    20: [2, 2, 2, 1.5, 1, 0.5],
    15: [1.5, 1.5, 1.5, 1, 0.5],
}
ENGANCHES = [15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 95]

ACABADOS_TXT = ("Se entrega con pisos, closets, carpintería de cocina con barra de granito, "
                "horno, campana, parrilla eléctrica y cancelería.")

# Competencia — presentación interna del 12-ago-2026 ($/m² sobre m² de construcción)
COMPETENCIA = [
    ("Altarena Zaah", 45643), ("Altarena Hail", 45643), ("Altarena Hamac", 45455),
    ("Azaluma", 45038), ("Caay MC", 38393), ("Caay MA", 38679), ("Caay MB", 38776),
    ("Hax 1", 48571), ("Hax 2", 48571), ("Marenza A", 60347), ("Marenza B", 44784),
    ("P. Península", 40762),
]
PROMEDIO_MERCADO_M2 = 43589


def money(n):
    return "${:,.0f}".format(n)


def m2_txt(n):
    return f"{n:g} m²"


def fecha_larga(d):
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def obtener_descuento(enganche, plazo):
    fila = MATRIZ.get(enganche, [])
    if 1 <= plazo <= len(fila):
        return fila[plazo - 1]
    return None


def escalon_lista(precio_lista2, listas_adelante):
    """Precio de lista en N listas más adelante, a partir de la Lista 2 vigente."""
    p = precio_lista2
    for _ in range(listas_adelante):
        p = round(p * INCREMENTO_SIGUIENTE)
    return p


# ==============================================================================
# BARRA LATERAL
# ==============================================================================
st.sidebar.image("logo.png", use_container_width=True)
st.sidebar.markdown(f'<span class="badge-lista">{LISTA_BADGE}</span>', unsafe_allow_html=True)
st.sidebar.markdown("### Datos de la cotización")

cliente = st.sidebar.text_input("Cliente", value="")
asesor = st.sidebar.text_input("Asesor", value="")
fecha_cot = st.sidebar.date_input("Fecha", value=date.today(), format="DD/MM/YYYY")

st.sidebar.markdown("---")
st.sidebar.markdown("**1. Propiedad**")

lotes_activos = [n for n in sorted(LOTES) if LOTES[n]["activo"] and not LOTES[n]["vendido"]]
if not lotes_activos:
    st.error("No hay lotes disponibles para la venta en este momento.")
    st.stop()


def fmt_lote(n):
    l = LOTES[n]
    txt = l["entrega"]["txt"].replace("septiembre 20", "sep ").replace("marzo 20", "mar ")
    return f'Lote {n} · {l["priv"]:g} m² · {money(l["precio"])} · {txt}'


lote_sel = st.sidebar.selectbox("Lote (disponible)", lotes_activos, format_func=fmt_lote, index=0)
lote = LOTES[lote_sel]

st.sidebar.markdown("**2. Forma de pago**")
enganche_pct = st.sidebar.select_slider("% Enganche", options=ENGANCHES, value=30)
plazo_meses = st.sidebar.selectbox("Plazo enganche (meses)", list(range(1, 14)), index=5)

if "last_lote" not in st.session_state:
    st.session_state.last_lote = None
if st.session_state.last_lote != lote_sel:
    st.session_state.fliq = lote["entrega"]["txt"]
    st.session_state.last_lote = lote_sel
fliq = st.sidebar.text_input("Fecha estimada de liquidación", key="fliq")
fliq_txt = fliq.strip() or lote["entrega"]["txt"]

st.sidebar.markdown("---")
st.sidebar.markdown("**3. Simulador de rentas (opcional, ajustable)**")
tarifa_noche = st.sidebar.number_input("Tarifa por noche ($)", value=4500, step=250)
ocupacion_pct = st.sidebar.slider("Ocupación anual (%)", 20, 80, 45)
admin_pct = st.sidebar.slider("Comisión de administración (%)", 15, 30, 25)
gastos_fijos_mes = st.sidebar.number_input("Gastos fijos mensuales ($)", value=3000, step=250)

# ==============================================================================
# CÁLCULOS
# ==============================================================================
descuento_pct = obtener_descuento(enganche_pct, plazo_meses)
hay_desc = descuento_pct is not None
descuento_pct_val = descuento_pct or 0.0

precio_lista = lote["precio"]
monto_descuento = round(precio_lista * descuento_pct_val / 100)
precio_final = precio_lista - monto_descuento
monto_enganche = round(precio_final * enganche_pct / 100)
saldo_final = precio_final - monto_enganche

base_pago = monto_enganche // plazo_meses
pagos = [base_pago] * plazo_meses
pagos[-1] = monto_enganche - base_pago * (plazo_meses - 1)

precio_m2_ananda = precio_lista / lote["constr"]
precio_lista10 = escalon_lista(precio_lista, 8)  # Lista 2 -> Lista 10 = 8 incrementos
plusvalia_lista10 = precio_lista10 - precio_lista

ingreso_bruto = tarifa_noche * 365 * (ocupacion_pct / 100)
gasto_admin = ingreso_bruto * (admin_pct / 100)
gasto_servicios = gastos_fijos_mes * 12
total_gastos = gasto_admin + gasto_servicios
utilidad_neta = ingreso_bruto - total_gastos
roi_pct = (utilidad_neta / precio_final * 100) if precio_final else 0

# ==============================================================================
# CUERPO PRINCIPAL
# ==============================================================================
st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">'
    f'<h1 style="margin:0;color:{INK}">💎 Preventa Ananda · Lote {lote["n"]}</h1>'
    f'<span class="badge-lista">{LISTA_BADGE}</span></div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">1. 44 casas en Bahía Kino</div>', unsafe_allow_html=True)
chips = ["🛏️ 3 Recámaras", "🚿 2.5 Baños", "🚗 Doble cochera", "🍳 Cocina equipada",
         "👕 Closets", "🪟 Cancelería", "✨ Pisos incluidos"]
st.markdown("".join(f'<span class="chip">{c}</span>' for c in chips), unsafe_allow_html=True)
st.markdown(
    f'<div class="house-box" style="margin-top:10px">'
    f'<div class="house-t">Lote {lote["n"]} · Privativo {m2_txt(lote["priv"])} · Construcción {m2_txt(lote["constr"])} · '
    f'Patio {m2_txt(lote["patio"])}</div>'
    f'<div class="house-s">Terreno total {m2_txt(lote["terreno"])} · Entrega estimada: {lote["entrega"]["txt"]}</div>'
    f'<div class="house-s">{ACABADOS_TXT}</div></div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">2. Ananda vs el mercado</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="fin-card"><div class="fin-label">Precio de lista</div>'
                f'<div class="fin-val">{money(precio_lista)}</div></div>', unsafe_allow_html=True)
with c2:
    label = f"Tu descuento ({descuento_pct_val:g}%)" if hay_desc else "Tu descuento (sin combinación válida)"
    st.markdown(f'<div class="fin-card"><div class="fin-label">{label}</div>'
                f'<div class="fin-discount">-{money(monto_descuento)}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="fin-card" style="border:2px solid {DARK}"><div class="fin-label">Precio final</div>'
                f'<div class="fin-final">{money(precio_final)}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="fin-card"><div class="fin-label">Precio en Lista 10 (44/44 vendidas)</div>'
                f'<div class="fin-future">{money(precio_lista10)}</div></div>', unsafe_allow_html=True)

st.markdown(f"#### 🏷️ Tu precio por m² (sobre precio de lista): **{money(precio_m2_ananda)}**")
st.caption("El precio de la competencia es el de lista (sin descuento), para comparar en igualdad de condiciones.")

comp_rows = [("Ananda", precio_m2_ananda)] + COMPETENCIA
try:
    import plotly.graph_objects as go
    fig = go.Figure(go.Bar(
        x=[r[0] for r in comp_rows], y=[r[1] for r in comp_rows],
        marker_color=[DARK if r[0] == "Ananda" else LIGHT for r in comp_rows],
        text=[f"${r[1]:,.0f}" for r in comp_rows], textposition="outside",
    ))
    fig.add_hline(y=PROMEDIO_MERCADO_M2, line_dash="dot", line_color=MUTED,
                  annotation_text=f"Promedio mercado {money(PROMEDIO_MERCADO_M2)}/m²")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="$/m²", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
except ImportError:
    st.table({"Proyecto": [r[0] for r in comp_rows], "$/m²": [money(r[1]) for r in comp_rows]})
st.caption("Ventajas: precio por m² más bajo, privacidad (sin vecinos arriba/abajo), doble cochera, "
           "mantenimiento bajo, dueño de tierra + casa. Datos de competencia: presentación interna del 12-ago-2026.")

st.markdown('<div class="section-title">3. Proyección de plusvalía (Lista 2 → Lista 10)</div>', unsafe_allow_html=True)
listas_lbl = [f"Lista {i}" for i in range(2, 11)]
listas_val = [escalon_lista(precio_lista, i - 2) for i in range(2, 11)]
try:
    import plotly.graph_objects as go
    fig2 = go.Figure(go.Bar(
        x=listas_lbl, y=listas_val,
        marker_color=[DARK] + [LIGHT] * (len(listas_val) - 1),
        text=[money(v) for v in listas_val], textposition="outside",
    ))
    fig2.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="Precio de lista", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)
except ImportError:
    st.table({"Lista": listas_lbl, "Precio": [money(v) for v in listas_val]})

pct_plus = plusvalia_lista10 / precio_lista * 100
mcol1, mcol2 = st.columns(2)
mcol1.metric("Plusvalía a Lista 10", money(plusvalia_lista10), f"+{pct_plus:.1f}% vs. hoy")
mcol2.metric("Precio en Lista 10", money(precio_lista10))
st.caption("Con base en el incremento real de 3% entre cada lista de precios, documentado en la lista oficial "
           "vigente. No es una proyección de mercado.")

st.markdown('<div class="section-title">4. Simulador de negocio (rentas — estimado, ajustable)</div>', unsafe_allow_html=True)
r1, r2, r3 = st.columns(3)
r1.metric("Ingreso bruto anual (estimado)", money(ingreso_bruto))
r2.metric("Gastos totales (estimado)", f"-{money(total_gastos)}")
r3.metric("Utilidad neta (estimada)", money(utilidad_neta), f"ROI {roi_pct:.1f}%")
st.caption("Cifras estimadas con la tarifa, ocupación y gastos que ajustes en la barra lateral. No son un "
           "rendimiento garantizado; ajústalas según la evidencia real de la zona antes de presentarlas.")

st.markdown('<div class="section-title">5. Plan de inversión</div>', unsafe_allow_html=True)
p1, p2 = st.columns(2)
with p1:
    st.markdown(f'<div class="fin-card" style="border-top:4px solid {BRAND}"><div class="fin-label">'
                f'Enganche total ({enganche_pct}%)</div><div class="fin-val">{money(monto_enganche)}</div>'
                f'<div class="house-s">A pagar en {plazo_meses} meses</div></div>', unsafe_allow_html=True)
with p2:
    st.markdown(f'<div class="fin-card" style="border-top:4px solid {INK}"><div class="fin-label">'
                f'Liquidación final</div><div class="fin-val">{money(saldo_final)}</div>'
                f'<div class="house-s">Entrega estimada: {fliq_txt}</div></div>', unsafe_allow_html=True)

if not hay_desc:
    st.warning("Esta combinación de enganche y plazo no tiene descuento en la tabla vigente. Confírmala antes de ofrecerla.")

with st.expander("📅 Desglose de mensualidades"):
    st.table({"Mes": list(range(1, plazo_meses + 1)), "Monto": [money(p) for p in pagos]})

faltan = []
if not cliente.strip():
    faltan.append("cliente")
if not asesor.strip():
    faltan.append("asesor")
puede_descargar = not faltan
if faltan:
    st.info("Para descargar falta: " + " y ".join(faltan) + ".")


# ==============================================================================
# GENERADOR DE PDF
# ==============================================================================
def nombre_archivo():
    import re
    c = re.sub(r"[^A-Za-z0-9]+", "_", cliente.strip()).strip("_")
    return f"Cotizacion_Ananda_Kino_Lote{lote['n']}" + (f"_{c}" if c else "") + ".pdf"


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def crear_pdf():
    pdf = FPDF(format="Letter")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    W = pdf.w
    M = 18
    R = W - M

    blue = hexrgb(BRAND)
    ink = hexrgb(INK)
    gray = hexrgb(MUTED)
    line = hexrgb(LINE)
    soft = hexrgb(SOFT)
    dark = hexrgb(DARK)
    med = hexrgb(MED)

    def encabezado(subtitulo):
        pdf.image("logo.png", M, 9, 50)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*ink)
        pdf.set_xy(M, 10)
        pdf.cell(R - M, 6, "COTIZACION PREVENTA", align="R")
        pdf.set_fill_color(*blue)
        pdf.rect(R - 56, 16, 56, 9.5, style="F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_xy(R - 56, 18.6)
        pdf.cell(56, 5, "LISTA 2 - SEP 2026", align="C")
        pdf.set_text_color(*gray)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_xy(M, 26)
        pdf.cell(R - M, 5, subtitulo, align="R")
        pdf.set_draw_color(*hexrgb(LOGO_C))
        pdf.set_line_width(0.8)
        pdf.line(M, 31, R, 31)
        pdf.set_xy(M, 36)

    def salto_si_falta(alto):
        if pdf.get_y() + alto > 272:
            pdf.add_page()
            encabezado("Argumentos de venta (continuación)")

    def titulo(txt):
        salto_si_falta(14)
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*blue)
        pdf.cell(0, 7, txt, new_x="LMARGIN", new_y="NEXT")

    def fila(label, val, strong=False, color=None):
        rh = 8 if not strong else 9
        salto_si_falta(rh)
        w = R - M
        x0, y0 = M, pdf.get_y()
        if strong:
            pdf.set_fill_color(*soft)
            pdf.rect(x0, y0, w, rh, style="F")
        pdf.set_draw_color(*line)
        pdf.set_line_width(0.25)
        pdf.line(x0, y0 + rh, x0 + w, y0 + rh)
        pdf.set_font("Helvetica", "B" if strong else "", 11.5 if strong else 10)
        pdf.set_text_color(*(color or ink))
        pdf.set_xy(x0 + 2, y0 + 1.2)
        pdf.cell(w - 62, rh - 2, label)
        pdf.set_xy(x0 + w - 60, y0 + 1.2)
        pdf.cell(58, rh - 2, val, align="R")
        pdf.set_xy(x0, y0 + rh)

    # ---------- PÁGINA 1: cotización ----------
    encabezado("44 casas - Kino Nuevo, Bahia de Kino, Sonora - www.anandakino.mx")

    for k, v, x in [("CLIENTE", cliente or "-", M), ("ASESOR", asesor or "-", M + 78),
                    ("FECHA", fecha_larga(fecha_cot), M + 128)]:
        pdf.set_xy(x, 40)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*gray)
        pdf.cell(46, 5, k)
        pdf.set_xy(x, 46)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*ink)
        pdf.cell(72 if k == "CLIENTE" else 46, 6, str(v)[:38])

    y = 56
    pdf.set_fill_color(*soft)
    pdf.rect(M, y, R - M, 38, style="F")
    pdf.set_xy(M + 5, y + 4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*ink)
    pdf.cell(0, 6, f"Lote {lote['n']} - 3 recamaras - 2.5 banos - Doble cochera")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*gray)
    pdf.set_xy(M + 5, y + 11)
    pdf.cell(0, 5, f"Privativo {lote['priv']:g} m2 - Construccion {lote['constr']:g} m2 - Patio {lote['patio']:g} m2")
    pdf.set_xy(M + 5, y + 17)
    pdf.cell(0, 5, f"Terreno total {lote['terreno']:g} m2 - Entrega estimada: {lote['entrega']['txt']}")
    pdf.set_xy(M + 5, y + 23)
    pdf.multi_cell(R - M - 10, 5, "Se entrega con pisos, closets, carpinteria de cocina con barra de granito, "
                                    "horno, campana, parrilla electrica y canceleria.")

    pdf.set_xy(M, y + 40)
    titulo("CONDICIONES ECONOMICAS - LISTA DE PRECIOS 2")
    fila("Precio de lista", money(precio_lista))
    desc_lbl = f"Descuento por enganche y plazo ({descuento_pct_val:g}%)" if hay_desc else \
        "Descuento por enganche y plazo (sin descuento en esta combinacion)"
    fila(desc_lbl, ("-" + money(monto_descuento)) if hay_desc else "$0")
    fila("Precio final", money(precio_final), strong=True, color=dark)
    fila(f"Enganche ({enganche_pct}% del precio final)", money(monto_enganche))
    fila("Saldo a liquidar", money(saldo_final))

    titulo("PLAN DE PAGO DEL ENGANCHE")
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(*ink)
    if plazo_meses == 1:
        resumen = f"1 pago de {money(pagos[-1])}"
    elif base_pago == pagos[-1]:
        resumen = f"{plazo_meses} pagos mensuales de {money(base_pago)}"
    else:
        resumen = f"{plazo_meses} pagos mensuales de {money(base_pago)} (el ultimo de {money(pagos[-1])})"
    pdf.cell(0, 6, resumen, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(R - M, 5.5, f"Saldo de {money(saldo_final)}. Fecha estimada de liquidacion: {fliq_txt}. "
                                "El saldo se cubre con recursos propios o con credito hipotecario a traves de "
                                "brokers aliados, sujeto a aprobacion de la institucion financiera.")

    # ---------- PÁGINA 2: argumentos de venta ----------
    pdf.add_page()
    encabezado("Argumentos de venta")

    titulo("ANANDA VS EL MERCADO ($/m2 sobre precio de lista)")
    pdf.set_font("Helvetica", "", 10)
    for nombre, valor in comp_rows:
        strong = nombre == "Ananda"
        fila(nombre, f"${valor:,.0f}/m2", strong=strong, color=dark if strong else None)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*gray)
    pdf.multi_cell(R - M, 5, f"Promedio de mercado: ${PROMEDIO_MERCADO_M2:,.0f}/m2. Ventajas de Ananda: precio por "
                              "m2 mas bajo, privacidad (sin vecinos arriba/abajo), doble cochera, mantenimiento "
                              "bajo, dueno de tierra + casa. Datos de competencia: presentacion interna del "
                              "12-ago-2026.")

    titulo("PROYECCION DE PLUSVALIA (LISTA 2 A LISTA 10)")
    pdf.set_font("Helvetica", "", 10)
    for lbl, val in zip(listas_lbl, listas_val):
        fila(lbl, money(val), strong=(lbl == "Lista 10"), color=dark if lbl == "Lista 10" else None)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*dark)
    pdf.cell(0, 6, f"Plusvalia estimada a Lista 10: +{money(plusvalia_lista10)} (+{pct_plus:.1f}%)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*gray)
    pdf.multi_cell(R - M, 5, "Con base en el incremento real de 3% entre cada lista de precios, documentado en "
                              "la lista oficial vigente. La lista cambia cada 3 ventas.")

    titulo("SIMULADOR DE NEGOCIO (RENTAS) - ESTIMADO, NO GARANTIZADO")
    pdf.set_font("Helvetica", "", 10)
    fila(f"Tarifa {money(tarifa_noche)}/noche - Ocupacion {ocupacion_pct}%", "")
    fila("Ingreso bruto anual (estimado)", money(ingreso_bruto))
    fila(f"Gastos (admin {admin_pct}% + fijos)", f"-{money(total_gastos)}")
    fila("Utilidad neta (estimada)", money(utilidad_neta), strong=True, color=dark)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*gray)
    pdf.multi_cell(R - M, 5, f"ROI estimado sobre precio final: {roi_pct:.1f}%. Esta cifra depende de la tarifa "
                              "por noche y la ocupacion que se logre; no es un rendimiento garantizado ni una "
                              "proyeccion de mercado.")

    fy = max(pdf.get_y() + 8, 250)
    pdf.set_draw_color(*line)
    pdf.line(M, fy, R, fy)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*gray)
    pdf.set_xy(M, fy + 4)
    pdf.multi_cell(R - M, 4, f"{LISTA_TXT}. Precios en pesos mexicanos (MXN). Precios sujetos a cambios sin "
                              "previo aviso; la lista de precios cambia cada 3 ventas. Las proyecciones de "
                              "plusvalia y renta son estimadas y no garantizan rendimientos futuros. Cotizacion "
                              "informativa, sujeta a disponibilidad de la unidad al formalizar la compra.")
    pdf.set_xy(M, pdf.get_y() + 2)
    pdf.cell(0, 4, "www.anandakino.mx - @anandakinomx")

    return bytes(pdf.output())


st.markdown("---")
pdf_bytes = crear_pdf() if puede_descargar else None
st.download_button(
    "📥 Descargar cotización en PDF",
    data=pdf_bytes if pdf_bytes else b"",
    file_name=nombre_archivo(),
    mime="application/pdf",
    disabled=not puede_descargar,
    use_container_width=True,
)
