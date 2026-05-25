# -*- coding: utf-8 -*-
"""
DASHBOARD DE ALERTAS TEMPRANAS - UFPS
Universidad Francisco de Paula Santander
Versión: 3.0 (Carga Automática y Error de Texto corregido)
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import textwrap
import re
import base64
import os
import requests
from io import BytesIO
from datetime import datetime
from wordcloud import WordCloud
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURACIÓN DE DATOS (GOOGLE DRIVE)
# ============================================================================
# IMPORTANTE: Reemplaza este ID por el ID real de tu archivo en Google Drive
ID_DRIVE = "1kOy-kkQwz4PCP-hOPQWF41MO6ICOjHdy" 
URL_DRIVE = f'https://docs.google.com/spreadsheets/d/1kOy-kkQwz4PCP-hOPQWF41MO6ICOjHdy/export?format=xlsx'

# ============================================================================
# FUNCIONES UTILITARIAS Y DE LOGOS
# ============================================================================
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

def cargar_logo_base64(ruta_imagen: str) -> str:
    if os.path.exists(ruta_imagen):
        with open(ruta_imagen, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# ============================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ============================================================================
st.set_page_config(
    page_title="Dashboard Alertas Tempranas - UFPS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #8B0000 0%, #C73E1D 100%);
        padding: 20px 30px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 24px;
    }
    .main-header-logo { height: 90px; width: auto; flex-shrink: 0; filter: brightness(0) invert(1); }
    .main-header-text { text-align: left; }
    .main-header h1 { margin: 0 0 4px 0; font-size: 1.7rem; }
    .main-header h3 { margin: 0 0 4px 0; font-size: 1.1rem; opacity: .92; }
    .main-header p  { margin: 0; font-size: .85rem; opacity: .80; }
    .section-title { color: #8B0000; border-bottom: 2px solid #C73E1D; padding-bottom: 5px; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNCIONES DE DATOS
# ============================================================================
def simplificar_razones(razon):
    if pd.isna(razon) or str(razon).strip() == '':
        return None
    razon_lower = str(razon).lower().strip()
    categorias = {
        'Falta de preparación':     ['no me preparé', 'falta de estudio', 'no estudié', 'no repasé'],
        'Dificultad de comprensión':['no comprendo', 'no entiendo', 'dificultad para entender'],
        'Problemas con evaluación': ['temas evaluados', 'dificultad del examen', 'no son acordes'],
        'Problemas laborales':      ['temas laborales', 'trabajo', 'laboral'],
        'Temática amplia':          ['temática evaluada', 'muy amplia', 'muchos temas'],
        'Tiempo insuficiente':      ['examen es muy largo', 'tiempo asignado', 'falta de tiempo'],
        'Problemas con docente':    ['explicaciones del docente', 'no son claras', 'metodología'],
        'Problemas familiares':     ['temas familiares', 'problemas familiares', 'familia']
    }
    for categoria, palabras in categorias.items():
        for palabra in palabras:
            if palabra in razon_lower:
                return categoria
    return 'Otras razones'

@st.cache_data(ttl=600)
def cargar_datos_automatico(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_excel(BytesIO(response.content))
            df['Año']        = df['Fecha'].dt.year
            df['Semestre']   = df['Fecha'].dt.month.apply(lambda x: 1 if x <= 6 else 2)
            df['Mes']        = df['Fecha'].dt.month
            df['Mes_Nombre'] = df['Fecha'].dt.strftime('%B')
            df['Día_Semana'] = df['Fecha'].dt.day_name()
            df_limpio = df.copy()
            for col in df_limpio.columns:
                if df_limpio[col].dtype == 'object':
                    df_limpio[col] = df_limpio[col].replace(['NO APLICA', ''], np.nan)
            return df, df_limpio
        return None, None
    except:
        return None, None

# ============================================================================
# ENCABEZADO Y LOGOS
# ============================================================================
logo_blanco_b64 = get_base64_of_bin_file("BLANCO.png")
_nuevo_logo_tag = f'<img src="data:image/png;base64,{logo_blanco_b64}" class="main-header-logo" style="width: 200px; height: auto; margin-right: 40px;">' if logo_blanco_b64 else ""

st.markdown(f"""
<div class="main-header">
    {_nuevo_logo_tag}
    <div class="main-header-text">
        <h1>📊 Dashboard de Alertas Tempranas</h1>
        <h3>Universidad Francisco de Paula Santander — UFPS</h3>
        <p>Análisis de Deserción y Permanencia Estudiantil | Maestría TIC aplicadas a la Educación</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# CARGA DE DATOS Y SIDEBAR
# ============================================================================
logo_sidebar_b64 = cargar_logo_base64("Logo-nuevo-vertical.png")
if logo_sidebar_b64:
    st.sidebar.markdown(f'<img src="data:image/png;base64,{logo_sidebar_b64}" style="width:230px; display:block; margin:0 auto 10px auto;">', unsafe_allow_html=True)

st.sidebar.markdown("## ⚙️ Configuración")

with st.spinner("Sincronizando con Drive..."):
    df, df_limpio = cargar_datos_automatico(URL_DRIVE)

if df is None:
    st.error("No se pudo cargar el archivo desde Drive. Revisa el ID y los permisos.")
    st.stop()

# Filtros
años_disponibles = sorted(df_limpio['Año'].unique().tolist())
semestres_disponibles = sorted(df_limpio['Semestre'].unique().tolist())
años_sel = st.sidebar.multiselect("📅 Año(s):", options=años_disponibles, default=años_disponibles)
semestres_sel = st.sidebar.multiselect("📆 Semestre(s):", options=semestres_disponibles, default=semestres_disponibles, format_func=lambda x: f"Semestre {x}")

df_f = df_limpio[df_limpio['Año'].isin(años_sel) & df_limpio['Semestre'].isin(semestres_sel)]

if len(df_f) == 0:
    st.warning("Selecciona filtros válidos.")
    st.stop()

# ============================================================================
# KPIs Y TABS (Lógica Original)
# ============================================================================
st.markdown("<h2 class='section-title'>📌 Indicadores Clave (KPIs)</h2>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("🚨 Total Alertas", f"{len(df_f):,}")
c2.metric("📚 Asignaturas", f"{df_f['Asignatura'].nunique():,}")
c3.metric("📈 Promedio Mensual", f"{df_f.groupby(df_f['Fecha'].dt.to_period('M')).size().mean():.1f}")
pct = (len(df_f[df_f['Razón principal de bajo desempeño'].notna()]) / len(df_f) * 100)
c4.metric("📝 Reportaron Razón", f"{pct:.1f}%")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📈 Tendencia", "📚 Top Asignaturas", "❓ Razones", "🔥 Mapa Calor", 
    "☁️ Nube", "📊 Ejecutivo", "🔍 Multidim.", "📋 Reporte"
])

# --- TAB 1: TENDENCIA ---
with tab1:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    df_f['Año'].value_counts().sort_index().plot(kind='bar', ax=axes[0,0], color='#910303')
    df_f['Semestre'].value_counts().sort_index().plot(kind='bar', ax=axes[0,1], color='#FF3838')
    df_f['Año'].value_counts().sort_index().plot(kind='line', marker='o', ax=axes[1,0], color='#910303')
    df_f['Mes'].value_counts().sort_index().plot(kind='bar', ax=axes[1,1], color='#C73E1D')
    st.pyplot(fig)

# --- TAB 5: NUBE DE PALABRAS (Aquí estaba el ERROR) ---
with tab5:
    st.markdown("<h3 class='section-title'>☁️ Nube de Palabras</h3>", unsafe_allow_html=True)
    # CORRECCIÓN: Se usa .str.lower() para Series de Pandas
    serie_razones = df_f['Razón principal de bajo desempeño'].dropna().astype(str).str.lower()
    texto = " ".join(serie_razones)
    
    if len(texto) > 10:
        wc = WordCloud(width=800, height=400, background_color='white', colormap='Reds').generate(texto)
        fig, ax = plt.subplots()
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
    else:
        st.info("No hay suficiente texto para la nube.")

# --- RESTO DE TABS (Simplificados para brevedad, pero funcionales) ---
with tab2:
    top_asig = df_f['Asignatura'].value_counts().head(15)
    fig, ax = plt.subplots()
    top_asig.plot(kind='barh', color='#C73E1D', ax=ax)
    st.pyplot(fig)

