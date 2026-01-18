import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# ==============================================================================
# 🧠 CÓDIGO INTELIGENTE DE RUTAS
# ==============================================================================
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except:
    BASE_DIR = os.getcwd()

LOGO_PATH = None
posibles_nombres = ["logo.png", "logo.jpg", "logo.jpeg", "Logo.png", "sinFondo_Azul.png"]

for nombre in posibles_nombres:
    ruta_temp = os.path.join(BASE_DIR, nombre)
    if os.path.exists(ruta_temp):
        LOGO_PATH = ruta_temp
        break

# ==============================================================================
# 🔴 MATRIZ DE DESCUENTOS EXACTA
# ==============================================================================
TABLA_DESCUENTOS = {
    0:  {95: 0.105, 90: 0.095, 80: 0.085, 70: 0.075, 60: 0.065, 50: 0.055, 40: 0.045, 30: 0.035, 25: 0.025, 20: 0.020, 15: 0.015},
    1:  {95: 0.105, 90: 0.095, 80: 0.085, 70: 0.075, 60: 0.065, 50: 0.055, 40: 0.045, 30: 0.035, 25: 0.025, 20: 0.020, 15: 0.015},
    2:  {95: 0.105, 90: 0.095, 80: 0.085, 70: 0.075, 60: 0.065, 50: 0.055, 40: 0.045, 30: 0.035, 25: 0.025, 20: 0.020, 15: 0.015},
    3:  {95: 0.105, 90: 0.095, 80: 0.085, 70: 0.075, 60: 0.065, 50: 0.055, 40: 0.045, 30: 0.035, 25: 0.025, 20: 0.020, 15: 0.015},
    4:  {95: 0.100, 90: 0.090, 80: 0.080, 70: 0.070, 60: 0.060, 50: 0.050, 40: 0.040, 30: 0.030, 25: 0.020, 20: 0.015, 15: 0.010},
    5:  {95: 0.095, 90: 0.085, 80: 0.075, 70: 0.065, 60: 0.055, 50: 0.045, 40: 0.035, 30: 0.025, 25: 0.015, 20: 0.010, 15: 0.005},
    6:  {95: 0.090, 90: 0.080, 80: 0.070, 70: 0.060, 60: 0.050, 50: 0.040, 40: 0.030, 30: 0.020, 25: 0.010, 20: 0.005},
    7:  {95: 0.085, 90: 0.075, 80: 0.065, 70: 0.055, 60: 0.045, 50: 0.035, 40: 0.025, 30: 0.015, 25: 0.005},
    8:  {95: 0.080, 90: 0.070, 80: 0.060, 70: 0.050, 60: 0.040, 50: 0.030, 40: 0.020, 30: 0.010},
    9:  {95: 0.075, 90: 0.065, 80: 0.055, 70: 0.045, 60: 0.035, 50: 0.025, 40: 0.015, 30: 0.005},
    10: {95: 0.070, 90: 0.060, 80: 0.050, 70: 0.040, 60: 0.030, 50: 0.020, 40: 0.010},
    11: {95: 0.0675, 90: 0.0575, 80: 0.0475, 70: 0.0375, 60: 0.0275, 50: 0.0175, 40: 0.0075},
    12: {95: 0.065, 90: 0.055, 80: 0.045, 70: 0.035, 60: 0.025, 50: 0.015, 40: 0.005},
    13: {95: 0.0625, 90: 0.0525, 80: 0.0425, 70: 0.0325, 60: 0.0225, 50: 0.0125, 40: 0.0025},
}

# --- PALETA DE COLORES AJUSTADA ---
BRAND_COLOR = "#004e92"  
SIDEBAR_BG = "#C5DFF8"   # <-- NUEVO COLOR: Azul intermedio más intenso
SIDEBAR_TEXT = "#003366" # Texto oscuro para contraste
MAIN_BG_GRADIENT = "linear-gradient(135deg, #E8F1F8 0%, #FAFCFF 100%)" 
ACCENT_COLOR = "#00c6ff" 

# -----------------------------------------------------------------------------
# 1. LÓGICA MATEMÁTICA
# -----------------------------------------------------------------------------
def obtener_descuento_automatico(plazo, enganche_pct):
    if plazo not in TABLA_DESCUENTOS:
        return 0.0
    escalones = TABLA_DESCUENTOS[plazo]
    niveles = sorted(escalones.keys(), reverse=True) 
    for nivel in niveles:
        if enganche_pct >= nivel:
            return escalones[nivel]
    return 0.0

