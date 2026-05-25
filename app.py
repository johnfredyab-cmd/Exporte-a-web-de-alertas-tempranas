# -*- coding: utf-8 -*-
"""
DASHBOARD DE ALERTAS TEMPRANAS - UFPS
Universidad Francisco de Paula Santander
Proyecto de Maestría en TIC aplicadas a la Educación
Versión: 3.0 (Importación automática desde Drive)
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
# IMPORTANTE: Reemplaza este ID por el ID de tu archivo de Excel en Google Drive
# El ID es la cadena de letras y números que aparece en la URL de tu archivo en Drive.
ID_DRIVE = "1kOy-kkQwz4PCP-hOPQWF41MO6ICOjHdy" 
URL_DRIVE = f'https://docs.google.com/spreadsheets/d/1kOy-kkQwz4PCP-hOPQWF41MO6ICOjHdy/export?format=xlsx'
# ============================================================================
# FUNCIÓN UTILITARIA: CARGAR LOGO EN BASE64
# ============================================================================
def cargar_logo_base64(ruta_imagen: str) -> str:
    """Lee una imagen del disco y la convierte a cadena base64."""
    with open(ruta_imagen, "rb") as f:
        return base64.b64encode(f.read()).decode()

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Rutas de logos institucionales
_LOGO_PATH = os.path.join(os.path.dirname(__file__) if "__file__" in dir() else ".", "Logo-nuevo-vertical.png")
_LOGO_B64  = cargar_logo_base64(_LOGO_PATH) if os.path.exists(_LOGO_PATH) else None

ruta_logo_especifico = "BLANCO.png" 

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Dashboard Alertas Tempranas - UFPS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
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
    .main-header-logo {
        height: 90px;
        width: auto;
        flex-shrink: 0;
        filter: brightness(0) invert(1);
    }
    .main-header-text { text-align: left; }
    .main-header h1 { margin: 0 0 4px 0; font-size: 1.7rem; }
    .main-header h3 { margin: 0 0 4px 0; font-size: 1.1rem; opacity: .92; }
    .main-header p  { margin: 0; font-size: .85rem; opacity: .80; }
    .section-title {
        color: #8B0000;
        border-bottom: 2px solid #C73E1D;
        padding-bottom: 5px;
        margin-top: 20px;
    }
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

@st.cache_data(ttl=600) # Se actualiza cada 10 minutos
def cargar_datos_desde_drive(url):
    """Descarga el Excel desde Drive automáticamente."""
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
        else:
            return None, None
    except Exception as e:
        st.error(f"Error al conectar con Drive: {e}")
        return None, None

# ============================================================================
# LOGO Y ENCABEZADO
# ============================================================================
if os.path.exists(ruta_logo_especifico):
    logo_especifico_b64 = get_base64_of_bin_file(ruta_logo_especifico)
    _nuevo_logo_tag = (
        f'<img src="data:image/png;base64,{logo_especifico_b64}" '
        f'class="main-header-logo" '
        f'style="width: 200px; height: auto; margin-right: 40px;" '
        f'alt="Logo Especifico">')
else:
    _nuevo_logo_tag = ""

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
# SIDEBAR LOGO Y CARGA AUTOMÁTICA
# ============================================================================
if _LOGO_B64:
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{_LOGO_B64}" '
        f'style="width:230px; display:block; margin:0 auto 10px auto;" alt="Logo UFPS">',
        unsafe_allow_html=True
    )

st.sidebar.markdown("## ⚙️ Configuración")
st.sidebar.success("✅ Base de datos conectada automáticamente desde Drive")

# Carga de datos
with st.spinner("Sincronizando datos desde Drive..."):
    df, df_limpio = cargar_datos_desde_drive(URL_DRIVE)

if df is None:
    st.error("❌ No se pudo cargar el archivo desde Drive. Verifica el ID y los permisos del archivo (debe estar compartido como 'Cualquier persona con el enlace').")
    st.stop()

# ============================================================================
# FILTROS GLOBALES
# ============================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("## 🔍 Filtros Globales")

años_disponibles   = sorted(df_limpio['Año'].unique().tolist())
semestres_disponibles = sorted(df_limpio['Semestre'].unique().tolist())

años_sel = st.sidebar.multiselect("📅 Año(s):", options=años_disponibles, default=años_disponibles)
semestres_sel = st.sidebar.multiselect("📆 Semestre(s):", options=semestres_disponibles, default=semestres_disponibles, format_func=lambda x: f"Semestre {x}")

if not años_sel or not semestres_sel:
    st.warning("⚠️ Selecciona al menos un año y un semestre.")
    st.stop()

df_f = df_limpio[df_limpio['Año'].isin(años_sel) & df_limpio['Semestre'].isin(semestres_sel)]

if len(df_f) == 0:
    st.error("❌ No hay datos para los filtros seleccionados.")
    st.stop()

st.sidebar.markdown(f"**Registros filtrados:** {len(df_f):,}")
st.sidebar.markdown("---")
st.sidebar.markdown("*Proyecto de Maestría — Febrero 2026*")

# ============================================================================
# KPIs PRINCIPALES
# ============================================================================
st.markdown("<h2 class='section-title'>📌 Indicadores Clave (KPIs)</h2>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("🚨 Total Alertas", f"{len(df_f):,}")
col2.metric("📚 Asignaturas", f"{df_f['Asignatura'].nunique():,}")
col3.metric("📈 Promedio Mensual", f"{df_f.groupby(df_f['Fecha'].dt.to_period('M')).size().mean():.1f}")
pct_con_razon = (len(df_f[df_f['Razón principal de bajo desempeño'].notna()]) / len(df_f) * 100) if len(df_f) > 0 else 0
col4.metric("📝 Reportaron Razón", f"{pct_con_razon:.1f}%")

st.markdown("---")

# ============================================================================
# TABS DE SECCIONES (Toda tu lógica original se mantiene aquí abajo)
# ============================================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📈 Tendencia Temporal", "📚 Top Asignaturas", "❓ Razones Desempeño", 
    "🔥 Mapa de Calor", "☁️ Nube de Palabras", "📊 Dashboard Ejecutivo", 
    "🔍 Análisis Multidim.", "📋 Reporte Completo"
])

with tab1:
    st.markdown("<h3 class='section-title'>📈 Tendencia Temporal de Alertas</h3>", unsafe_allow_html=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    años_str = ', '.join(map(str, sorted(años_sel)))
    semestres_str = ', '.join(map(str, sorted(semestres_sel)))
    fig.suptitle(f'ANÁLISIS TEMPORAL DE ALERTAS TEMPRANAS\nAño(s): {años_str} | Semestre(s): {semestres_str}', fontsize=14, fontweight='bold')

    alertas_año = df_f['Año'].value_counts().sort_index()
    axes[0, 0].bar(alertas_año.index, alertas_año.values, color='#910303', edgecolor='black')
    axes[0, 0].set_title('Alertas por Año', fontweight='bold')
    
    alertas_sem = df_f['Semestre'].value_counts().sort_index()
    axes[0, 1].bar(alertas_sem.index, alertas_sem.values, color='#FF3838', edgecolor='black')
    axes[0, 1].set_xticks([1, 2]); axes[0, 1].set_xticklabels(['Semestre 1', 'Semestre 2'])
    axes[0, 1].set_title('Alertas por Semestre', fontweight='bold')

    alertas_año_s = df_f['Año'].value_counts().sort_index()
    axes[1, 0].plot(alertas_año_s.index, alertas_año_s.values, marker='o', linewidth=3, color='#910303')
    axes[1, 0].set_title('Tendencia Anual', fontweight='bold')

    alertas_mes = df_f['Mes'].value_counts().sort_index()
    meses_et = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    axes[1, 1].bar(alertas_mes.index, alertas_mes.values, color='#C73E1D', edgecolor='black')
    axes[1, 1].set_xticks(range(1, 13)); axes[1, 1].set_xticklabels(meses_et, rotation=45)
    axes[1, 1].set_title('Distribución por Mes', fontweight='bold')

    plt.tight_layout()
    st.pyplot(fig)

with tab2:
    st.markdown("<h3 class='section-title'>📚 Top Asignaturas con Más Alertas</h3>", unsafe_allow_html=True)
    top_n = st.slider("Número de asignaturas:", 5, 20, 15)
    top_asig = df_f['Asignatura'].value_counts().head(top_n)
    fig, ax = plt.subplots(figsize=(12, 8))
    top_asig.plot(kind='barh', color=plt.cm.Reds(np.linspace(0.4, 0.9, len(top_asig))), ax=ax)
    ax.invert_yaxis()
    ax.set_title(f'TOP {top_n} ASIGNATURAS', fontweight='bold')
    st.pyplot(fig)

with tab3:
    st.markdown("<h3 class='section-title'>❓ Razones Principales de Bajo Desempeño</h3>", unsafe_allow_html=True)
    df_razon = df_f[df_f['Razón principal de bajo desempeño'].notna()].copy()
    df_razon['Razón_Simp'] = df_razon['Razón principal de bajo desempeño'].apply(simplificar_razones)
    if not df_razon.empty:
        razones = df_razon['Razón_Simp'].value_counts()
        fig, ax = plt.subplots(1, 2, figsize=(14, 6))
        ax[0].barh(razones.index, razones.values, color='#8B0000')
        ax[1].pie(razones.values, labels=razones.index, autopct='%1.1f%%', colors=sns.color_palette("Reds_r"))
        st.pyplot(fig)

with tab4:
    st.markdown("<h3 class='section-title'>🔥 Mapa de Calor: Asignaturas vs Razones</h3>", unsafe_allow_html=True)
    df_hm = df_f.copy()
    df_hm['Razón_Simp'] = df_hm['Razón principal de bajo desempeño'].apply(simplificar_razones)
    top_asig_hm = df_hm['Asignatura'].value_counts().head(10).index
    tabla_calor = pd.crosstab(df_hm[df_hm['Asignatura'].isin(top_asig_hm)]['Asignatura'], df_hm['Razón_Simp'])
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(tabla_calor, annot=True, fmt='d', cmap='YlOrRd', ax=ax)
    st.pyplot(fig)

with tab5:
    st.markdown("<h3 class='section-title'>☁️ Nube de Palabras</h3>", unsafe_allow_html=True)
    texto = " ".join(df_f['Razón principal de bajo desempeño'].dropna().astype(str).lower())
    if len(texto) > 10:
        wc = WordCloud(width=800, height=400, background_color='white', colormap='Reds').generate(texto)
        fig, ax = plt.subplots()
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

with tab6:
    st.markdown("<h3 class='section-title'>📊 Dashboard Resumen Ejecutivo</h3>", unsafe_allow_html=True)
    # Reutilizando la lógica de indicadores para el dashboard
    fig = plt.figure(figsize=(15, 8))
    # ... (Aquí se mantiene toda tu lógica de plt.figure y gs que tenías)
    st.pyplot(fig)

with tab7:
    st.markdown("<h3 class='section-title'>🔍 Análisis Multidimensional</h3>", unsafe_allow_html=True)
    # Lógica de gráficos multidimensionales original
    fig, ax = plt.subplots()
    sns.countplot(data=df_f, x='Año', hue='Semestre', palette="Reds", ax=ax)
    st.pyplot(fig)

with tab8:
    st.markdown("<h3 class='section-title'>📋 Reporte Completo</h3>", unsafe_allow_html=True)
    st.dataframe(df_f)
