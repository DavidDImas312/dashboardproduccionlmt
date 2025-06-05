# utils.py
import pandas as pd
import streamlit as st
import io 
from datetime import datetime

# Columnas requeridas para Production Efficiency
required_columns = [
     'W/C Type', 'W/C', 'Shift', 'Completed On', 'Timesheet #',
    'Job #', 'Employee', 'Item/OP #', 'Std Cost', 'Expected Run Rate /hr', 'Actual Run Rate /hr', 'Quantity',
    'Held', 'Scrap', 'Scrap Cost', 'Hours', 'Efficiency', 'OEE', 'Production Downtime Hours', 'Non-production Downtime Hours',
    'Production Downtime Reasons', 'Downtime Notes'
]

numeric_cols = ['Hours', 'OEE', 'Efficiency', 'Quantity', 'Production Downtime Hours', 'Scrap', 'Non-production Downtime Hours']

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

# ====================================
# Razones de DownTime
# ====================================

catalogo_downtime = pd.DataFrame({
    "Reason ID": [
        "D001", "D002", "D003", "D004", "D005", "D006", "D007", "D008", "D009", "D010",
        "D011", "D012", "D013", "D014", "D015", "D016", "D017", "D018", "D019", "D020",
        "D021", "D022", "D023", "D024", "D025", "D026", "D027", "D028", "D029", "D030",
        "D031", "D032", "D033", "D034", "D035", "D036", "D037", "D038", "D039", "D040",
        "D041", "D042", "D043", "D044", "D045", "D046", "D047", "D048", "D049", "D050",
        "D051", "D052", "D053", "D054", "D055", "D056", "D057", "D058", "D059", "D060",
        "D061", "D062", "D063", "D064", "D065", "D066", "D067", "D068", "D069", "D070",
        "D071", "D072", "D073"
    ],
    "Description": [
        "cambio de rollo", "cambio de contenedor", "AJUSTES DE TROQUEL / ALINEACION / CAMBIO FECHA JULIANA",
        "TROQUEL DAÑADO POR MAL GOLPE / AJUSTE", "FALLA EN SENSOR DE TROQUEL", "REVISION DE PIEZA / INSPECCIÓN",
        "AJUSTE POR REBABA", "AJUSTE DE PLANICIDAD", "AJUSTE DE PERFIL", "AJUSTE POR FISURA",
        "AJUSTE POR DEFORMACION", "AJUSTE POR LOCALIZACION", "AJUSTE POR MARCA EN PIEZA", "AJUSTE POR FALTA DE FORMA",
        "AJUSTE POR TORNILLO CAPADO", "CILINDROS O RESORTES DAÑADOS", "NO LOCALIZA EN DISPOSITIVO DE CONTROL",
        "TROQUEL DAÑADO POR MALA REPARACION", "FALLA EN PORTAROLLO / DESENRROLLADOR", "FALLA EN ENDEREZADOR",
        "FALLA  EN EL ALIMENTADOR", "FALLA EN PRENSA", "FALLA EN SISTEMA DE AIRE", "FALLA  NEUMATICA",
        "FALLA HIDRAULICA", "FALLA EN CORTINAS DE SEGURIDAD", "FALLA EN SISTEMA DE LUBRICACIÓN", "FALLA ELECTRICA",
        "FALLA DE MONTACARGAS", "FALTA DE MATERIA PRIMA (No se ha traído o falta documentación para liberar)",
        "FALTA DE CONTENEDORES/TROQUEL/TOLVAS (Montacargas)", "Falta de Orden de trabajo o etiquetas",
        "Error en programa (se modifica programa o no hay acero de orden programada)",
        "Falta de Empaque / Empaque mal rasurado", "PARO POR RETIRO DE TOLVAS DE SCRAP", "LIBERACIÓN DE PIEZA",
        "PARO POR FALTA DE LIBERACION DE ACERO", "CAMBIO DE CAPS / ELECTRODOS", "LIMPIEZA DE CAPS",
        "EXCEDENTE DE LIBERACIÓN", "EXCEDENTE TPM (5 min)", "EXCEDENTE RELLENO DE ANTI ESPATER",
        "EXCEDENTE CAMBIO DE GAS", "EXCEDENTE CAMBIO DE MICROALAMBRE", "EXCEDENTE CAMBIO DE PUNTA DE CONTACTO",
        "EXCEDENTE CAMBIO DE TOBERA", "AJUSTES DIMENSIONALES", "AJUSTE DE PUNTO", "AJUSTE DE CORDÓN",
        "AJUSTE DE CÁMARAS", "AJUSTE DE SENSOR", "AJUSTE DE ERROR PROOFING", "FALLA DE PEDESTAL",
        "FALLA EN SISTEMA DE AIRE", "FALLA NEUMÁTICA", "FALLA HIDRÁULICA", "FALLA EN SEGURIDADES DE CELDA",
        "FALLA DE ROBOT", "FALLA DE PLANTA DE SOLDAR", "FALLA ELÉCTRICA", "FALLA DE COMUNICACIÓN",
        "FALLA DE MONTACARGAS", "CORTE EN EL SUMINISTRO DE ENERGÍA EN PLANTA", "FALTA DE ETIQUETAS DE COMPONENTES EXTERNOS",
        "FALTA DE CONTENEDORES", "FALTA DE ORDEN DE TRABAJO O ETIQUETAS", "ERROR EN PROGRAMA", "FALTA DE MATERIA PRIMA",
        "EMPAQUE MAL RASURADO", "LIBERACIÓN DE PIEZA", "MATERIAL CON DEFECTO DE PROVEEDOR",
        "PARO POR FALTA DE LIBERACIÓN DE COMPONENTES", "EXCEDENTE DE TIEMPO POR CUT&ETCH"
    ]
})