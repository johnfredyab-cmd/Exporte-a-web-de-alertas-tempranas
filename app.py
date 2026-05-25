# -*- coding: utf-8 -*-
"""
DASHBOARD DE ALERTAS TEMPRANAS - UFPS
Universidad Francisco de Paula Santander
Proyecto de Maestría en TIC aplicadas a la Educación
Versión: 3.0 (Carga Automática y Logo Ajustado)
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
# CONFIGURACIÓN DE DATOS (GOOGLE DRIVE) https://docs.google.com/spreadsheets/d/1kOy-kkQwz4PCP-hOPQWF41MO6ICOjHdy/edit?usp=sharing&ouid=115985076438086553034&rtpof=true&sd=true
# ============================================================================
# Reemplaza con el ID de tu archivo de Google Drive
ID_DRIVE = "1kOy-kkQwz4PCP-hOPQWF41MO6ICOjHdy" 
URL_DRIVE = f'https://docs.google.com/spreadsheets/d/1kOy-kkQwz4PCP-hOPQWF41MO6ICOjHdy/export?format=xlsx'

# ============================================================================
# FUNCIONES UTILITARIAS
# ============================================================================

def get_base64_of_bin_file(bin_file):
    """Convierte imagen local a base64."""
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

def simplificar_razones(razon):
    """Agrupa razones similares en categorías principales."""
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
def cargar_datos_drive(url):
    """Carga datos directamente desde Drive."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_excel(BytesIO(response.content))
            # Preparación de fechas
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
        st.error(f"Error de conexión: {e}")
        return None, None

# ============================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ============================================================================
st.set_page_config(page_title="Dashboard Alertas UFPS", page_icon="🎓", layout="wide")

