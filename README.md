# 📊 Dashboard Alertas Tempranas — UFPS

Dashboard interactivo de análisis de deserción y permanencia estudiantil para la Universidad Francisco de Paula Santander (UFPS), Cúcuta.

**Proyecto de Maestría en TIC aplicadas a la Educación**  
Versión: 2.0 (Streamlit) | Febrero 2026

---

## 🚀 Despliegue en Streamlit Cloud (paso a paso)

### 1. Subir a GitHub
1. Crea un repositorio nuevo en [github.com](https://github.com) (puede ser privado)
2. Sube los archivos: `app.py`, `requirements.txt` y este `README.md`

### 2. Desplegar en Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io) e inicia sesión con tu cuenta de GitHub
2. Clic en **"New app"**
3. Selecciona tu repositorio y la rama `main`
4. En **"Main file path"** escribe: `app.py`
5. Clic en **"Deploy!"**
6. En ~2 minutos tendrás tu URL pública 🎉

---

## 📁 Estructura del proyecto

```
dashboard-alertas-ufps/
├── app.py              ← Aplicación principal Streamlit
├── requirements.txt    ← Dependencias Python
└── README.md           ← Este archivo
```

---

## 📊 Contenido del Dashboard

| Sección | Descripción |
|---|---|
| 📌 KPIs | Total alertas, asignaturas, promedio mensual |
| 📈 Tendencia Temporal | Alertas por año, semestre y mes |
| 📚 Top Asignaturas | Ranking configurable de asignaturas con más alertas |
| ❓ Razones Desempeño | Categorización y distribución de razones |
| 🔥 Mapa de Calor | Cruce asignaturas vs razones |
| ☁️ Nube de Palabras | Visualización cualitativa de razones |
| 📊 Dashboard Ejecutivo | Vista consolidada con KPIs y gráficos |
| 🔍 Análisis Multidim. | Razones por año, semestre, asignatura |
| 📋 Reporte Completo | Reporte con recomendaciones automáticas |

---

## 🔍 Uso

1. Abre la URL pública del dashboard
2. Carga el archivo Excel desde el panel lateral izquierdo
3. Usa los filtros de **Año** y **Semestre** para explorar los datos
4. Navega entre las pestañas para ver cada análisis

El archivo Excel debe contener las columnas:
- `Fecha` (formato fecha)
- `Asignatura`
- `Razón principal de bajo desempeño`
- `Razón personal de bajo desempeño`
