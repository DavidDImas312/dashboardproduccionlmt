# utils.py
import pandas as pd
import streamlit as st
import io
import plotly.express as px
from datetime import datetime
from io import BytesIO

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


columnas_orders = [
    "Week Of", "Ship From", "Customer", "Ship To", "Item", "On Hand",
    "Customer PO", "Order #", "Customer Item", "Wanted On", "Ship On",
    "Quantity", "Unit Price", "U/M", "Amount", "Firm/Planned"
]

columnas_sales = [
    "Week Of", "Invoice Date", "Posting Date", "Ship From", "Market Type",
    "Customer", "Ship To", "Item", "Customer PO", "Customer Item", "Quantity",
    "Unit Price", "Std Cost", "Total Cost", "U/M", "Amount", "Margin",
    "G/L Account", "Currency", "Invoice #", "P/S #", "Order#"
]

# Función para cargar Production Efficiency
@st.cache_data
def cargar_reporte_produccion(file):
    df = pd.read_excel(file)
    if list(df.columns) != required_columns:
        return None, list(df.columns)
    df['Completed On'] = pd.to_datetime(df['Completed On'], errors='coerce')
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    return df, None

# Función para cargar Scheduled Jobs
@st.cache_data
def cargar_programacion(file):
    df = pd.read_excel(file)
    if list(df.columns) != required_columns_plan:
        return None, list(df.columns)
    for col in date_columns_plan:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df, None

# 🧮 CONVERSIÓN DE COLUMNAS
def convertir_columnas_fecha(df, columnas):
    """Convierte las columnas especificadas a formato datetime."""
    for col in columnas:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df


def convertir_columnas_numericas(df, columnas):
    """Convierte las columnas especificadas a formato numérico."""
    df[columnas] = df[columnas].apply(pd.to_numeric, errors='coerce')
    return df

# 🔍 FILTROS (sección para agregar)
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


# Razones de DownTime
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

# Extraer DownTime
@st.cache_data
def cargar_downtime(file):
    try:
        df_raw = pd.read_excel(
            file,
            header=0,               
            usecols="A:B",
            skiprows=1,          
            skipfooter=1,        
            engine="openpyxl"    
        )
        df_raw.columns = ["WorkCenter", "TotalHours"]
        return df_raw
    except Exception as e:
        print(f"Error al cargar downtime: {e}")
        return None

def extraer_downtime(df):
    data = []
    current_reason = None

    for index, row in df.iterrows():
        texto = str(row["WorkCenter"]).strip()

        # Detectar encabezado de grupo tipo D005 - D005
        if texto.startswith("D") and " - " in texto:
            current_reason = texto.split(" - ")[0]

        # Ignorar Totales y líneas vacías o genéricas
        elif texto.startswith("Total") or texto == "" or texto.upper() == "PRESS - PRESS" or texto.upper() == "WELDING N2 - WELD N2" or texto.upper() == "PROD N4 - PROD N4" or texto.upper() == "Down Time by WC":
            continue

        # Si hay razón activa y es una línea válida
        elif current_reason:
            data.append({
                "W/C": texto.split(" - ")[0],  # antes del primer guión por si hay
                "Horas Downtime": row["TotalHours"],
                "Razones": current_reason
            })

    return pd.DataFrame(data)

# Filtros DownTime
def filtrar_downtime(df_downtime, fechas=None, turnos=None, wc_types=None, wcs=None):
    df_filtrado = df_downtime.copy()

    if fechas is not None:
        if "Completed On" in df_filtrado.columns:
            df_filtrado = df_filtrado[
                (df_filtrado["Completed On"] >= pd.to_datetime(fechas[0])) &
                (df_filtrado["Completed On"] <= pd.to_datetime(fechas[1]))
            ]

    if turnos is not None:
        if "Shift" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["Shift"].isin(turnos)]

    if wc_types is not None:
        if "W/C Type" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["W/C Type"].isin(wc_types)]

    if wcs is not None:
        if "W/C" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["W/C"].isin(wcs)]

    return df_filtrado

# Función para cargar cualquier archivo y extraer solo las columnas requeridas
@st.cache_data
def cargar_datos_columnas_requeridas(file, columnas_requeridas, skiprows=0):
    """Carga un archivo Excel, limpia encabezados y devuelve columnas requeridas."""
    try:
        df = pd.read_excel(file, skiprows=skiprows)

        # Limpiar nombres de columnas
        df.columns = (
            df.columns.str.replace(r"\s+", " ", regex=True)
                      .str.strip()
        )

        # Verificar columnas disponibles
        columnas_disponibles = df.columns.tolist()
        columnas_faltantes = [col for col in columnas_requeridas if col not in columnas_disponibles]

        if columnas_faltantes:
            return None, f"Faltan las siguientes columnas: {columnas_faltantes}"

        # Filtrar solo las columnas requeridas
        df_filtrado = df[columnas_requeridas]

        # Limpiar espacios extra en los valores string
        for col in df_filtrado.columns:
            if df_filtrado[col].dtype == 'object':
                df_filtrado[col] = df_filtrado[col].astype(str).str.strip()
                df_filtrado[col] = df_filtrado[col].replace(
                    to_replace=['-', 'N/A', 'nan', 'None', 'NaT'], value=pd.NA
                )

        # Eliminar filas completamente vacías en las columnas requeridas
        df_filtrado = df_filtrado.dropna(how='all', subset=columnas_requeridas)

        return df_filtrado, None

    except Exception as e:
        return None, f"Error al cargar el archivo: {str(e)}"

