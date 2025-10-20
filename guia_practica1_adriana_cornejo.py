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
    # El parámetro "search" se usa para palabra clave, acá ponemos la provincia
    # El "buyer" también puede usar la provincia, pero se puede omitir si queremos más datos.
    params = {
        "year": year,
        "search": region,
        "page": 1,
        # Si quieres filtrar por comprador, por ejemplo buyer=region,
        # params["buyer"] = region
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            # Convertimos la lista de dicts en DataFrame
            return pd.DataFrame(data["data"])
        else:
            return pd.DataFrame()
    else:
        return pd.DataFrame()  # Retorna vacío si falla

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
# Normalizar columnas, ajustamos a los nombres del JSON
df = df.rename(columns={
    'buyerName': 'region',
    'internal_type': 'internal_type',  # No siempre está, puede que no exista en esta API
    'single_provider': 'single_provider',
    'title': 'title',
    'date': 'date',
})

# Convertir tipos
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['month'] = df['date'].dt.month

# Nota: esta API no trae directamente 'total' ni 'contracts', se puede agregar más consulta si quieres detalles con ocid.

# ==============================
# 5. KPIs básicos
# ==============================
st.subheader("📌 Estadísticas Generales")
col1, col2 = st.columns(2)
col1.metric("Total registros", f"{len(df):,}")
col2.metric("Año seleccionado", anio)

# ==============================
# 6. Visualizaciones simples
# ==============================
st.subheader("📊 Visualizaciones")

# Conteo por tipo de proceso (internal_type puede no estar, usamos 'title' o 'single_provider' como ejemplo)
if 'single_provider' in df.columns:
    conteo_proveedor = df['single_provider'].value_counts().reset_index()
    conteo_proveedor.columns = ['Proveedor', 'Cantidad']
    fig1 = px.bar(conteo_proveedor.head(10), x='Proveedor', y='Cantidad', title="Top 10 Proveedores")
    st.plotly_chart(fig1, use_container_width=True)

if 'month' in df.columns:
    mensual = df.groupby('month').size().reset_index(name='cantidad')
    fig2 = px.line(mensual, x='month', y='cantidad', title="Contratos por mes")
    st.plotly_chart(fig2, use_container_width=True)

# ==============================
# 7. Exportar CSV
# ==============================
st.subheader("💾 Exportar Datos")
st.download_button(
    label="📥 Descargar CSV",
    data=df.to_csv(index=False).encode('utf-8'),
    file_name="compras_filtradas.csv",
    mime="text/csv"
)

# ==============================
# 8. Conclusiones
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