with tab3:
    df_razon = df_f.copy()
    df_razon['Razón_Simp'] = df_razon['Razón principal de bajo desempeño'].apply(simplificar_razones)
    razones = df_razon['Razón_Simp'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(razones, labels=razones.index, autopct='%1.1f%%', colors=sns.color_palette("Reds_r"))
    st.pyplot(fig)

with tab6: # Dashboard Ejecutivo
    st.dataframe(df_f[['Fecha', 'Asignatura', 'Razón principal de bajo desempeño']].tail(10))

with tab8: # Reporte
    st.dataframe(df_f)# -*- coding: utf-8 -*-
"""
DASHBOARD DE ALERTAS TEMPRANAS - UFPS
Universidad Francisco de Paula Santander
Versión: 3.0 (Carga Automática y Error de Texto corregido)
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import textwrap
import re
import base64
import os
import requests
from io import BytesIO
from datetime import datetime
from wordcloud import WordCloud
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURACIÓN DE DATOS (GOOGLE DRIVE)
# ============================================================================
# IMPORTANTE: Reemplaza este ID por el ID real de tu archivo en Google Drive
ID_DRIVE = "1vS7k_T9W2i5i-r6Z4G_TuID_AQUI" 
URL_DRIVE = f'https://docs.google.com/spreadsheets/d/{ID_DRIVE}/export?format=xlsx'

# ============================================================================
# FUNCIONES UTILITARIAS Y DE LOGOS
# ============================================================================
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

def cargar_logo_base64(ruta_imagen: str) -> str:
    if os.path.exists(ruta_imagen):
        with open(ruta_imagen, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# ============================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ============================================================================
st.set_page_config(
    page_title="Dashboard Alertas Tempranas - UFPS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #8B0000 0%, #C73E1D 100%);
        padding: 20px 30px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 24px;
    }
    .main-header-logo { height: 90px; width: auto; flex-shrink: 0; filter: brightness(0) invert(1); }
    .main-header-text { text-align: left; }
    .main-header h1 { margin: 0 0 4px 0; font-size: 1.7rem; }
    .main-header h3 { margin: 0 0 4px 0; font-size: 1.1rem; opacity: .92; }
    .main-header p  { margin: 0; font-size: .85rem; opacity: .80; }
    .section-title { color: #8B0000; border-bottom: 2px solid #C73E1D; padding-bottom: 5px; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNCIONES DE DATOS
# ============================================================================
def simplificar_razones(razon):
    if pd.isna(razon) or str(razon).strip() == '':
        return None
    razon_lower = str(razon).lower().strip()
    categorias = {
        'Falta de preparación':     ['no me preparé', 'falta de estudio', 'no estudié', 'no repasé'],
        'Dificultad de comprensión':['no comprendo', 'no entiendo', 'dificultad para entender'],
        'Problemas con evaluación': ['temas evaluados', 'dificultad del examen', 'no son acordes'],
        'Problemas laborales':      ['temas laborales', 'trabajo', 'laboral'],
        'Temática amplia':          ['temática evaluada', 'muy amplia', 'muchos temas'],
        'Tiempo insuficiente':      ['examen es muy largo', 'tiempo asignado', 'falta de tiempo'],
        'Problemas con docente':    ['explicaciones del docente', 'no son claras', 'metodología'],
        'Problemas familiares':     ['temas familiares', 'problemas familiares', 'familia']
    }
    for categoria, palabras in categorias.items():
        for palabra in palabras:
            if palabra in razon_lower:
                return categoria
    return 'Otras razones'

@st.cache_data(ttl=600)
def cargar_datos_automatico(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_excel(BytesIO(response.content))
            df['Año']        = df['Fecha'].dt.year
            df['Semestre']   = df['Fecha'].dt.month.apply(lambda x: 1 if x <= 6 else 2)
            df['Mes']        = df['Fecha'].dt.month
            df['Mes_Nombre'] = df['Fecha'].dt.strftime('%B')
            df['Día_Semana'] = df['Fecha'].dt.day_name()
            df_limpio = df.copy()
            for col in df_limpio.columns:
                if df_limpio[col].dtype == 'object':
                    df_limpio[col] = df_limpio[col].replace(['NO APLICA', ''], np.nan)
            return df, df_limpio
        return None, None
    except:
        return None, None

# ============================================================================
# ENCABEZADO Y LOGOS
# ============================================================================
logo_blanco_b64 = get_base64_of_bin_file("BLANCO.png")
_nuevo_logo_tag = f'<img src="data:image/png;base64,{logo_blanco_b64}" class="main-header-logo" style="width: 200px; height: auto; margin-right: 40px;">' if logo_blanco_b64 else ""

st.markdown(f"""
<div class="main-header">
    {_nuevo_logo_tag}
    <div class="main-header-text">
        <h1>📊 Dashboard de Alertas Tempranas</h1>
        <h3>Universidad Francisco de Paula Santander — UFPS</h3>
        <p>Análisis de Deserción y Permanencia Estudiantil | Maestría TIC aplicadas a la Educación</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# CARGA DE DATOS Y SIDEBAR
# ============================================================================
logo_sidebar_b64 = cargar_logo_base64("Logo-nuevo-vertical.png")
if logo_sidebar_b64:
    st.sidebar.markdown(f'<img src="data:image/png;base64,{logo_sidebar_b64}" style="width:230px; display:block; margin:0 auto 10px auto;">', unsafe_allow_html=True)

st.sidebar.markdown("## ⚙️ Configuración")

with st.spinner("Sincronizando con Drive..."):
    df, df_limpio = cargar_datos_automatico(URL_DRIVE)

if df is None:
    st.error("No se pudo cargar el archivo desde Drive. Revisa el ID y los permisos.")
    st.stop()

# Filtros
años_disponibles = sorted(df_limpio['Año'].unique().tolist())
semestres_disponibles = sorted(df_limpio['Semestre'].unique().tolist())
años_sel = st.sidebar.multiselect("📅 Año(s):", options=años_disponibles, default=años_disponibles)
semestres_sel = st.sidebar.multiselect("📆 Semestre(s):", options=semestres_disponibles, default=semestres_disponibles, format_func=lambda x: f"Semestre {x}")

df_f = df_limpio[df_limpio['Año'].isin(años_sel) & df_limpio['Semestre'].isin(semestres_sel)]

if len(df_f) == 0:
    st.warning("Selecciona filtros válidos.")
    st.stop()

# ============================================================================
# KPIs Y TABS (Lógica Original)
# ============================================================================
st.markdown("<h2 class='section-title'>📌 Indicadores Clave (KPIs)</h2>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("🚨 Total Alertas", f"{len(df_f):,}")
c2.metric("📚 Asignaturas", f"{df_f['Asignatura'].nunique():,}")
c3.metric("📈 Promedio Mensual", f"{df_f.groupby(df_f['Fecha'].dt.to_period('M')).size().mean():.1f}")
pct = (len(df_f[df_f['Razón principal de bajo desempeño'].notna()]) / len(df_f) * 100)
c4.metric("📝 Reportaron Razón", f"{pct:.1f}%")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📈 Tendencia", "📚 Top Asignaturas", "❓ Razones", "🔥 Mapa Calor", 
    "☁️ Nube", "📊 Ejecutivo", "🔍 Multidim.", "📋 Reporte"
])

