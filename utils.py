# utils.py
import pandas as pd
import streamlit as st
import io 
from datetime import datetime

# Columnas requeridas para Production Efficiency
required_columns = [
     'Production Facility', 'W/C Type', 'W/C', 'Shift', 'Completed On', 'Timesheet #',
    'Job #', 'Employee', 'Item/OP #', 'Actual Labour Units', 'Expected Labour Units',
    'Machine Units', 'Expected Run Rate /hr', 'Actual Run Rate /hr', 'SPM', 'Quantity',
    'Held', 'Scrap', 'Hours', 'Efficiency', 'Performance', 'Quality', 'Availability',
    'OEE', 'Downtime', 'Available Hours'
]

numeric_cols = ['Hours', 'OEE', 'Efficiency', 'Quantity', 'Downtime', 'Scrap']

# Columnas requeridas para Scheduled Jobs
required_columns_plan = [
    'Production Facility', 'W/C Type', 'W/C', 'Job #', 'Item', 'Ship Date',
    'Lead Time (Days)', 'Produced', 'To Make', 'Remaining', 'Can Make', 'Run Rate',
    'Setup Hrs.', 'Run Hrs.', 'Total Hrs.', 'Primary Operators', 'Secondary Operators',
    'Due', 'Order Due', 'Job Created On', 'Status', 'Setup Status', 'Tooling Items',
    'Changeovers', 'Starts On', 'Ends On'
]

date_columns_plan = ['Ship Date', 'Due', 'Order Due', 'Job Created On', 'Starts On', 'Ends On']

# Función para cargar Production Efficiency
def cargar_reporte_produccion(file):
    df = pd.read_excel(file)
    if list(df.columns) != required_columns:
        return None, list(df.columns)
    df['Completed On'] = pd.to_datetime(df['Completed On'], errors='coerce')
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    return df, None

# Función para cargar Scheduled Jobs
def cargar_programacion(file):
    df = pd.read_excel(file)
    if list(df.columns) != required_columns_plan:
        return None, list(df.columns)
    for col in date_columns_plan:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df, None


# ====================================
# 🧮 CONVERSIÓN DE COLUMNAS
# ====================================

def convertir_columnas_fecha(df, columnas):
    """Convierte las columnas especificadas a formato datetime."""
    for col in columnas:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df


def convertir_columnas_numericas(df, columnas):
    """Convierte las columnas especificadas a formato numérico."""
    df[columnas] = df[columnas].apply(pd.to_numeric, errors='coerce')
    return df

# ====================================
# 🔍 FILTROS (sección para agregar)
# ====================================

def get_unique_values(df, column):
    """Devuelve valores únicos ordenados para un filtro dado."""
    return sorted(df[column].dropna().unique())

def filter_by_date_range(df, date_column, start_date, end_date):
    """Filtra un DataFrame por rango de fechas."""
    mask = (df[date_column] >= start_date) & (df[date_column] <= end_date)
    return df.loc[mask]

def filter_by_columns(df, filters):
    """Filtra un DataFrame según los valores de columnas dados en un diccionario."""
    for column, value in filters.items():
        if value is not None and value != 'Todos':
            df = df[df[column] == value]
    return df

# ====================================
# Exportar información a excel
# ====================================

def exportar_varias_hojas_excel(diccionario_dfs, nombre_base="Reporte_Produccion"):
    output = io.BytesIO()
    
     # Obtener fecha y hora actual
    fecha_hora_actual = datetime.now().strftime("%Y%m%d_%H%M")
    # Construir nombre de archivo con timestamp
    nombre_archivo = f"{nombre_base}_{fecha_hora_actual}.xlsx"

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for nombre_hoja, df in diccionario_dfs.items():
            df.to_excel(writer, sheet_name=nombre_hoja, index=False)

    output.seek(0)

    st.download_button(
        label="📥 Descargar Excel con reportes",
        data=output,
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )