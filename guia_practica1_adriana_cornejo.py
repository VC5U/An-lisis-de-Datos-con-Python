# guia_practica1_TuNombre_TuApellido.py 
import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Análisis Compras Públicas", layout="wide")

st.title("📊 Guía Práctica 1 – Análisis de Compras Públicas en Ecuador")
st.markdown("Aplicación desarrollada para visualizar datos del portal oficial usando filtros dinámicos.")

# ==============================
# 1. Filtros (año, provincia, tipo)
# ==============================
st.sidebar.header("📌 Filtros")
anio = st.sidebar.slider("Año", min_value=2019, max_value=2025, value=2024)
region = st.sidebar.text_input("Provincia (ej: Azuay)", "Azuay")
tipo = st.sidebar.selectbox("Tipo de Contratación", ["Bienes", "Servicios", "Obras"])

# ==============================
# 2. Cargar desde API con search_ocds
# ==============================
@st.cache_data
def cargar_datos_api(year, region, tipo):
    url = "https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/api/search_ocds"
    params = {
        "year": year,
        "search": region,
        "page": 1,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            return pd.DataFrame(data["data"])
        else:
            return pd.DataFrame()
    else:
        return pd.DataFrame()

df = cargar_datos_api(anio, region, tipo)

# ==============================
# 3. Verificar y mostrar datos
# ==============================
if df.empty:
    st.error("❌ No se encontraron datos. Verifica los filtros.")
    st.stop()

st.success(f"✅ Datos cargados: {df.shape[0]} registros.")
st.dataframe(df.head())

# ==============================
# 4. Limpieza de datos
# ==============================
df = df.rename(columns={
    'buyerName': 'region',
    'internal_type': 'internal_type',
    'single_provider': 'single_provider',
    'title': 'title',
    'date': 'date',
    'amount': 'amount',
    'contracts': 'contracts',
    'total': 'total'
})

# Convertir tipos
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df[df['date'].notna()]  # eliminar fechas inválidas

if 'amount' in df.columns:
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

# ==============================
# 5. KPIs y Análisis Descriptivo
# ==============================
st.subheader("📌 Estadísticas Generales y Descriptivas")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total registros", f"{len(df):,}")

if 'amount' in df.columns:
    total_monto = df['amount'].sum(skipna=True)
    promedio_monto = df['amount'].mean(skipna=True)
    max_monto = df['amount'].max(skipna=True)
    min_monto = df['amount'].min(skipna=True)
else:
    total_monto = promedio_monto = max_monto = min_monto = 0

col2.metric("Monto total", f"${total_monto:,.2f}")
col3.metric("Promedio por registro", f"${promedio_monto:,.2f}")
col4.metric("Máximo / Mínimo", f"${max_monto:,.2f} / ${min_monto:,.2f}")

if 'amount' in df.columns:
    st.subheader("📊 Estadísticas Descriptivas")
    st.write(df['amount'].describe())

# Conteos por categorías relevantes
if 'single_provider' in df.columns:
    st.subheader("📌 Conteo por Proveedor")
    conteo_proveedor = df['single_provider'].value_counts().reset_index()
    conteo_proveedor.columns = ['Proveedor', 'Cantidad']
    st.dataframe(conteo_proveedor.head(10))

# ==============================
# 6. Visualizaciones simples
# ==============================
st.subheader("📊 Visualizaciones")

# Top 10 proveedores
if 'single_provider' in df.columns:
    conteo_proveedor = df['single_provider'].value_counts().reset_index()
    conteo_proveedor.columns = ['Proveedor', 'Cantidad']
    fig1 = px.bar(conteo_proveedor.head(10), x='Proveedor', y='Cantidad', title="Top 10 Proveedores")
    st.plotly_chart(fig1, use_container_width=True)

# Contratos por mes
if 'date' in df.columns:
    df['month_year'] = df['date'].dt.to_period('M').dt.to_timestamp()
    mensual = df.groupby('month_year').size().reset_index(name='Cantidad')
    fig2 = px.line(mensual, x='month_year', y='Cantidad', title="Contratos por Mes")
    fig2.update_layout(xaxis_title="Mes", yaxis_title="Cantidad de Contratos")
    st.plotly_chart(fig2, use_container_width=True)

# Barras apiladas tipo de contratación
if 'internal_type' in df.columns:
    stacked = df.groupby(['month_year', 'internal_type']).size().reset_index(name='Cantidad')
    fig3 = px.bar(stacked, x='month_year', y='Cantidad', color='internal_type', barmode='stack',
                  title="Contratos por Mes y Tipo de Proceso")
    st.plotly_chart(fig3, use_container_width=True)

# Pastel por tipo de contrato
if 'internal_type' in df.columns:
    pie_data = df['internal_type'].value_counts().reset_index()
    pie_data.columns = ['Tipo', 'Cantidad']
    fig4 = px.pie(pie_data, names='Tipo', values='Cantidad', title="Proporción de Contratos por Tipo")
    st.plotly_chart(fig4, use_container_width=True)

# ==============================
# 7. Relación Monto Total vs Cantidad de Contratos
# ==============================
st.subheader("📈 Relación Monto Total vs Cantidad de Contratos")
if 'contracts' in df.columns and 'total' in df.columns and 'internal_type' in df.columns:
    df['total'] = pd.to_numeric(df['total'], errors='coerce')
    fig5 = px.scatter(
        df,
        x="contracts",
        y="total",
        color="internal_type",
        size="total",
        hover_data=["title", "region"],
        title="Dispersión: Monto Total vs Cantidad de Contratos"
    )
    st.plotly_chart(fig5, use_container_width=True)
    st.markdown("""
    **Interpretación:**
    - Correlación positiva: puntos suben de izquierda a derecha.
    - Correlación negativa: puntos bajan de izquierda a derecha.
    - Correlación débil: puntos dispersos.
    """)
else:
    st.info("❗ No hay datos suficientes para mostrar la relación entre Monto Total y Cantidad de Contratos.")

# ==============================
# 8. Comparativa de Tipos de Contratación por Mes
# ==============================
st.subheader("📊 Comparativa de Tipos de Contratación por Mes")
if 'internal_type' in df.columns:
    mensual_tipo = df.groupby(['month_year', 'internal_type']).size().reset_index(name='Cantidad')
    fig6 = px.line(
        mensual_tipo,
        x='month_year',
        y='Cantidad',
        color='internal_type',
        markers=True,
        title="Evolución Mensual por Tipo de Contratación"
    )
    fig6.update_layout(xaxis_title="Mes", yaxis_title="Cantidad de Contratos")
    st.plotly_chart(fig6, use_container_width=True)
    st.markdown("""
    **Interpretación:**  
    - Permite ver cuál tipo de contratación tiene mayor actividad en cada mes.  
    - Identifica picos y tendencias estacionales.
    """)
else:
    st.info("❗ No hay datos suficientes para la comparativa mensual por tipo de contratación.")

# ==============================
# 9. Análisis por Años
# ==============================
st.subheader("📈 Análisis Comparativo por Año")
if 'date' in df.columns and 'internal_type' in df.columns:
    df['year'] = df['date'].dt.year
    kpi_year = df.groupby('year').agg(
        total_registros=('title', 'count'),
        total_monto=('total', lambda x: pd.to_numeric(x, errors='coerce').sum())
    ).reset_index()
    st.dataframe(kpi_year)

    stacked_year = df.groupby(['year', 'internal_type']).size().reset_index(name='Cantidad')
    fig7 = px.bar(stacked_year, x='year', y='Cantidad', color='internal_type', barmode='stack',
                  title="Contratos por Tipo y Año")
    st.plotly_chart(fig7, use_container_width=True)

    monthly_year = df.groupby(['month_year', 'year']).size().reset_index(name='Cantidad')
    fig8 = px.line(monthly_year, x='month_year', y='Cantidad', color='year', markers=True,
                   title="Evolución Mensual Comparada por Año")
    st.plotly_chart(fig8, use_container_width=True)

    heatmap_data = df.groupby(['year', 'month_year']).size().reset_index(name='Cantidad')
    heatmap_pivot = heatmap_data.pivot(index='year', columns='month_year', values='Cantidad').fillna(0)
    fig9 = px.imshow(heatmap_pivot, labels=dict(x="Mes", y="Año", color="Cantidad"),
                     title="Mapa de Calor: Contratos por Año y Mes")
    st.plotly_chart(fig9, use_container_width=True)

    st.markdown("""
    **Interpretación general:**  
    - Permite identificar cambios de actividad entre años.  
    - Los gráficos muestran picos, variabilidad y tendencias de contratación por tipo y mes.
    """)
else:
    st.info("❗ No hay datos suficientes para realizar análisis por años.")

# ==============================
# 10. Exportar CSV
# ==============================
st.subheader("💾 Exportar Datos")
st.download_button(
    label="📥 Descargar CSV",
    data=df.to_csv(index=False).encode('utf-8'),
    file_name="compras_filtradas.csv",
    mime="text/csv"
)

# ==============================
# 11. Conclusiones
# ==============================
st.markdown(f"""
---
### ✅ Conclusiones
- Provincia seleccionada: **{region}**
- Año seleccionado: **{anio}**
- Total registros encontrados: **{len(df)}**
- Se muestran contratos relacionados con la provincia y año seleccionados.
""")
st.markdown("Desarrollado por Adriana Cornejo - Curso de Análisis de Datos con Python")