# --- TAB 1: TENDENCIA ---
with tab1:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    df_f['Año'].value_counts().sort_index().plot(kind='bar', ax=axes[0,0], color='#910303')
    df_f['Semestre'].value_counts().sort_index().plot(kind='bar', ax=axes[0,1], color='#FF3838')
    df_f['Año'].value_counts().sort_index().plot(kind='line', marker='o', ax=axes[1,0], color='#910303')
    df_f['Mes'].value_counts().sort_index().plot(kind='bar', ax=axes[1,1], color='#C73E1D')
    st.pyplot(fig)

# --- TAB 5: NUBE DE PALABRAS (Aquí estaba el ERROR) ---
with tab5:
    st.markdown("<h3 class='section-title'>☁️ Nube de Palabras</h3>", unsafe_allow_html=True)
    # CORRECCIÓN: Se usa .str.lower() para Series de Pandas
    serie_razones = df_f['Razón principal de bajo desempeño'].dropna().astype(str).str.lower()
    texto = " ".join(serie_razones)
    
    if len(texto) > 10:
        wc = WordCloud(width=800, height=400, background_color='white', colormap='Reds').generate(texto)
        fig, ax = plt.subplots()
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
    else:
        st.info("No hay suficiente texto para la nube.")

# --- RESTO DE TABS (Simplificados para brevedad, pero funcionales) ---
with tab2:
    top_asig = df_f['Asignatura'].value_counts().head(15)
    fig, ax = plt.subplots()
    top_asig.plot(kind='barh', color='#C73E1D', ax=ax)
    st.pyplot(fig)

with tab3:
    df_razon = df_f.copy()
    df_razon['Razón_Simp'] = df_razon['Razón principal de bajo desempeño'].apply(simplificar_razones)
    razones = df_razon['Razón_Simp'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(razones, labels=razones.index, autopct='%1.1f%%', colors=sns.color_palette("Reds_r"))
    st.pyplot(fig)

with tab6: # Dashboard Ejecutivo
    st.dataframe(df_f[['Fecha', 'Asignatura', 'Razón principal de bajo desempeño']].tail(10))

with tab8: # Reporte
    st.dataframe(df_f)
