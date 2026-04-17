# -*- coding: utf-8 -*-
"""
DASHBOARD DE ALERTAS TEMPRANAS - UFPS
Universidad Francisco de Paula Santander
Proyecto de Maestría en TIC aplicadas a la Educación
Versión: 2.0 (Streamlit)
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import textwrap
import re
from datetime import datetime
from wordcloud import WordCloud
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Dashboard Alertas Tempranas - UFPS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado con colores institucionales UFPS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #8B0000 0%, #C73E1D 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #C73E1D;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    .section-title {
        color: #8B0000;
        border-bottom: 2px solid #C73E1D;
        padding-bottom: 5px;
        margin-top: 20px;
    }
    .stSelectbox label { font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNCIONES DE DATOS
# ============================================================================

def simplificar_razones(razon):
    """Agrupa razones similares en categorías principales"""
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


@st.cache_data
def cargar_datos(archivo):
    """Carga y prepara los datos para el análisis"""
    df = pd.read_excel(archivo)
    df['Año']        = df['Fecha'].dt.year
    df['Semestre']   = df['Fecha'].dt.month.apply(lambda x: 1 if x <= 6 else 2)
    df['Mes']        = df['Fecha'].dt.month
    df['Mes_Nombre'] = df['Fecha'].dt.strftime('%B')
    df['Día_Semana'] = df['Fecha'].dt.day_name()

    df_limpio = df.copy()
    for col in df_limpio.columns:
        if df_limpio[col].dtype == 'object':
            df_limpio[col] = df_limpio[col].replace('NO APLICA', np.nan)
            df_limpio[col] = df_limpio[col].replace('', np.nan)
    return df, df_limpio


# ============================================================================
# ENCABEZADO PRINCIPAL
# ============================================================================
st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard de Alertas Tempranas</h1>
    <h3>Universidad Francisco de Paula Santander — UFPS</h3>
    <p>Análisis de Deserción y Permanencia Estudiantil | Maestría TIC aplicadas a la Educación</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# CARGA DE ARCHIVO
# ============================================================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Escudo_UFPS.png/200px-Escudo_UFPS.png",
                 width=120)
st.sidebar.markdown("## ⚙️ Configuración")
archivo = st.sidebar.file_uploader(
    "📂 Cargar archivo Excel (.xlsx)",
    type=["xlsx"],
    help="Sube el archivo consolidado de alertas tempranas de la UFPS"
)

if archivo is None:
    st.info("👆 Por favor, carga el archivo Excel con los datos de alertas tempranas desde el panel lateral izquierdo.")
    st.markdown("""
    ### ¿Qué contiene este dashboard?
    Una vez cargues el archivo verás:
    - 📈 **Tendencia temporal** de alertas por año, semestre y mes
    - 📚 **Top asignaturas** con mayor número de alertas
    - ❓ **Razones de bajo desempeño** categorizadas
    - 🔥 **Mapa de calor** asignaturas vs razones
    - ☁️ **Nube de palabras** de razones personales y académicas
    - 📊 **Dashboard ejecutivo** con KPIs principales
    - 🔍 **Análisis multidimensional** de razones
    - 📋 **Reporte completo** con recomendaciones
    """)
    st.stop()

# Cargar datos
with st.spinner("Cargando datos..."):
    df, df_limpio = cargar_datos(archivo)

# ============================================================================
# FILTROS GLOBALES EN SIDEBAR
# ============================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("## 🔍 Filtros Globales")

años_disponibles   = sorted(df_limpio['Año'].unique().tolist())
semestres_disponibles = sorted(df_limpio['Semestre'].unique().tolist())

años_sel = st.sidebar.multiselect(
    "📅 Año(s):",
    options=años_disponibles,
    default=años_disponibles
)
semestres_sel = st.sidebar.multiselect(
    "📆 Semestre(s):",
    options=semestres_disponibles,
    default=semestres_disponibles,
    format_func=lambda x: f"Semestre {x}"
)

# Validación de filtros
if not años_sel or not semestres_sel:
    st.warning("⚠️ Selecciona al menos un año y un semestre en el panel lateral.")
    st.stop()

# Aplicar filtros globales
df_f = df_limpio[
    df_limpio['Año'].isin(años_sel) &
    df_limpio['Semestre'].isin(semestres_sel)
]

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

total_alertas     = len(df_f)
total_asignaturas = df_f['Asignatura'].nunique()
promedio_mes      = df_f.groupby(df_f['Fecha'].dt.to_period('M')).size().mean()
df_con_razon_kpi  = df_f[df_f['Razón principal de bajo desempeño'].notna()]
pct_con_razon     = (len(df_con_razon_kpi) / total_alertas * 100) if total_alertas > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("🚨 Total Alertas",       f"{total_alertas:,}")
col2.metric("📚 Asignaturas",          f"{total_asignaturas:,}")
col3.metric("📈 Promedio Mensual",     f"{promedio_mes:.1f}")
col4.metric("📝 Reportaron Razón",    f"{pct_con_razon:.1f}%")

st.markdown("---")

# ============================================================================
# TABS DE SECCIONES
# ============================================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📈 Tendencia Temporal",
    "📚 Top Asignaturas",
    "❓ Razones Desempeño",
    "🔥 Mapa de Calor",
    "☁️ Nube de Palabras",
    "📊 Dashboard Ejecutivo",
    "🔍 Análisis Multidim.",
    "📋 Reporte Completo"
])

# ============================================================================
# TAB 1 — TENDENCIA TEMPORAL
# ============================================================================
with tab1:
    st.markdown("<h3 class='section-title'>📈 Tendencia Temporal de Alertas</h3>", unsafe_allow_html=True)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    años_str     = ', '.join(map(str, sorted(años_sel)))
    semestres_str = ', '.join(map(str, sorted(semestres_sel)))
    fig.suptitle(f'ANÁLISIS TEMPORAL DE ALERTAS TEMPRANAS\nAño(s): {años_str} | Semestre(s): {semestres_str}',
                 fontsize=14, fontweight='bold')

    # 1. Alertas por año
    alertas_año = df_f['Año'].value_counts().sort_index()
    axes[0, 0].bar(alertas_año.index, alertas_año.values, color='#910303', edgecolor='black')
    axes[0, 0].set_title('Alertas por Año', fontweight='bold')
    axes[0, 0].set_xlabel('Año'); axes[0, 0].set_ylabel('Número de Alertas')
    axes[0, 0].grid(axis='y', alpha=0.3)
    for i, v in enumerate(alertas_año.values):
        axes[0, 0].text(alertas_año.index[i], v + 3, str(v), ha='center', fontweight='bold')

    # 2. Alertas por semestre
    alertas_sem = df_f['Semestre'].value_counts().sort_index()
    axes[0, 1].bar(alertas_sem.index, alertas_sem.values, color='#FF3838', edgecolor='black')
    axes[0, 1].set_title('Alertas por Semestre', fontweight='bold')
    axes[0, 1].set_xlabel('Semestre'); axes[0, 1].set_ylabel('Número de Alertas')
    axes[0, 1].set_xticks([1, 2]); axes[0, 1].set_xticklabels(['Semestre 1', 'Semestre 2'])
    axes[0, 1].grid(axis='y', alpha=0.3)
    for i, v in enumerate(alertas_sem.values):
        axes[0, 1].text(alertas_sem.index[i], v + 3, str(v), ha='center', fontweight='bold')

    # 3. Tendencia anual
    alertas_año_s = df_f['Año'].value_counts().sort_index()
    if len(alertas_año_s) > 0:
        axes[1, 0].plot(alertas_año_s.index, alertas_año_s.values,
                        marker='o', linewidth=3, markersize=12,
                        color='#910303', markerfacecolor='white', markeredgewidth=3)
        for año, val in alertas_año_s.items():
            axes[1, 0].text(año, val + 5, str(val), ha='center', fontweight='bold', fontsize=11)
        axes[1, 0].fill_between(alertas_año_s.index, alertas_año_s.values, alpha=0.2, color='#910303')
        axes[1, 0].set_xticks(alertas_año_s.index)
    axes[1, 0].set_title('Tendencia Anual', fontweight='bold')
    axes[1, 0].set_xlabel('Año'); axes[1, 0].set_ylabel('Número de Alertas')
    axes[1, 0].grid(True, alpha=0.3, linestyle='--')

    # 4. Distribución mensual
    alertas_mes = df_f['Mes'].value_counts().sort_index()
    meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    if len(alertas_mes) > 0:
        colores_meses = ['#C73E1D' if m <= 6 else '#695757' for m in alertas_mes.index]
        axes[1, 1].bar(alertas_mes.index, alertas_mes.values, color=colores_meses, edgecolor='black')
        axes[1, 1].set_xticks(range(1, 13)); axes[1, 1].set_xticklabels(meses, rotation=45, ha='right')
        for mes, val in alertas_mes.items():
            axes[1, 1].text(mes, val + 1, str(val), ha='center', fontweight='bold', fontsize=8)
        legend_el = [
            mpatches.Patch(facecolor='#C73E1D', label='Semestre 1 (Ene-Jun)'),
            mpatches.Patch(facecolor='#695757', label='Semestre 2 (Jul-Dic)')
        ]
        axes[1, 1].legend(handles=legend_el, loc='upper right', fontsize=8)
    axes[1, 1].set_title('Distribución por Mes', fontweight='bold')
    axes[1, 1].set_xlabel('Mes'); axes[1, 1].set_ylabel('Número de Alertas')
    axes[1, 1].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# ============================================================================
# TAB 2 — TOP ASIGNATURAS
# ============================================================================
with tab2:
    st.markdown("<h3 class='section-title'>📚 Top Asignaturas con Más Alertas</h3>", unsafe_allow_html=True)
    top_n = st.slider("Número de asignaturas a mostrar:", min_value=5, max_value=20, value=15)

    top_asig = df_f['Asignatura'].value_counts().head(top_n)
    etiquetas = [textwrap.fill(a, width=35) for a in top_asig.index]

    fig, ax = plt.subplots(figsize=(12, max(6, top_n * 0.5)))
    colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(top_asig)))
    barras = ax.barh(range(len(top_asig)), top_asig.values, color=colors, edgecolor='black', linewidth=1.2)
    ax.set_yticks(range(len(top_asig))); ax.set_yticklabels(etiquetas, fontsize=9)
    ax.set_xlabel('Número de Alertas', fontweight='bold')
    ax.set_title(f'TOP {len(top_asig)} ASIGNATURAS CON MÁS ALERTAS TEMPRANAS\nAño(s): {años_str} | Semestre(s): {semestres_str}',
                 fontsize=13, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    for i, v in enumerate(top_asig.values):
        ax.text(v + 0.5, i, str(v), va='center', fontweight='bold', fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# ============================================================================
# TAB 3 — RAZONES DE BAJO DESEMPEÑO
# ============================================================================
with tab3:
    st.markdown("<h3 class='section-title'>❓ Razones Principales de Bajo Desempeño</h3>", unsafe_allow_html=True)

    df_razon = df_f[df_f['Razón principal de bajo desempeño'].notna()].copy()
    df_razon['Razón_Simp'] = df_razon['Razón principal de bajo desempeño'].apply(simplificar_razones)
    df_razon = df_razon[df_razon['Razón_Simp'].notna()]

    if len(df_razon) == 0:
        st.warning("No hay datos de razones para los filtros seleccionados.")
    else:
        razones = df_razon['Razón_Simp'].value_counts()

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('ANÁLISIS DE RAZONES PRINCIPALES DE BAJO DESEMPEÑO', fontsize=14, fontweight='bold')

        etiquetas_r = [textwrap.fill(r, width=25) for r in razones.index]
        axes[0].barh(range(len(razones)), razones.values, color='#8B0000', edgecolor='black', linewidth=1.2)
        axes[0].set_yticks(range(len(razones))); axes[0].set_yticklabels(etiquetas_r, fontsize=9)
        axes[0].set_xlabel('Frecuencia', fontweight='bold')
        axes[0].set_title('Distribución por Categoría', fontweight='bold')
        axes[0].grid(axis='x', alpha=0.3)
        for i, v in enumerate(razones.values):
            axes[0].text(v + 0.3, i, str(v), va='center', fontweight='bold')

        colors_pie = plt.cm.Reds(np.linspace(0.3, 0.9, len(razones)))
        axes[1].pie(razones.values, labels=None, autopct='%1.1f%%',
                    colors=colors_pie, startangle=90,
                    textprops={'fontsize': 9, 'fontweight': 'bold'})
        axes[1].set_title('Distribución Porcentual', fontweight='bold')
        axes[1].legend(razones.index, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # Tabla resumen
        st.markdown("#### Tabla de Frecuencias")
        df_tabla = pd.DataFrame({'Razón': razones.index, 'Frecuencia': razones.values,
                                  'Porcentaje (%)': (razones.values / razones.sum() * 100).round(1)})
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 4 — MAPA DE CALOR
# ============================================================================
with tab4:
    st.markdown("<h3 class='section-title'>🔥 Mapa de Calor: Asignaturas vs Razones</h3>", unsafe_allow_html=True)
    top_n_hm = st.slider("Top asignaturas para el mapa:", min_value=5, max_value=15, value=12, key="hm")

    df_razon_hm = df_f[df_f['Razón principal de bajo desempeño'].notna()].copy()
    df_razon_hm['Razón_Simp'] = df_razon_hm['Razón principal de bajo desempeño'].apply(simplificar_razones)
    df_razon_hm = df_razon_hm[df_razon_hm['Razón_Simp'].notna()]

    if len(df_razon_hm) == 0:
        st.warning("No hay suficientes datos para el mapa de calor.")
    else:
        top_asig_hm = df_razon_hm['Asignatura'].value_counts().head(top_n_hm).index
        df_top_hm   = df_razon_hm[df_razon_hm['Asignatura'].isin(top_asig_hm)]
        tabla_calor  = pd.crosstab(df_top_hm['Asignatura'], df_top_hm['Razón_Simp'])
        tabla_calor.index   = [textwrap.fill(a, 25) for a in tabla_calor.index]
        tabla_calor.columns = [textwrap.fill(c, 20) for c in tabla_calor.columns]

        fig, ax = plt.subplots(figsize=(14, max(7, top_n_hm * 0.6)))
        sns.heatmap(tabla_calor, annot=True, fmt='d', cmap='YlOrRd',
                    linewidths=0.5, linecolor='gray', cbar_kws={'label': 'Frecuencia'}, ax=ax)
        ax.set_title(f'MAPA DE CALOR: ASIGNATURAS vs RAZONES\n(Top {top_n_hm} Asignaturas)',
                     fontsize=14, fontweight='bold')
        ax.set_xlabel('Razón de Bajo Desempeño', fontweight='bold')
        ax.set_ylabel('Asignatura', fontweight='bold')
        plt.xticks(rotation=40, ha='right', fontsize=8)
        plt.yticks(rotation=0, fontsize=8)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

# ============================================================================
# TAB 5 — NUBE DE PALABRAS
# ============================================================================
with tab5:
    st.markdown("<h3 class='section-title'>☁️ Nube de Palabras — Razones de Bajo Desempeño</h3>", unsafe_allow_html=True)

    stopwords_es = set([
        'de','la','que','el','en','y','a','los','del','se','las','por','un','para',
        'con','no','una','su','al','lo','como','más','pero','sus','le','ya','o',
        'este','sí','porque','esta','entre','cuando','muy','sin','sobre','también',
        'me','hasta','hay','donde','quien','desde','todo','nos','durante','todos',
        'uno','les','ni','contra','otros','ese','eso','ante','ellos','e','esto',
        'mí','antes','algunos','qué','unos','yo','otro','otras','otra','él','tanto',
        'esa','estos','mucho','quienes','nada','muchos','cual','poco','ella',
        'estas','algunas','algo','nosotros','mi','mis','tú','te','ti','tu','tus',
        'ellas','ser','estar','fue','ha','sido','son','estoy','está','han','hacer',
        'hizo','era','fueron','puede','dar','ver','decir','ir','vez','si',
        'además','cada','tal','ahora','aquí','día','forma','gran','haber','hemos',
        'mismo','nuevo','parte','tener','toda','tras','aún','dos','manera',
        'porque','debido','motivo','razón','razones','caso','situación','situaciones',
        'tema','temas','aspecto','aspectos','problema','problemas',
        'asignatura','asignaturas','materia','materias','clase','clases','tenía',
        'tengo','docente','docentes','profesor','profesores',
        'universidad','ufps','carrera','programa',
        'estudiante','estudiantes','creo','acorde',
        'parcial','parciales','examen','exámenes','nota','notas',
        'tiempo','momento','semestre','año','años','día','días','mes','meses',
        'tener','hacer','poder','sentir','estar','haber','ir','ver','dar'
    ])

    col_principal = 'Razón principal de bajo desempeño'
    col_personal  = 'Razón personal de bajo desempeño'

    razones_p = df_f[col_principal].dropna() if col_principal in df_f.columns else pd.Series(dtype=str)
    razones_per = df_f[col_personal].dropna() if col_personal in df_f.columns else pd.Series(dtype=str)

    top_asig_wc   = df_f['Asignatura'].value_counts().head(10).index.tolist()
    df_top_wc     = df_f[df_f['Asignatura'].isin(top_asig_wc)]
    razones_p_top = df_top_wc[col_principal].dropna() if col_principal in df_top_wc.columns else pd.Series(dtype=str)
    razones_per_top = df_top_wc[col_personal].dropna() if col_personal in df_top_wc.columns else pd.Series(dtype=str)

    texto_ponderado = (
        ' '.join(razones_p.astype(str)) + ' ' +
        ' '.join(razones_per.astype(str)) * 2 + ' ' +
        ' '.join(razones_p_top.astype(str)) + ' ' +
        ' '.join(razones_per_top.astype(str)) * 3
    )

    texto_limpio = re.sub(r'[^\w\s]', ' ', texto_ponderado.lower())
    palabras     = [p for p in texto_limpio.split() if p not in stopwords_es and len(p) > 3]
    texto_final  = ' '.join(palabras)

    if len(texto_final.strip()) < 10:
        st.warning("No hay suficiente texto para generar la nube de palabras con los filtros actuales.")
    else:
        wc = WordCloud(
            width=1200, height=600, background_color='white', colormap='Reds',
            max_words=250, relative_scaling=0.5, min_font_size=12, max_font_size=150,
            prefer_horizontal=0.8, collocations=False, contour_width=2, contour_color='#2C3E50'
        ).generate(texto_final)

        fig, ax = plt.subplots(figsize=(14, 8))
        fig.suptitle('NUBE DE PALABRAS – RAZONES DE BAJO DESEMPEÑO ACADÉMICO\nIntegración de razones académicas y personales',
                     fontsize=16, fontweight='bold')
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

# ============================================================================
# TAB 6 — DASHBOARD EJECUTIVO
# ============================================================================
with tab6:
    st.markdown("<h3 class='section-title'>📊 Dashboard Resumen Ejecutivo</h3>", unsafe_allow_html=True)

    df_razon_exec = df_f[df_f['Razón principal de bajo desempeño'].notna()].copy()
    df_razon_exec['Razón_Simp'] = df_razon_exec['Razón principal de bajo desempeño'].apply(simplificar_razones)

    fig = plt.figure(figsize=(16, 10))
    gs  = fig.add_gridspec(4, 3, hspace=0.45, wspace=0.35)
    fig.suptitle('DASHBOARD EJECUTIVO — ALERTAS TEMPRANAS UFPS', fontsize=16, fontweight='bold', y=0.98)

    # KPI 1
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.text(0.5, 0.65, str(len(df_f)), ha='center', va='center', fontsize=48, fontweight='bold', color='#C73E1D')
    ax1.text(0.5, 0.25, 'ALERTAS TOTALES', ha='center', va='center', fontsize=12, fontweight='bold')
    ax1.axis('off'); ax1.set_facecolor('#FFF5F5')

    # KPI 2
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.text(0.5, 0.65, str(df_f['Asignatura'].nunique()), ha='center', va='center', fontsize=48, fontweight='bold', color='#2E86AB')
    ax2.text(0.5, 0.25, 'ASIGNATURAS', ha='center', va='center', fontsize=12, fontweight='bold')
    ax2.axis('off'); ax2.set_facecolor('#F0F8FF')

    # KPI 3
    ax3 = fig.add_subplot(gs[0, 2])
    pm  = df_f.groupby(df_f['Fecha'].dt.to_period('M')).size().mean()
    ax3.text(0.5, 0.65, f'{pm:.1f}', ha='center', va='center', fontsize=48, fontweight='bold', color='#F18F01')
    ax3.text(0.5, 0.25, 'PROMEDIO MENSUAL', ha='center', va='center', fontsize=12, fontweight='bold')
    ax3.axis('off'); ax3.set_facecolor('#FFF9F0')

    # Top 8 asignaturas
    ax4    = fig.add_subplot(gs[1, :])
    top_8  = df_f['Asignatura'].value_counts().head(8)
    etiqs8 = [a[:35] + '...' if len(a) > 35 else a for a in top_8.index]
    ax4.barh(range(len(top_8)), top_8.values, color='#C73E1D', edgecolor='black')
    ax4.set_yticks(range(len(top_8))); ax4.set_yticklabels(etiqs8, fontsize=9)
    ax4.set_xlabel('Alertas', fontweight='bold')
    ax4.set_title('Top 8 Asignaturas con Más Alertas', fontweight='bold')
    ax4.grid(axis='x', alpha=0.3)
    for i, v in enumerate(top_8.values):
        ax4.text(v + 0.5, i, str(v), va='center', fontweight='bold', fontsize=9)

    # Razones principales
    ax5    = fig.add_subplot(gs[2:, :2])
    razones_exec = df_razon_exec['Razón_Simp'].value_counts().head(6)
    etiqs_r = [textwrap.fill(r, 25) for r in razones_exec.index]
    ax5.barh(range(len(razones_exec)), razones_exec.values, color='#8B0000', edgecolor='black')
    ax5.set_yticks(range(len(razones_exec))); ax5.set_yticklabels(etiqs_r, fontsize=9)
    ax5.set_xlabel('Frecuencia', fontweight='bold')
    ax5.set_title('Top 6 Razones de Bajo Desempeño', fontweight='bold')
    ax5.grid(axis='x', alpha=0.3)
    for i, v in enumerate(razones_exec.values):
        ax5.text(v + 0.3, i, str(v), va='center', fontweight='bold', fontsize=9)

    # Distribución por año
    ax6       = fig.add_subplot(gs[2:, 2])
    dist_año  = df_f['Año'].value_counts().sort_index()
    c_año     = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'][:len(dist_año)]
    ax6.bar(dist_año.index, dist_año.values, color=c_año, edgecolor='black', width=0.6)
    ax6.set_title('Por Año Académico', fontweight='bold')
    ax6.set_xlabel('Año', fontweight='bold'); ax6.set_ylabel('Alertas', fontweight='bold')
    ax6.grid(axis='y', alpha=0.3)
    for i, v in enumerate(dist_año.values):
        ax6.text(dist_año.index[i], v + 1, str(v), ha='center', fontweight='bold', fontsize=10)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# ============================================================================
# TAB 7 — ANÁLISIS MULTIDIMENSIONAL
# ============================================================================
with tab7:
    st.markdown("<h3 class='section-title'>🔍 Análisis Multidimensional de Razones</h3>", unsafe_allow_html=True)

    df_md = df_f[df_f['Razón principal de bajo desempeño'].notna()].copy()
    df_md['Razón_Simp'] = df_md['Razón principal de bajo desempeño'].apply(simplificar_razones)
    df_md = df_md[df_md['Razón_Simp'].notna()]

    if len(df_md) == 0:
        st.warning("No hay datos suficientes para el análisis multidimensional.")
    else:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('ANÁLISIS MULTIDIMENSIONAL DE RAZONES DE BAJO DESEMPEÑO',
                     fontsize=14, fontweight='bold')

        # 1. Razones por año
        tabla_año = pd.crosstab(df_md['Año'], df_md['Razón_Simp'])
        tabla_año.plot(kind='bar', stacked=True, ax=axes[0,0], edgecolor='black', linewidth=0.5)
        axes[0,0].set_title('Razones por Año', fontweight='bold')
        axes[0,0].set_xlabel('Año'); axes[0,0].set_ylabel('Frecuencia')
        axes[0,0].legend(title='Razón', bbox_to_anchor=(1.05,1), loc='upper left', fontsize=7)
        axes[0,0].tick_params(axis='x', rotation=0)

        # 2. Razones por semestre
        tabla_sem = pd.crosstab(df_md['Semestre'], df_md['Razón_Simp'])
        tabla_sem.plot(kind='bar', stacked=True, ax=axes[0,1], edgecolor='black', linewidth=0.5)
        axes[0,1].set_title('Razones por Semestre', fontweight='bold')
        axes[0,1].set_xlabel('Semestre'); axes[0,1].set_ylabel('Frecuencia')
        axes[0,1].set_xticklabels(['Semestre 1', 'Semestre 2'], rotation=0)
        axes[0,1].legend(title='Razón', bbox_to_anchor=(1.05,1), loc='upper left', fontsize=7)

        # 3. Top 5 asignaturas por razón
        top5 = df_md['Asignatura'].value_counts().head(5).index
        df_t5 = df_md[df_md['Asignatura'].isin(top5)]
        tabla_t5 = pd.crosstab(df_t5['Asignatura'], df_t5['Razón_Simp'])
        tabla_t5.index = [a[:25]+'...' if len(a) > 25 else a for a in tabla_t5.index]
        tabla_t5.plot(kind='barh', stacked=True, ax=axes[1,0], edgecolor='black', linewidth=0.5)
        axes[1,0].set_title('Top 5 Asignaturas: Razones', fontweight='bold')
        axes[1,0].set_xlabel('Frecuencia')
        axes[1,0].legend(title='Razón', bbox_to_anchor=(1.05,1), loc='upper left', fontsize=7)

        # 4. Donut chart
        razones_tot = df_md['Razón_Simp'].value_counts()
        colors_d    = plt.cm.Set3(np.linspace(0, 1, len(razones_tot)))
        axes[1,1].pie(razones_tot.values, labels=None, autopct='%1.1f%%',
                      colors=colors_d, startangle=90, pctdistance=0.85,
                      textprops={'fontsize': 8, 'fontweight': 'bold'})
        circle = plt.Circle((0,0), 0.70, fc='white')
        axes[1,1].add_artist(circle)
        axes[1,1].set_title('Distribución Global', fontweight='bold')
        axes[1,1].legend(razones_tot.index, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=7)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # Evolución temporal (heatmap)
        st.markdown("#### Evolución Temporal por Asignatura")
        df_periodo = df_f.copy()
        df_periodo['Período'] = df_periodo['Año'].astype(str) + '-S' + df_periodo['Semestre'].astype(str)
        top10_et   = df_f['Asignatura'].value_counts().head(10).index
        df_top10   = df_periodo[df_periodo['Asignatura'].isin(top10_et)]
        tabla_et   = pd.crosstab(df_top10['Asignatura'], df_top10['Período'])
        tabla_et.index = [a[:30]+'...' if len(a) > 30 else a for a in tabla_et.index]

        fig2, ax2 = plt.subplots(figsize=(12, 7))
        sns.heatmap(tabla_et, annot=True, fmt='d', cmap='Blues',
                    linewidths=0.5, linecolor='gray', cbar_kws={'label': 'Alertas'}, ax=ax2)
        ax2.set_title('EVOLUCIÓN TEMPORAL DE ALERTAS POR ASIGNATURA (Top 10)', fontweight='bold')
        ax2.set_xlabel('Período Académico', fontweight='bold')
        ax2.set_ylabel('Asignatura', fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0, fontsize=9)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

# ============================================================================
# TAB 8 — REPORTE COMPLETO
# ============================================================================
with tab8:
    st.markdown("<h3 class='section-title'>📋 Reporte Completo con Recomendaciones</h3>", unsafe_allow_html=True)

    df_cr = df_f[df_f['Razón principal de bajo desempeño'].notna()].copy()
    df_cr['Razón_Simp'] = df_cr['Razón principal de bajo desempeño'].apply(simplificar_razones)
    df_cr = df_cr[df_cr['Razón_Simp'].notna()]

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown("#### 1. Resumen General")
        st.markdown(f"""
        - **Total de alertas registradas:** {len(df_f):,}
        - **Período de análisis:** {df_f['Fecha'].min().date()} a {df_f['Fecha'].max().date()}
        - **Asignaturas únicas:** {df_f['Asignatura'].nunique()}
        - **Promedio de alertas por mes:** {df_f.groupby(df_f['Fecha'].dt.to_period('M')).size().mean():.1f}
        """)

        st.markdown("#### 2. Análisis Temporal")
        for año, count in df_f['Año'].value_counts().sort_index().items():
            pct = count / len(df_f) * 100
            st.markdown(f"- **{año}:** {count} alertas ({pct:.1f}%)")
        for sem, count in df_f['Semestre'].value_counts().sort_index().items():
            pct = count / len(df_f) * 100
            st.markdown(f"- **Semestre {sem}:** {count} alertas ({pct:.1f}%)")

    with col_r2:
        st.markdown("#### 3. Asignaturas con Mayor Riesgo")
        for i, (asig, count) in enumerate(df_f['Asignatura'].value_counts().head(10).items(), 1):
            pct = count / len(df_f) * 100
            st.markdown(f"{i}. **{asig[:50]}** — {count} alertas ({pct:.1f}%)")

    st.markdown("#### 4. Principales Razones de Bajo Desempeño")
    st.markdown(f"- Estudiantes que reportaron razón: **{len(df_cr)}**")
    st.markdown(f"- Sin razón especificada: **{len(df_f) - len(df_cr)}**")

    if len(df_cr) > 0:
        for i, (razon, count) in enumerate(df_cr['Razón_Simp'].value_counts().items(), 1):
            pct = count / len(df_cr) * 100
            st.markdown(f"{i}. **{razon}** — {count} estudiantes ({pct:.1f}%)")

        st.markdown("#### 5. Recomendaciones")
        razon_principal = df_cr['Razón_Simp'].value_counts().index[0]
        recomendaciones = [
            "Fortalecer el sistema de alertas tempranas",
            "Monitoreo continuo de asignaturas de alto riesgo",
            "Intervención temprana en estudiantes con múltiples alertas"
        ]
        if razon_principal == 'Falta de preparación':
            recomendaciones = ["Implementar talleres de hábitos de estudio",
                               "Crear grupos de estudio monitoreados",
                               "Establecer tutorías académicas preventivas"] + recomendaciones
        if 'Dificultad de comprensión' in df_cr['Razón_Simp'].value_counts().head(3).index:
            recomendaciones.insert(2, "Revisar metodologías de enseñanza en asignaturas críticas")
            recomendaciones.insert(3, "Implementar sesiones de refuerzo")
        if 'Problemas laborales' in df_cr['Razón_Simp'].value_counts().head(3).index:
            recomendaciones.append("Flexibilizar horarios para estudiantes trabajadores")
            recomendaciones.append("Crear modalidades de estudio adaptativas")

        for i, rec in enumerate(recomendaciones, 1):
            st.markdown(f"{i}. {rec}")

    st.markdown("---")
    st.caption(f"📅 Reporte generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | UFPS — Maestría TIC aplicadas a la Educación")
