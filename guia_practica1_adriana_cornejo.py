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
# 5. KPIs y Análisis Descriptivo
# ==============================
st.subheader("📌 Estadísticas Generales y Descriptivas")

# Columnas para KPIs rápidos
col1, col2, col3, col4 = st.columns(4)

# Total de registros
col1.metric("Total registros", f"{len(df):,}")

# Si la columna de monto existe, calculamos total y promedio
if 'amount' in df.columns:
    total_monto = df['amount'].sum()
    promedio_monto = df['amount'].mean()
    max_monto = df['amount'].max()
    min_monto = df['amount'].min()
else:
    total_monto = promedio_monto = max_monto = min_monto = 0

col2.metric("Monto total", f"${total_monto:,.2f}")
col3.metric("Promedio por registro", f"${promedio_monto:,.2f}")
col4.metric("Máximo / Mínimo", f"${max_monto:,.2f} / ${min_monto:,.2f}")

# Estadísticas descriptivas completas
st.subheader("📊 Estadísticas Descriptivas")
if 'amount' in df.columns:
    st.write(df['amount'].describe())  # media, mediana, std, min, max, cuartiles

# Conteos por categorías relevantes (ejemplo: tipo de contratación)
if 'single_provider' in df.columns:
    st.subheader("📌 Conteo por Proveedor")
    conteo_proveedor = df['single_provider'].value_counts().reset_index()
    conteo_proveedor.columns = ['Proveedor', 'Cantidad']
    st.dataframe(conteo_proveedor.head(10))

# ==============================
# 6. Visualizaciones simples
# ==============================
st.subheader("📊 Visualizaciones")

# a) Barras por tipo de proveedor o proceso
if 'single_provider' in df.columns:
    conteo_proveedor = df['single_provider'].value_counts().reset_index()
    conteo_proveedor.columns = ['Proveedor', 'Cantidad']
    fig1 = px.bar(conteo_proveedor.head(10), x='Proveedor', y='Cantidad', title="Top 10 Proveedores")
    st.plotly_chart(fig1, use_container_width=True)

# b) Línea mensual de contratos
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    mensual = df.resample('M', on='date').size().reset_index(name='Cantidad')
    fig2 = px.line(mensual, x='date', y='Cantidad', title="Contratos por Mes")
    st.plotly_chart(fig2, use_container_width=True)

# c) Barras apiladas: tipo de contratación por mes
if 'date' in df.columns and 'internal_type' in df.columns:
    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
    stacked = df.groupby(['month', 'internal_type']).size().reset_index(name='Cantidad')
    fig3 = px.bar(stacked, x='month', y='Cantidad', color='internal_type', barmode='stack',
                  title="Contratos por Mes y Tipo de Proceso")
    st.plotly_chart(fig3, use_container_width=True)

# d) Pastel: proporción de contratos por tipo
if 'internal_type' in df.columns:
    pie_data = df['internal_type'].value_counts().reset_index()
    pie_data.columns = ['Tipo', 'Cantidad']
    fig4 = px.pie(pie_data, names='Tipo', values='Cantidad', title="Proporción de Contratos por Tipo")
    st.plotly_chart(fig4, use_container_width=True)
# ==============================
# 6. Relación Monto Total vs Cantidad de Contratos
# ==============================
st.subheader("📈 Relación Monto Total vs Cantidad de Contratos")

# Verificamos que existan las columnas necesarias
if 'contracts' in df.columns and 'total' in df.columns and 'internal_type' in df.columns:
    fig5 = px.scatter(
        df,
        x="contracts",
        y="total",
        color="internal_type",
        size="total",  # opcional: tamaño según el monto
        hover_data=["title", "region"],
        title="Dispersión: Monto Total vs Cantidad de Contratos"
    )
    st.plotly_chart(fig5, use_container_width=True)
    
    # Interpretación básica
    st.markdown("""
    **Interpretación:**
    - Si los puntos tienden a subir de izquierda a derecha → correlación positiva.
    - Si los puntos bajan de izquierda a derecha → correlación negativa.
    - Si los puntos están dispersos → correlación débil.
    """)
else:
    st.info("❗ No hay datos suficientes para mostrar la relación entre Monto Total y Cantidad de Contratos.")

# ==============================
# 7. Comparativa de Tipos de Contratación por Mes
# ==============================
st.subheader("📊 Comparativa de Tipos de Contratación por Mes")

if 'date' in df.columns and 'internal_type' in df.columns:
    df['month'] = df['date'].dt.month
    mensual_tipo = df.groupby(['month', 'internal_type']).size().reset_index(name='Cantidad')
    
    fig6 = px.line(
        mensual_tipo,
        x='month',
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
# 8. Análisis por Años
# ==============================
st.subheader("📈 Análisis Comparativo por Año")

if 'date' in df.columns and 'internal_type' in df.columns:
    df['year'] = df['date'].dt.year
    
    # a) KPIs por año
    kpi_year = df.groupby('year').agg(
        total_registros=('title', 'count'),
        total_monto=('total', 'sum')
    ).reset_index()
    st.dataframe(kpi_year)
    
    # b) Barras apiladas tipo × año
    stacked_year = df.groupby(['year', 'internal_type']).size().reset_index(name='Cantidad')
    fig7 = px.bar(
        stacked_year,
        x='year',
        y='Cantidad',
        color='internal_type',
        barmode='stack',
        title="Contratos por Tipo y Año"
    )
    st.plotly_chart(fig7, use_container_width=True)
    
    # c) Evolución mensual comparada por año
    df['month_year'] = df['date'].dt.to_period('M').dt.to_timestamp()
    monthly_year = df.groupby(['month_year', 'year']).size().reset_index(name='Cantidad')
    fig8 = px.line(
        monthly_year,
        x='month_year',
        y='Cantidad',
        color='year',
        markers=True,
        title="Evolución Mensual Comparada por Año"
    )
    st.plotly_chart(fig8, use_container_width=True)
    
    # d) Heatmap año × mes
    heatmap_data = df.groupby(['year', 'month']).size().reset_index(name='Cantidad')
    heatmap_pivot = heatmap_data.pivot(index='year', columns='month', values='Cantidad').fillna(0)
    fig9 = px.imshow(
        heatmap_pivot,
        labels=dict(x="Mes", y="Año", color="Cantidad"),
        title="Mapa de Calor: Contratos por Año y Mes"
    )
    st.plotly_chart(fig9, use_container_width=True)
    
    st.markdown("""
    **Interpretación general:**  
    - Permite identificar cambios de actividad entre años.  
    - Los gráficos muestran picos, variabilidad y tendencias de contratación por tipo y mes.  
    - El heatmap facilita la visualización de meses con alta o baja actividad.
    """)
else:
    st.info("❗ No hay datos suficientes para realizar análisis por años.")

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