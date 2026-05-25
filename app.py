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
ID_DRIVE = "TU_ID_DE_ARCHIVO_AQUI" 
URL_DRIVE = f'https://docs.google.com/spreadsheets/d/{ID_DRIVE}/export?format=xlsx'

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
