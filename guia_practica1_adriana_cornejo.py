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
def cargar_datos_api(year, region):
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

df = cargar_datos_api(anio, region)

# ==============================
# 3. Verificar y mostrar datos
# ==============================
if df.empty:
    st.error("❌ No se encontraron datos. Verifica los filtros.")
    st.stop()

st.success(f"✅ Datos cargados: {df.shape[0]} registros.")
st.dataframe(df.head())

# ==============================
# 4. Limpieza de datos y filtros
# ==============================
# Normalizar columnas
df = df.rename(columns={
    'buyerName': 'region',
    'internal_type': 'internal_type',
    'single_provider': 'single_provider',
    'title': 'title',
    'date': 'date',
    'amount': 'amount'
})

# Convertir a datetime y filtrar años >= 2024
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df[df['date'].notna()]
    df = df[df['date'].dt.year >= 2024]
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year

# Convertir monto a numérico
if 'amount' in df.columns:
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

# Filtrar por tipo de contratación seleccionado
if 'internal_type' in df.columns:
    df = df[df['internal_type'] == tipo]

# ==============================
# 5. KPIs y Análisis Descriptivo
# ==============================
st.subheader("📌 Estadísticas Generales y Descriptivas")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total registros", f"{len(df):,}")

if 'amount' in df.columns and not df['amount'].empty:
    total_monto = df['amount'].sum(skipna=True)
    promedio_monto = df['amount'].mean(skipna=True)
    max_monto = df['amount'].max(skipna=True)
    min_monto = df['amount'].min(skipna=True)
else:
    total_monto = promedio_monto = max_monto = min_monto = 0

col2.metric("Monto total", f"${total_monto:,.2f}")
col3.metric("Promedio por registro", f"${promedio_monto:,.2f}")
col4.metric("Máximo / Mínimo", f"${max_monto:,.2f} / ${min_monto:,.2f}")

st.subheader("📊 Estadísticas Descriptivas")
if 'amount' in df.columns and not df['amount'].empty:
    st.write(df['amount'].describe())

# Conteos por proveedor
if 'single_provider' in df.columns:
    st.subheader("📌 Conteo por Proveedor")
    conteo_proveedor = df['single_provider'].value_counts().reset_index()
    conteo_proveedor.columns = ['Proveedor', 'Cantidad']
    st.dataframe(conteo_proveedor.head(10))

# ==============================
# 6. Visualizaciones simples
# ==============================
st.subheader("📊 Visualizaciones")

# Top proveedores
if 'single_provider' in df.columns:
    fig1 = px.bar(conteo_proveedor.head(10), x='Proveedor', y='Cantidad', title="Top 10 Proveedores")
    st.plotly_chart(fig1, use_container_width=True)

# Contratos por mes
if 'date' in df.columns:
    mensual = df.resample('M', on='date').size().reset_index(name='Cantidad')
    fig2 = px.line(mensual, x='date', y='Cantidad', title="Contratos por Mes")
    st.plotly_chart(fig2, use_container_width=True)

# Barras apiladas tipo x mes
if 'internal_type' in df.columns and 'date' in df.columns:
    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
    stacked = df.groupby(['month', 'internal_type']).size().reset_index(name='Cantidad')
    fig3 = px.bar(stacked, x='month', y='Cantidad', color='internal_type', barmode='stack',
                  title="Contratos por Mes y Tipo de Proceso")
    st.plotly_chart(fig3, use_container_width=True)

# Pastel por tipo
if 'internal_type' in df.columns:
    pie_data = df['internal_type'].value_counts().reset_index()
    pie_data.columns = ['Tipo', 'Cantidad']
    fig4 = px.pie(pie_data, names='Tipo', values='Cantidad', title="Proporción de Contratos por Tipo")
    st.plotly_chart(fig4, use_container_width=True)

# ==============================
# 7. Comparativa de Tipos de Contratación por Mes
# ==============================
st.subheader("📊 Comparativa de Tipos de Contratación por Mes")

if 'internal_type' in df.columns and 'date' in df.columns:
    mensual_tipo = df.groupby(['month', 'internal_type']).size().reset_index(name='Cantidad')
    fig5 = px.line(mensual_tipo, x='month', y='Cantidad', color='internal_type', markers=True,
                   title="Evolución Mensual por Tipo de Contratación")
    fig5.update_layout(xaxis_title="Mes", yaxis_title="Cantidad de Contratos")
    st.plotly_chart(fig5, use_container_width=True)

# ==============================
# 8. Exportar CSV
# ==============================
st.subheader("💾 Exportar Datos")
st.download_button(
    label="📥 Descargar CSV",
    data=df.to_csv(index=False).encode('utf-8'),
    file_name="compras_filtradas.csv",
    mime="text/csv"
)

# ==============================
# 9. Conclusiones
# ==============================
st.markdown(f"""
---
### ✅ Conclusiones
- Provincia seleccionada: **{region}**
- Año seleccionado: **{anio}**
- Tipo de contratación: **{tipo}**
- Total registros encontrados: **{len(df)}**
- Se muestran contratos relacionados con la provincia, tipo seleccionado y años >= 2024.
""")
st.markdown("Desarrollado por Adriana Cornejo - Curso de Análisis de Datos con Python")