def leer_mrp_excel(ruta_archivo, hoja=0):
    df_raw = pd.read_excel(ruta_archivo, sheet_name=hoja)

    df_po_rows = []
    df_sin_req_rows = []

    current_item = None
    current_type = None

    for _, row in df_raw.iterrows():
        item = row.iloc[0]
        referencia = str(row.iloc[1])
        type_col = row.iloc[4]
        on_hand = row.iloc[6]
        demand_total = row.iloc[11]
        vendor = row.iloc[3]

        # Si es encabezado de Item
        if pd.notna(item):
            current_item = item
            current_type = type_col

            # Si en columna J no hay valor o es 0 —> sin requerimiento
            if pd.isna(row.iloc[9]) or row.iloc[9] == 0:
                df_sin_req_rows.append({
                    'Item': current_item,
                    'Type': current_type,
                    'Vendor': vendor,
                    'On Hand': on_hand,
                    'Demand Total': demand_total
                })

        # Si es Purchase Order
        if "Purchase Order" in referencia:
            df_po_rows.append({
                'Item': current_item,
                'Type': current_type,
                'Fecha Llegada': row.iloc[2],
                'Fecha Envío': row.iloc[3],
                'Cantidad': row.iloc[4],
                'Proveedor_PO': row.iloc[5]
            })

    df_po = pd.DataFrame(df_po_rows)
    df_sin_requerimiento = pd.DataFrame(df_sin_req_rows)

    return df_po, df_sin_requerimiento

def cargar_archivos_estilo_escalera(archivos):
    """
    Carga múltiples archivos Excel con formato:
    - Columna A = Item
    - Columnas B en adelante = fechas con cantidades

    Devuelve:
    - DataFrame pivoteado con filas = Item + Snapshot, columnas = fechas
    - Lista de versiones / snapshots
    """
    lista_df = []

    for idx, file in enumerate(archivos):
        nombre_snapshot = f"Archivo_{idx+1}"
        df = pd.read_excel(file)

        # Validación mínima
        if df.shape[1] < 2:
            st.warning(f"⚠️ El archivo {file.name} no tiene suficientes columnas.")
            continue

        # Renombrar primera columna como 'Item'
        df.rename(columns={df.columns[0]: "Item"}, inplace=True)

        # Transformar a formato largo
        df_largo = df.melt(id_vars=["Item"], var_name="Fecha", value_name="Cantidad")
        df_largo["Snapshot"] = nombre_snapshot
        lista_df.append(df_largo)

    if not lista_df:
        st.error("❌ No se pudieron procesar los archivos.")
        return None, []

    # Combinar todo
    df_todo = pd.concat(lista_df)

    # Pivotear para mostrar como escalera: filas = Item + Snapshot, columnas = fechas
    df_pivot = df_todo.pivot_table(
        index=["Item", "Snapshot"],
        columns="Fecha",
        values="Cantidad",
        aggfunc="first"
    ).reset_index()

    # Ordenar columnas de fecha (ignorando errores si son string)
    try:
        fechas_ordenadas = sorted([col for col in df_pivot.columns if isinstance(col, pd.Timestamp) or "-" in str(col)],
                                  key=lambda x: pd.to_datetime(x, errors='coerce'))
        df_pivot = df_pivot[["Item", "Snapshot"] + fechas_ordenadas]
    except:
        pass

    # Agregar columna opcional de Release Date vacía
    df_pivot["Release Date"] = ""

    return df_pivot, [f"Archivo_{i+1}" for i in range(len(archivos))]


def exportar_excel(df):
    """
    Genera archivo Excel descargable en memoria
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Escalera")
    output.seek(0)
    return output


def graficar_evolucion_item(df, item):
    """
    Gráfica clara por ítem mostrando evolución por fecha en cada snapshot
    """
    import plotly.graph_objects as go

    df_largo = df.melt(id_vars=["Item", "Snapshot"], var_name="Fecha", value_name="Cantidad")
    df_largo = df_largo[df_largo["Item"] == item].dropna()

    if df_largo.empty:
        st.warning("No hay datos para graficar este ítem.")
        return

    # Asegurar formato de fechas
    df_largo["Fecha"] = pd.to_datetime(df_largo["Fecha"], errors="coerce")
    df_largo = df_largo.dropna(subset=["Fecha"]).sort_values("Fecha")

    fig = go.Figure()

    for snapshot in df_largo["Snapshot"].unique():
        df_snapshot = df_largo[df_largo["Snapshot"] == snapshot]
        fig.add_trace(go.Scatter(
            x=df_snapshot["Fecha"],
            y=df_snapshot["Cantidad"],
            mode="lines+markers",
            name=snapshot,
            line=dict(width=2),
            marker=dict(size=6)
        ))

    fig.update_layout(
        title=f"Evolución de cantidades para '{item}' por fecha",
        xaxis_title="Fecha",
        yaxis_title="Cantidad",
        legend_title="Versión",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)
