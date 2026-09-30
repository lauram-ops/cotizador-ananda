# -*- coding: utf-8 -*-
"""
Cotizador de preventa · Ananda Kino
-----------------------------------
App de una sola pantalla para que los asesores generen cotizaciones
en PDF durante la cita. Corre en Streamlit Community Cloud.

Estructura del repositorio esperada:
    app.py              (este archivo)
    requirements.txt
    logo.png            (logo de Ananda, fondo transparente)
"""

import base64
from datetime import date, datetime

import streamlit as st
from fpdf import FPDF

with open("logo.png", "rb") as _f:
    LOGO_B64 = base64.b64encode(_f.read()).decode("ascii")

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(page_title="Ananda Kino | Cotizador de preventa", page_icon="🏠", layout="wide")

# Paleta tomada del logo de Ananda
BRAND = "#4D6D80"       # botones / acentos
LOGO_C = "#658597"      # línea del logo
SOFT = "#E9F0F3"        # fondo de tarjetas
INK = "#16232C"
MUTED = "#5C6D78"
LINE = "#DDE5EA"
BAD = "#B3261E"

st.markdown(f"""
<style>
.stApp {{ background: #F3F6F8; }}
.badge-lista {{
    display:inline-block; background:{BRAND}; color:#fff; font-weight:800;
    font-size:15px; letter-spacing:.5px; padding:5px 14px; border-radius:8px;
}}
.doc-card {{
    background:#fff; border-radius:12px; padding:26px 30px; border:1px solid {LINE};
}}
.doc-head {{
    display:flex; justify-content:space-between; align-items:center;
    border-bottom:2px solid {LOGO_C}; padding-bottom:14px; margin-bottom:16px; flex-wrap:wrap; gap:10px;
}}
.kind {{ font-size:12px; font-weight:700; letter-spacing:1px; text-transform:uppercase; text-align:right; color:{INK}; }}
.sub {{ font-size:12px; color:{MUTED}; text-align:right; margin-top:4px; }}
.meta-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:16px; }}
.meta-k {{ font-size:11px; text-transform:uppercase; letter-spacing:.8px; color:{MUTED}; }}
.meta-v {{ font-weight:600; color:{INK}; }}
.house-box {{ background:{SOFT}; border-radius:10px; padding:14px 16px; margin-bottom:16px; }}
.house-t {{ font-weight:700; color:{INK}; }}
.house-s {{ font-size:13px; color:{MUTED}; margin-top:3px; }}
table.eco {{ width:100%; border-collapse:collapse; margin-bottom:18px; }}
table.eco td {{ padding:10px 6px; border-bottom:1px solid {LINE}; vertical-align:top; color:{INK}; }}
table.eco td:last-child {{ text-align:right; font-weight:600; white-space:nowrap; }}
table.eco tr.final td {{ background:{SOFT}; font-weight:800; font-size:16px; }}
table.eco .small {{ display:block; font-size:12px; color:{MUTED}; font-weight:400; }}
.disc {{ color:{BAD}; }}
h3.sect {{ font-size:13px; text-transform:uppercase; letter-spacing:1px; color:{BRAND}; margin-bottom:6px; }}
.pays-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:6px; margin-bottom:18px; }}
.pay-item {{ display:flex; justify-content:space-between; font-size:13px; border:1px solid {LINE}; border-radius:6px; padding:6px 10px; }}
.pay-item span:first-child {{ color:{MUTED}; }}
.fine {{ font-size:12px; color:{MUTED}; margin-top:14px; border-top:1px solid {LINE}; padding-top:10px; }}
.push-note {{ background:{BRAND}; color:#fff; border-radius:8px; padding:12px 14px; font-size:14px; margin-bottom:10px; }}
.warn-note {{ background:#FFF3DC; color:#8A5300; border-radius:8px; padding:10px 14px; font-size:13px; margin-bottom:10px; }}
.info-note {{ background:{SOFT}; color:{MUTED}; border-radius:8px; padding:10px 14px; font-size:13px; margin-bottom:10px; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# DATOS DEL PROYECTO — LISTA DE PRECIOS 2 (vigente desde el 18-sep-2026)
# ==============================================================================
# desplante = m² de planta baja del prototipo (Memorándum Ananda): A = 82.04, C = 74.12
# patio = privativo - desplante
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

# La lista cambia cada 3 ventas; la siguiente lista sube 3% sobre la actual.
VENDIDOS_AL_INICIO_DE_LISTA = 3   # vendidos cuando arrancó la Lista 2
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

# Descuento (%) por % de enganche (fila) y plazo en meses 1..13 (índice 0..12)
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

# Estancia (Prototipo B, Memorándum Ananda): agrega recámara/estancia en planta alta.
# Solo disponible para lotes de 161 y 147 m² privativos (no para los de 133 m², lotes 34-37).
ESTANCIA_PRECIO = 450000
ESTANCIA_CONSTR_EXTRA = 18.15  # 146.95 - 128.80 m² (planta baja / patio no cambian)


def money(n):
    return "${:,.0f}".format(n)


def pct_txt(p):
    return f"{p:g}%"


def m2_txt(n):
    return f"{n:g} m²"


def fecha_larga(d):
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def obtener_descuento(enganche, plazo):
    fila = MATRIZ.get(enganche, [])
    if 1 <= plazo <= len(fila):
        return fila[plazo - 1]
    return None


# ==============================================================================
# BARRA LATERAL — DATOS DE LA COTIZACIÓN
# ==============================================================================
st.sidebar.image("logo.png", use_container_width=True)
st.sidebar.markdown("### Datos de la cotización")

cliente = st.sidebar.text_input("Cliente", value="")
asesor = st.sidebar.text_input("Asesor", value="")
fecha_cot = st.sidebar.date_input("Fecha", value=date.today(), format="DD/MM/YYYY")

st.sidebar.markdown("---")

lotes_activos = [n for n in sorted(LOTES) if LOTES[n]["activo"]]
if not lotes_activos:
    st.error("No hay lotes activos configurados en GRUPOS. Revisa la lista de precios en el código.")
    st.stop()


def fmt_lote(n):
    l = LOTES[n]
    txt = l["entrega"]["txt"].replace("septiembre 20", "sep ").replace("marzo 20", "mar ")
    extra = " (vendido)" if l["vendido"] else ""
    return f'Lote {n} · {l["priv"]:g} m² · {money(l["precio"])} · {txt}{extra}'


lote_sel = st.sidebar.selectbox("Lote", lotes_activos, format_func=fmt_lote, index=0)
lote = LOTES[lote_sel]
vendido = lote["vendido"]

estancia_disponible = lote["priv"] in (147, 161)
if estancia_disponible:
    con_estancia = st.sidebar.checkbox(f"Agregar estancia en planta alta (+{money(ESTANCIA_PRECIO)})",
                                        key="con_estancia")
    st.sidebar.caption("Prototipo B: +18.15 m² de construcción en planta alta. El patio no cambia.")
else:
    con_estancia = False
    st.sidebar.caption("La estancia no está disponible para este lote (prototipo C, lotes 34-37).")

col_a, col_b = st.sidebar.columns(2)
with col_a:
    enganche_pct = st.selectbox("% de enganche", ENGANCHES, index=ENGANCHES.index(30))
with col_b:
    plazo_meses = st.selectbox("Plazo (meses)", list(range(1, 14)), index=5)

# Fecha de liquidación: se llena sola con la entrega del lote seleccionado,
# y el asesor puede editarla. Se reinicia solo cuando cambia el lote.
if "last_lote" not in st.session_state:
    st.session_state.last_lote = None
if st.session_state.last_lote != lote_sel:
    st.session_state.fliq = LOTES[lote_sel]["entrega"]["txt"]
    st.session_state.last_lote = lote_sel

fliq = st.sidebar.text_input("Fecha estimada de liquidación", key="fliq")
st.sidebar.caption('Se llena con la entrega estimada del lote. Edítala si el acuerdo es distinto.')

# ==============================================================================
# CÁLCULOS
# ==============================================================================
descuento_pct = obtener_descuento(enganche_pct, plazo_meses)
hay_desc = descuento_pct is not None
descuento_pct_val = descuento_pct or 0.0

precio_casa = lote["precio"]  # precio de lista oficial, el que sube cada 3 ventas
monto_estancia = ESTANCIA_PRECIO if con_estancia else 0
precio_lista = precio_casa + monto_estancia  # base sobre la que se calcula el descuento
constr_mostrada = lote["constr"] + (ESTANCIA_CONSTR_EXTRA if con_estancia else 0)
monto_descuento = round(precio_lista * descuento_pct_val / 100)
precio_final = precio_lista - monto_descuento
monto_enganche = round(precio_final * enganche_pct / 100)
saldo_final = precio_final - monto_enganche

base_pago = monto_enganche // plazo_meses
pagos = [base_pago] * plazo_meses
pagos[-1] = monto_enganche - base_pago * (plazo_meses - 1)

fliq_txt = fliq.strip() or lote["entrega"]["txt"]

# Escalón a la siguiente lista (Lista 3 = Lista 2 + 3%)
restantes = VENTAS_POR_LISTA - (len(VENDIDOS) - VENDIDOS_AL_INICIO_DE_LISTA)
mostrar_escalon = 1 <= restantes <= VENTAS_POR_LISTA
if mostrar_escalon:
    precio_casa_prox = round(precio_casa * INCREMENTO_SIGUIENTE)  # la estancia no escala con la lista
    precio_prox = precio_casa_prox + monto_estancia
    final_prox = precio_prox - round(precio_prox * descuento_pct_val / 100)

# ==============================================================================
# CUERPO PRINCIPAL
# ==============================================================================
st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px">'
    f'<h2 style="margin:0;color:{INK}">Cotizador de preventa · Ananda Kino</h2>'
    f'<span class="badge-lista">{LISTA_BADGE}</span></div>',
    unsafe_allow_html=True,
)

if vendido:
    st.error("⛔ Este lote ya está vendido. Selecciona otro en la barra lateral.")

meta_html = f"""
<div class="meta-grid">
  <div><div class="meta-k">Cliente</div><div class="meta-v">{cliente or '—'}</div></div>
  <div><div class="meta-k">Asesor</div><div class="meta-v">{asesor or '—'}</div></div>
  <div><div class="meta-k">Fecha</div><div class="meta-v">{fecha_larga(fecha_cot)}</div></div>
</div>
"""

pagos_html = "".join(
    f'<div class="pay-item"><span>Pago {i+1}</span><span>{money(p)}</span></div>'
    for i, p in enumerate(pagos)
)

if hay_desc:
    base_desc_txt = "el subtotal (casa + estancia)" if con_estancia else "el precio de lista"
    desc_label = f'Descuento por enganche y plazo <span class="small">{pct_txt(descuento_pct_val)} sobre {base_desc_txt}</span>'
    desc_val = f'<span class="disc">-{money(monto_descuento)}</span>'
else:
    desc_label = 'Descuento por enganche y plazo <span class="small">Esta combinación no tiene descuento en la tabla vigente</span>'
    desc_val = "$0"

if plazo_meses == 1:
    resumen_pagos = f"1 pago de {money(pagos[-1])}"
elif base_pago == pagos[-1]:
    resumen_pagos = f"{plazo_meses} pagos mensuales de {money(base_pago)}"
else:
    resumen_pagos = f"{plazo_meses} pagos mensuales de {money(base_pago)} (el último de {money(pagos[-1])})"

doc_html = f"""
<div class="doc-card">
  <div class="doc-head">
    <img src="data:image/png;base64,{LOGO_B64}" style="height:56px">
    <div>
      <div class="kind">Cotización de preventa</div>
      <div style="text-align:right;margin-top:4px"><span class="badge-lista">{LISTA_BADGE}</span></div>
      <div class="sub">44 casas · Kino Nuevo</div>
    </div>
  </div>
  {meta_html}
  <div class="house-box">
    <div class="house-t">Lote {lote['n']} · 3 recámaras · 2.5 baños · Doble cochera{' + Estancia' if con_estancia else ''}</div>
    <div class="house-s">Privativo {m2_txt(lote['priv'])} · Construcción {m2_txt(constr_mostrada)} · Patio {m2_txt(lote['patio'])}</div>
    <div class="house-s">Terreno total {m2_txt(lote['terreno'])} · Entrega estimada: {lote['entrega']['txt']}{' · Incluye estancia (+' + m2_txt(ESTANCIA_CONSTR_EXTRA) + ')' if con_estancia else ''}</div>
    <div class="house-s">{ACABADOS_TXT}</div>
  </div>
  <table class="eco">
    <tr><td>Precio de lista</td><td>{money(precio_casa)}</td></tr>
    {'<tr><td>+ Estancia <span class="small">Prototipo B, planta alta</span></td><td>' + money(monto_estancia) + '</td></tr>' if con_estancia else ''}
    {'<tr style="background:var(--soft); font-weight:700"><td>Subtotal (casa + estancia)</td><td>' + money(precio_lista) + '</td></tr>' if con_estancia else ''}
    <tr><td>{desc_label}</td><td>{desc_val}</td></tr>
    <tr class="final"><td>Precio final</td><td>{money(precio_final)}</td></tr>
    <tr><td>Enganche <span class="small">{enganche_pct}% del precio final</span></td><td>{money(monto_enganche)}</td></tr>
    <tr><td>Saldo a liquidar</td><td>{money(saldo_final)}</td></tr>
  </table>
  <h3 class="sect">Plan de pago del enganche</h3>
  <p>{resumen_pagos}</p>
  <div class="pays-grid">{pagos_html}</div>
  <h3 class="sect">Liquidación del saldo</h3>
  <p>Fecha estimada de liquidación: <strong>{fliq_txt}</strong></p>
  <p>El saldo se cubre con recursos propios o con crédito hipotecario a través de brokers aliados. El crédito está sujeto a aprobación de la institución financiera.</p>
  <div class="fine">{LISTA_TXT}. Precios en pesos mexicanos (MXN). Precios sujetos a cambios sin previo aviso; la lista de precios cambia cada 3 ventas. Cotización informativa, sujeta a disponibilidad de la unidad al formalizar la compra.</div>
</div>
"""

col_izq, col_der = st.columns([1, 1.4])

with col_izq:
    st.markdown("#### Avisos para el asesor")
    st.caption("Esta columna no se imprime ni se incluye en el PDF.")

    if mostrar_escalon:
        st.markdown(
            f'<div class="push-note"><strong>Al cerrar {restantes} '
            f'{"venta más" if restantes == 1 else "ventas más"}, este lote sube a {money(precio_prox)}</strong> '
            f'(+{money(precio_prox - precio_lista)} en precio de lista).<br>'
            f'Con esta misma forma de pago, el precio final pasaría de {money(precio_final)} a {money(final_prox)} '
            f'(+{money(final_prox - precio_final)}).</div>',
            unsafe_allow_html=True,
        )

    if not hay_desc:
        st.markdown(
            '<div class="warn-note">Esta combinación de enganche y plazo no tiene descuento en la '
            'tabla vigente. Confírmala antes de ofrecerla.</div>',
            unsafe_allow_html=True,
        )

    fin = datetime(fecha_cot.year, fecha_cot.month, 1)
    mm = fin.month - 1 + plazo_meses
    fin_y = fin.year + mm // 12
    fin_m = mm % 12 + 1
    fin_key = fin_y * 12 + fin_m
    ent_key = lote["entrega"]["y"] * 12 + lote["entrega"]["m"]
    fin_txt = f"{MESES[fin_m - 1]} {fin_y}"
    if fin_key > ent_key:
        st.markdown(
            f'<div class="warn-note">Con pagos mensuales desde la fecha de la cotización, el enganche '
            f'terminaría en {fin_txt}, después de la entrega estimada de este lote ({lote["entrega"]["txt"]}). '
            f'Reduce el plazo o confirma el esquema con dirección comercial.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="info-note">El enganche termina hacia {fin_txt}, antes o en la entrega estimada '
            f'del lote ({lote["entrega"]["txt"]}).</div>',
            unsafe_allow_html=True,
        )

    faltan = []
    if not cliente.strip():
        faltan.append("cliente")
    if not asesor.strip():
        faltan.append("asesor")
    puede_descargar = not faltan and not vendido

    if faltan:
        st.info("Para descargar falta: " + " y ".join(faltan) + ".")

with col_der:
    st.markdown(doc_html, unsafe_allow_html=True)


# ==============================================================================
# GENERADOR DE PDF
# ==============================================================================
class CotizacionPDF(FPDF):
    pass


def nombre_archivo():
    import re
    c = re.sub(r"[^A-Za-z0-9]+", "_", cliente.strip()).strip("_")
    return f"Cotizacion_Ananda_Kino_Lote{lote['n']}" + (f"_{c}" if c else "") + ".pdf"


def crear_pdf():
    pdf = CotizacionPDF(format="Letter")
    pdf.add_page()
    W = pdf.w
    M = 18
    R = W - M

    def hexrgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    blue = hexrgb(BRAND)
    logoc = hexrgb(LOGO_C)
    ink = hexrgb(INK)
    gray = hexrgb(MUTED)
    line = hexrgb(LINE)
    soft = hexrgb(SOFT)

    # --- Encabezado con logo + insignia de lista ---
    pdf.image("logo.png", M, 9, 54)
    pdf.set_text_color(*ink)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(M, 10)
    pdf.cell(R - M, 6, "COTIZACION DE PREVENTA", align="R")
    pdf.set_fill_color(*blue)
    pdf.set_xy(R - 56, 16)
    pdf.set_draw_color(*blue)
    pdf.rect(R - 56, 16, 56, 9.5, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_xy(R - 56, 18.6)
    pdf.cell(56, 5, "LISTA 2 - SEP 2026", align="C")
    pdf.set_text_color(*gray)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(M, 26)
    pdf.cell(R - M, 5, "44 casas - Kino Nuevo, Bahia de Kino, Sonora - www.anandakino.mx", align="R")
    pdf.set_draw_color(*logoc)
    pdf.set_line_width(0.8)
    pdf.line(M, 31, R, 31)

    # --- Datos del cliente ---
    y = 44
    cols = [("CLIENTE", cliente or "-", M), ("ASESOR", asesor or "-", M + 78), ("FECHA", fecha_larga(fecha_cot), M + 128)]
    for k, v, x in cols:
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*gray)
        pdf.cell(46, 5, k)
        pdf.set_xy(x, y + 6)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*ink)
        pdf.cell(72 if k == "CLIENTE" else 46, 6, str(v)[:38])

    # --- Casa ---
    y = 58
    pdf.set_fill_color(*soft)
    pdf.rect(M, y, R - M, 38, style="F")
    pdf.set_xy(M + 5, y + 4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*ink)
    titulo_casa = f"Lote {lote['n']} - 3 recamaras - 2.5 banos - Doble cochera"
    if con_estancia:
        titulo_casa += " + Estancia"
    pdf.cell(0, 6, titulo_casa)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*gray)
    pdf.set_xy(M + 5, y + 11)
    pdf.cell(0, 5, f"Privativo {lote['priv']:g} m2 - Construccion {constr_mostrada:g} m2 - Patio {lote['patio']:g} m2")
    pdf.set_xy(M + 5, y + 17)
    entrega_linea = f"Terreno total {lote['terreno']:g} m2 - Entrega estimada: {lote['entrega']['txt']}"
    if con_estancia:
        entrega_linea += f" - Incluye estancia (+{ESTANCIA_CONSTR_EXTRA:g} m2)"
    pdf.cell(0, 5, entrega_linea)
    pdf.set_xy(M + 5, y + 23)
    pdf.multi_cell(R - M - 10, 5, "Se entrega con pisos, closets, carpinteria de cocina con barra de "
                                    "granito, horno, campana, parrilla electrica y canceleria.")

    # --- Condiciones económicas: tarjetas + escalón (estilo de la primera propuesta) ---
    red = hexrgb("#DC3545")
    green = hexrgb("#28A745")
    gold = hexrgb("#B8860B")
    cream = hexrgb("#FFFCF2")

    y = 106
    pdf.set_xy(M, y)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*blue)
    pdf.cell(0, 6, "CONDICIONES ECONOMICAS - LISTA DE PRECIOS 2")
    y += 9

    gap = 4
    cw3 = (R - M - 2 * gap) / 3
    ch3 = 25 if con_estancia else 20
    xs = [M, M + cw3 + gap, M + 2 * (cw3 + gap)]
    val_y = 15 if con_estancia else 11  # centra mejor el valor cuando la tarjeta crece

    def tarjeta(x, label, valor, color_valor, fuente_valor=13, borde=None):
        pdf.set_fill_color(*soft)
        pdf.rect(x, y, cw3, ch3, style="F")
        if borde:
            pdf.set_draw_color(*borde)
            pdf.set_line_width(0.7)
            pdf.rect(x, y, cw3, ch3, style="D")
        pdf.set_xy(x + 4, y + 3.5)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*gray)
        pdf.cell(cw3 - 8, 4, label)
        pdf.set_xy(x + 4, y + val_y)
        pdf.set_font("Helvetica", "B", fuente_valor)
        pdf.set_text_color(*color_valor)
        pdf.cell(cw3 - 8, 8, valor)

    if con_estancia:
        # Tarjeta 1 desglosada: casa + estancia = subtotal (antes del descuento)
        x0 = xs[0]
        pdf.set_fill_color(*soft)
        pdf.rect(x0, y, cw3, ch3, style="F")
        pdf.set_xy(x0 + 4, y + 3)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*gray)
        pdf.cell(cw3 - 8, 3.5, "PRECIO DE LISTA")
        pdf.set_xy(x0 + 4, y + 7.5)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*ink)
        pdf.cell(cw3 - 8, 4, f"Casa: {money(precio_casa)}")
        pdf.set_xy(x0 + 4, y + 12)
        pdf.cell(cw3 - 8, 4, f"+ Estancia: {money(monto_estancia)}")
        pdf.set_xy(x0 + 4, y + 17.5)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(cw3 - 8, 6, f"= {money(precio_lista)}")
    else:
        tarjeta(xs[0], "PRECIO DE LISTA", money(precio_lista), ink, 12)

    label2 = f"TU DESCUENTO ({descuento_pct_val:g}%)" if hay_desc else "SIN DESCUENTO"
    tarjeta(xs[1], label2, ("-" + money(monto_descuento)) if hay_desc else "$0", red, 11 if con_estancia else 12)
    tarjeta(xs[2], "PRECIO FINAL", money(precio_final), green, 14, borde=green)

    y += ch3 + 2

    if mostrar_escalon:
        eb_h = 12
        pdf.set_fill_color(*cream)
        pdf.rect(M, y, R - M, eb_h, style="F")
        pdf.set_draw_color(*gold)
        pdf.set_line_width(0.6)
        pdf.rect(M, y, R - M, eb_h, style="D")
        restantes_txt = "venta mas" if restantes == 1 else "ventas mas"
        pdf.set_xy(M + 5, y + 2)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(*gold)
        pdf.cell(R - M - 10, 5.5, f"Al cerrar {restantes} {restantes_txt}, este lote sube a {money(precio_prox)}")
        pdf.set_xy(M + 5, y + 7)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*ink)
        pdf.cell(R - M - 10, 5, f"Con esta misma forma de pago, el precio final pasaria a {money(final_prox)}.")
        y += eb_h + 2
    else:
        y += 2

    rh = 9
    filas2 = [
        (f"Enganche ({enganche_pct}% del precio final)", money(monto_enganche)),
        ("Saldo a liquidar", money(saldo_final)),
    ]
    for i, (label, val) in enumerate(filas2):
        top = y + i * rh
        pdf.set_draw_color(*line)
        pdf.set_line_width(0.3)
        pdf.line(M, top + rh, R, top + rh)
        pdf.set_font("Helvetica", "", 10.5)
        pdf.set_text_color(*ink)
        pdf.set_xy(M + 2, top + 1.5)
        pdf.cell(R - M - 60, rh - 2, label)
        pdf.set_xy(R - 60, top + 1.5)
        pdf.cell(58, rh - 2, val, align="R")
    y += len(filas2) * rh + 5

    # --- Plan de pago ---
    pdf.set_xy(M, y)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*blue)
    pdf.cell(0, 6, "PLAN DE PAGO DEL ENGANCHE")
    y += 6
    pdf.set_xy(M, y)
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(*ink)
    pdf.cell(0, 6, resumen_pagos)
    y += 5

    ncols = 4
    cw = (R - M) / ncols
    ch = 8
    for i, p in enumerate(pagos):
        col = i % ncols
        row = i // ncols
        cx = M + col * cw
        cy = y + row * ch
        pdf.set_draw_color(*line)
        pdf.set_line_width(0.3)
        pdf.rect(cx + 0.5, cy, cw - 3, ch - 1.5)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*gray)
        pdf.set_xy(cx + 3, cy + 1.2)
        pdf.cell(cw - 10, ch - 3, f"Pago {i + 1}")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*ink)
        pdf.set_xy(cx + 3, cy + 1.2)
        pdf.cell(cw - 8, ch - 3, money(p), align="R")
    import math
    y += math.ceil(len(pagos) / ncols) * ch + 6

    # --- Liquidación ---
    pdf.set_xy(M, y)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*blue)
    pdf.cell(0, 6, "LIQUIDACION DEL SALDO")
    y += 6
    pdf.set_xy(M, y)
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(*ink)
    pdf.multi_cell(R - M, 5.5, f"Saldo de {money(saldo_final)}. Fecha estimada de liquidacion: {fliq_txt}.")
    y = pdf.get_y() + 2
    pdf.set_xy(M, y)
    pdf.multi_cell(R - M, 5, "El saldo se cubre con recursos propios o con credito hipotecario a "
                              "traves de brokers aliados. El credito esta sujeto a aprobacion de la "
                              "institucion financiera.")

    # --- Pie (posición dinámica: con enganches largos el contenido de arriba crece) ---
    fy = max(252, pdf.get_y() + 6)
    pdf.set_draw_color(*line)
    pdf.line(M, fy, R, fy)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*gray)
    pdf.set_xy(M, fy + 4)
    pdf.multi_cell(R - M, 4, f"{LISTA_TXT}. Precios en pesos mexicanos (MXN). Precios sujetos a cambios "
                              "sin previo aviso; la lista de precios cambia cada 3 ventas. Cotizacion "
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