# -----------------------------------------------------------------------------
# 2. CONFIGURACIÓN VISUAL (CSS)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Cotizador Ananda Kino", layout="wide", page_icon="🌊")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Avenir Next', 'Nunito', sans-serif; }}
    
    /* FONDO PRINCIPAL */
    .stApp {{ background: {MAIN_BG_GRADIENT}; }}
    
    /* BARRA LATERAL (Nuevo color intermedio) */
    section[data-testid="stSidebar"] {{ 
        background-color: {SIDEBAR_BG}; 
        border-right: 1px solid #b8cce4; /* Borde ligeramente más oscuro */
    }}
    /* TEXTO BARRA LATERAL */
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown {{ 
        color: {SIDEBAR_TEXT} !important; 
        font-weight: 600; /* Un poco más grueso para que resalte */
    }}
    
    /* Títulos */
    h1, h2, h3 {{ color: {BRAND_COLOR} !important; font-weight: 800 !important; }}
    
    /* Tarjetas Generales */
    div[data-testid="metric-container"] {{ 
        background-color: white; padding: 15px; border-radius: 12px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); text-align: center; border: 1px solid #eee;
    }}
    div[data-testid="stMetricValue"] {{ font-size: 1.5rem !important; font-weight: 800 !important; color: {BRAND_COLOR}; }}
    
    /* TARJETA ENGANCHE */
    .enganche-card {{
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px rgba(0, 78, 146, 0.15);
        border-top: 6px solid {BRAND_COLOR};
        text-align: center;
    }}
    
    /* TARJETA LIQUIDACIÓN FINAL */
    .final-saldo {{
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        margin-top: 0px; 
        box-shadow: 0 8px 20px rgba(0,0,0, 0.15);
        border-top: 6px solid #2c3e50; 
        text-align: center;
    }}
    
    .card-title {{ color: #7f8c8d; font-size: 1.1em; font-weight: 600; margin-bottom: 5px; text-transform: uppercase; }}
    .card-amount {{ font-size: 2.5em; font-weight: 900; margin: 0; }}
    .card-subtitle {{ font-weight: 700; margin-top: 5px; font-size: 0.9em; }}
    
    .blue-text {{ color: {BRAND_COLOR}; }}
    .dark-text {{ color: #2c3e50; }}
    .cyan-text {{ color: #00c6ff; }}

    /* Tabla */
    .payment-table {{
        width: 100%; border-collapse: collapse; margin-top: 10px;
        background-color: rgba(255,255,255,0.9); border-radius: 10px; overflow: hidden;
    }}
    .payment-table th {{ background-color: {BRAND_COLOR}; color: white; padding: 10px; text-align: left; font-size: 0.9em; }}
    .payment-table td {{ padding: 10px; border-bottom: 1px solid #ddd; color: #333; font-size: 0.9em; }}
    
    .stDownloadButton > button {{ width: 100%; background: linear-gradient(90deg, {BRAND_COLOR} 0%, {ACCENT_COLOR} 100%); color: white !important; font-weight: 800; padding: 15px; border-radius: 50px; border: none; box-shadow: 0 4px 15px rgba(0, 78, 146, 0.4); }}
    .stDownloadButton > button:hover {{ transform: scale(1.02); }}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. MOTOR DE PDF
# -----------------------------------------------------------------------------
class PDF(FPDF):
    def header(self):
        logo_cargado = False
        if LOGO_PATH:
            try:
                self.image(LOGO_PATH, 10, 8, 30)
                logo_cargado = True
            except: pass
        
        self.set_font('Arial', 'B', 20)
        self.set_text_color(0, 78, 146)
        
        if logo_cargado:
            self.set_xy(50, 10)
            self.cell(0, 10, 'COTIZACION ANANDA KINO', 0, 1, 'R')
        else:
            self.cell(0, 10, 'COTIZACION ANANDA KINO', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', '', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Entrega Feb 2027 | Pagina {self.page_no()}', 0, 0, 'C')

def create_pdf(cliente, lote_data, calculos, plan_pago):
    pdf = PDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(0, 78, 146)
    pdf.set_line_width(0.5)
    pdf.line(10, 30, 200, 30) 
    pdf.ln(20)
    
    # Datos
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(240, 245, 255)
    pdf.cell(0, 8, '   DATOS DEL CLIENTE', 0, 1, 'L', True)
    pdf.set_font('Arial', '', 10)
    pdf.ln(2)
    pdf.cell(100, 6, f"Cliente: {cliente['nombre']}", 0)
    pdf.cell(0, 6, f"Fecha: {cliente['fecha']}", 0, 1)
    pdf.cell(100, 6, f"Telefono: {cliente['telefono']}", 0)
    pdf.ln(5)

    # Unidad
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, '   DETALLE DE LA UNIDAD', 0, 1, 'L', True)
    pdf.set_font('Arial', '', 10)
    pdf.ln(2)
    pdf.cell(100, 6, f"Lote: {lote_data['Lote']}", 0)
    pdf.cell(0, 6, f"Superficie: {lote_data['M2']:.2f} m2", 0, 1)
    pdf.ln(5)
    
    # Financiero
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, '   PLAN FINANCIERO (PREVENTA)', 0, 1, 'L', True)
    
    w_lbl = 130
    w_val = 60
    
    def fila(txt, val, negrita=False):
        pdf.set_font('Arial', 'B' if negrita else '', 10)
        pdf.cell(w_lbl, 8, txt, 0)
        pdf.cell(w_val, 8, val, 0, 1, 'R')
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    pdf.ln(2)
    fila("Precio de Lista Base", f"${calculos['precio_lista']:,.2f}")
    fila(f"Descuento Aplicado ({calculos['pct_descuento']*100:.2f}%)", f"-${calculos['monto_descuento']:,.2f}")
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(w_lbl, 12, "PRECIO FINAL DE VENTA", 0)
    pdf.cell(w_val, 12, f"${calculos['precio_final']:,.2f}", 0, 1, 'R')
    pdf.set_text_color(0,0,0)
    
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, "DESGLOSE DE ENGANCHE:", 0, 1)
    
    fila(f"Total Enganche ({plan_pago['pct_enganche']}%)", f"${calculos['enganche_monto']:,.2f}", True)
    fila(f"Plazo para Enganche", f"{plan_pago['plazo']} Meses")
    
    if plan_pago['plazo'] > 0:
         fila(f"Mensualidad Enganche", f"${calculos['mensualidad']:,.2f}", True)

    pdf.ln(5)
    # SALDO
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, f"   LIQUIDACION FINAL (FEB 2027): ${calculos['saldo']:,.2f}", 0, 1, 'L', True)
    pdf.set_text_color(0, 0, 0)

    # Tabla
    if plan_pago['plazo'] > 0:
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 8, "Calendario de Pagos del Enganche", 0, 1)
        
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(20, 7, "#", 1, 0, 'C', True)
        pdf.cell(90, 7, "Concepto", 1, 0, 'L', True)
        pdf.cell(45, 7, "Monto", 1, 1, 'R', True)
        
        pdf.set_font('Arial', '', 9)
        mensual = calculos['mensualidad']
        for i in range(1, plan_pago['plazo'] + 1):
            pdf.cell(20, 7, str(i), 1, 0, 'C')
            pdf.cell(90, 7, f"Abono Mensual {i}/{plan_pago['plazo']}", 1, 0, 'L')
            pdf.cell(45, 7, f"${mensual:,.2f}", 1, 1, 'R')
            
    return pdf.output(dest='S').encode('latin-1')

# -----------------------------------------------------------------------------
# 4. INTERFAZ GRÁFICA
# -----------------------------------------------------------------------------
if LOGO_PATH:
    try:
        st.sidebar.image(LOGO_PATH, use_container_width=True)
    except:
        st.sidebar.warning("No se pudo leer el logo.")
else:
    st.sidebar.markdown(f"<h3 style='color:{SIDEBAR_TEXT}'>ANANDA KINO</h3>", unsafe_allow_html=True)

st.markdown("<h1>COTIZADOR ANANDA KINO</h1>", unsafe_allow_html=True)
st.markdown("### 🏗️ Entrega y Liquidación: Febrero 2027")
st.markdown("---")

uploaded_file = st.sidebar.file_uploader("📂 Cargar CSV", type=['csv'])

if uploaded_file is not None:
    try:
        encodings = ['utf-8', 'latin-1', 'cp1252']
        df = None
        list_map = None
        for enc in encodings:
            try:
                uploaded_file.seek(0)
                df_raw = pd.read_csv(uploaded_file, header=None, encoding=enc)
                h_idx = df_raw[df_raw.apply(lambda r: r.astype(str).str.contains('LOTE', case=False).any(), axis=1)].index[0]
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, header=h_idx, encoding=enc)
                df.columns = df.columns.str.strip()
                df = df[pd.to_numeric(df['LOTE'], errors='coerce').notnull()].copy()
                df['LOTE'] = df['LOTE'].astype(int)
                price_cols = [c for c in df.columns if 'Lista' in c and 'Construccion' in c]
                list_map = {f"Lista {i+1}": col for i, col in enumerate(price_cols)}
                break
            except: continue
    except: df = None

    if df is not None and list_map:
        st.sidebar.header("1. PROPIEDAD")
        sel_lote = st.sidebar.selectbox("Lote", sorted(df['LOTE'].unique()))
        sel_lista = st.sidebar.selectbox("Lista de Precio", list(list_map.keys()))
        
        row = df[df['LOTE'] == sel_lote].iloc[0]
        try:
            val_str = str(row[list_map[sel_lista]]).replace('$','').replace(',','')
            precio_base = float(val_str)
        except: precio_base = 0.0
        m2 = float(row['Total Terreno']) if 'Total Terreno' in df.columns else 0.0

        st.sidebar.header("2. CLIENTE")
        cli_nombre = st.sidebar.text_input("Nombre", "Cliente")
        cli_tel = st.sidebar.text_input("Teléfono")
        cli_fecha = st.sidebar.date_input("Fecha", datetime.now())
        
        st.sidebar.header("3. PLAN DE ENGANCHE")
        opciones_enganche = [15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 95]
        opciones_enganche = sorted(list(set(opciones_enganche)))
        
        eng_pct = st.sidebar.select_slider("% Enganche Total", options=opciones_enganche, value=30)
        
        opciones_plazo = [0] + list(range(1, 14))
        sel_plazo = st.sidebar.selectbox("Meses para pagar Enganche", opciones_plazo, index=12)
        
        # CÁLCULOS
        desc_final = obtener_descuento_automatico(sel_plazo, eng_pct)
        monto_desc = precio_base * desc_final
        precio_final = precio_base - monto_desc
        
        monto_enganche_total = precio_final * (eng_pct / 100.0)
        saldo_contra_entrega = precio_final - monto_enganche_total
        
        if sel_plazo > 0:
            mensualidad_enganche = monto_enganche_total / sel_plazo
        else:
            mensualidad_enganche = 0

        # VISUAL
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Precio Lista", f"${precio_base:,.2f}")
        with c2: st.metric("Descuento", f"{desc_final*100:.2f}%", f"-${monto_desc:,.2f}")
        with c3: st.metric("PRECIO CIERRE", f"${precio_final:,.2f}")

        st.markdown("<br>", unsafe_allow_html=True)

        col_izq, col_der = st.columns([1, 1])
        with col_izq:
            st.markdown(f"""
                <div class="enganche-card">
                    <div class="card-title">ENGANCHE TOTAL ({eng_pct}%)</div>
                    <div class="card-amount blue-text">${monto_enganche_total:,.2f}</div>
                    <div class="card-subtitle cyan-text">A pagar en {sel_plazo} meses</div>
                </div>
            """, unsafe_allow_html=True)
            
            if sel_plazo > 0:
                st.markdown(f"#### 📅 Desglose de Mensualidades")
                html_table = "<table class='payment-table'><tr><th>#</th><th>Concepto</th><th>Monto</th></tr>"
                for i in range(1, sel_plazo + 1):
                    html_table += f"<tr><td>{i}</td><td>Mensualidad Enganche</td><td><b>${mensualidad_enganche:,.2f}</b></td></tr>"
                html_table += "</table>"
                st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.info("Pago de Enganche Inmediato (Contado)")

        with col_der:
            st.markdown(f"""
                <div class="final-saldo">
                    <div class="card-title">LIQUIDACIÓN FINAL</div>
                    <div class="card-amount dark-text">${saldo_contra_entrega:,.2f}</div>
                    <div class="card-subtitle" style="color:#7f8c8d">Contra Entrega (Febrero 2027)</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            cli_data = {"nombre": cli_nombre, "telefono": cli_tel, "fecha": str(cli_fecha)}
            lot_data = {"Lote": sel_lote, "M2": m2}
            calc_data = {
                "precio_lista": precio_base, "pct_descuento": desc_final, 
                "monto_descuento": monto_desc, "precio_final": precio_final, 
                "enganche_monto": monto_enganche_total, "saldo": saldo_contra_entrega, 
                "mensualidad": mensualidad_enganche 
            }
            plan_data = {"pct_enganche": eng_pct, "plazo": sel_plazo}
            
            pdf_bytes = create_pdf(cli_data, lot_data, calc_data, plan_data)
            
            st.download_button(
                label="⬇️ DESCARGAR COTIZACIÓN OFICIAL",
                data=pdf_bytes,
                file_name=f"Cotizacion_{sel_lote}.pdf",
                mime="application/pdf"
            )

    else:
        st.warning("Error leyendo el CSV.")
else:
    st.info("👈 Carga el CSV en el menú azul de la izquierda.")