# Carga de logos
logo_ufps_b64 = get_base64_of_bin_file("Logo-nuevo-vertical.png") # Para sidebar
logo_blanco_b64 = get_base64_of_bin_file("BLANCO.png")           # Para encabezado

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #8B0000 0%, #C73E1D 100%);
        padding: 20px 30px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 30px;
    }
    .main-header-text { text-align: left; }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header h3 { margin: 5px 0; font-size: 1.1rem; opacity: 0.9; }
    .main-header p  { margin: 0; font-size: 0.85rem; opacity: 0.8; }
    .section-title { color: #8B0000; border-bottom: 2px solid #C73E1D; padding-bottom: 5px; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# ENCABEZADO
# ============================================================================
_logo_tag = f'<img src="data:image/png;base64,{logo_blanco_b64}" style="width: 220px; height: auto;">' if logo_blanco_b64 else ""

st.markdown(f"""
<div class="main-header">
    {_logo_tag}
    <div class="main-header-text">
        <h1>📊 Dashboard de Alertas Tempranas</h1>
        <h3>Universidad Francisco de Paula Santander — UFPS</h3>
        <p>Análisis de Deserción y Permanencia Estudiantil | Maestría TIC aplicadas a la Educación</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# CARGA AUTOMÁTICA DE DATOS
# ============================================================================
with st.spinner("Sincronizando con Google Drive..."):
    df, df_limpio = cargar_datos_drive(URL_DRIVE)

if df is None:
    st.error("❌ No se pudo cargar el archivo desde Drive. Verifica el ID y los permisos de compartir.")
    st.stop()

# ============================================================================
# SIDEBAR Y FILTROS
# ============================================================================
if logo_ufps_b64:
    st.sidebar.markdown(f'<img src="data:image/png;base64,{logo_ufps_b64}" style="width:200px; display:block; margin:0 auto 10px auto;">', unsafe_allow_html=True)

st.sidebar.title("⚙️ Configuración")
st.sidebar.success("✅ Datos sincronizados con Drive")

años_disponibles = sorted(df_limpio['Año'].unique().tolist())
semestres_disponibles = sorted(df_limpio['Semestre'].unique().tolist())

años_sel = st.sidebar.multiselect("📅 Año(s):", options=años_disponibles, default=años_disponibles)
semestres_sel = st.sidebar.multiselect("📆 Semestre(s):", options=semestres_disponibles, default=semestres_disponibles, format_func=lambda x: f"Semestre {x}")

df_f = df_limpio[df_limpio['Año'].isin(años_sel) & df_limpio['Semestre'].isin(semestres_sel)]

if len(df_f) == 0:
    st.warning("Selecciona filtros válidos en el panel lateral.")
    st.stop()

# ============================================================================
# KPIs
# ============================================================================
st.markdown("<h2 class='section-title'>📌 Indicadores Clave (KPIs)</h2>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("🚨 Total Alertas", f"{len(df_f):,}")
c2.metric("📚 Asignaturas", f"{df_f['Asignatura'].nunique():,}")
c3.metric("📈 Prom. Mensual", f"{df_f.groupby(df_f['Fecha'].dt.to_period('M')).size().mean():.1f}")
c4.metric("📝 % Con Razón", f"{(len(df_f[df_f['Razón principal de bajo desempeño'].notna()]) / len(df_f) * 100):.1f}%")

# ============================================================================
# TABS DE ANÁLISIS
# ============================================================================
tabs = st.tabs(["📈 Tendencia", "📚 Top Asignaturas", "❓ Razones", "🔥 Mapa Calor", "☁️ Nube", "📊 Ejecutivo", "🔍 Multidim."])

# --- TAB 1: TENDENCIA ---
with tabs[0]:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    df_f['Año'].value_counts().sort_index().plot(kind='bar', ax=axes[0], color='#8B0000', title="Alertas por Año")
    df_f['Mes_Nombre'].value_counts().plot(kind='line', ax=axes[1], marker='o', color='#C73E1D', title="Tendencia Mensual")
    st.pyplot(fig)

# --- TAB 2: TOP ASIGNATURAS ---
with tabs[1]:
    top_asig = df_f['Asignatura'].value_counts().head(15)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=top_asig.values, y=[textwrap.fill(a, 30) for a in top_asig.index], palette="Reds_r", ax=ax)
    ax.set_title("Top Asignaturas con Mayor Alerta")
    st.pyplot(fig)

# --- TAB 3: RAZONES ---
with tabs[2]:
    df_razon = df_f.copy()
    df_razon['Razón_Simp'] = df_razon['Razón principal de bajo desempeño'].apply(simplificar_razones)
    razones = df_razon['Razón_Simp'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(razones, labels=razones.index, autopct='%1.1f%%', colors=sns.color_palette("Reds"))
    st.pyplot(fig)

# --- TAB 4: MAPA DE CALOR ---
with tabs[3]:
    df_razon['Razón_Simp'] = df_razon['Razón principal de bajo desempeño'].apply(simplificar_razones)
    top_asig_hm = df_razon['Asignatura'].value_counts().head(10).index
    df_hm = df_razon[df_razon['Asignatura'].isin(top_asig_hm)]
    tabla = pd.crosstab(df_hm['Asignatura'], df_hm['Razón_Simp'])
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(tabla, annot=True, cmap="YlOrRd", ax=ax)
    st.pyplot(fig)

# --- TAB 5: NUBE DE PALABRAS ---
with tabs[4]:
    texto = " ".join(df_f['Razón principal de bajo desempeño'].dropna().astype(str))
    if len(texto) > 10:
        wc = WordCloud(width=800, height=400, background_color='white', colormap='Reds').generate(texto)
        fig, ax = plt.subplots()
        ax.imshow(wc)
        ax.axis('off')
        st.pyplot(fig)

# --- TAB 6: EJECUTIVO ---
with tabs[5]:
    st.info("Resumen de gestión académica proyectado para el periodo seleccionado.")
    st.dataframe(df_f[['Fecha', 'Asignatura', 'Razón principal de bajo desempeño']].tail(10))

# --- TAB 7: MULTIDIMENSIONAL ---
with tabs[6]:
    fig = plt.figure(figsize=(10, 6))
    sns.countplot(data=df_f, x='Año', hue='Semestre', palette="Reds")
    st.pyplot(fig)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Registros:** {len(df_f):,}")
st.sidebar.write("UFPS - Maestría TIC 2026")
