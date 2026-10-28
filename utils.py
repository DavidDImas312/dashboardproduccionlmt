# utils.py
import pandas as pd
import streamlit as st
import io
import re
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


# Catálogo de razones de Downtime
catalogo_downtime = pd.DataFrame({
    "Reason ID": [
        "D001", "D002", "D003", "D004", "D005", "D006", "D007", "D008", "D009", "D010",
        "D011", "D012", "D013", "D014", "D015", "D016", "D017", "D018", "D019", "D020",
        "D021", "D022", "D023", "D024", "D025", "D026", "D027", "D028", "D029", "D030",
        "D031", "D032", "D033", "D034", "D035", "D036", "D037", "D038", "D039", "D040",
        "D041", "D042", "D043", "D044", "D045", "D046", "D047", "D048", "D049", "D050",
        "D051", "D052", "D053", "D054", "D055", "D056", "D057", "D058", "D059", "D060",
        "D061", "D062", "D063", "D064", "D065", "D066", "D067", "D068", "D069", "D070",
        "D071", "D072", "D073", "D074", "D075", "D076", "D077", "D078", "D079", "D080",
        "D081", "D082", "D083", "D63.5", "D69.5", "D084", "D68.5", "D085", "D086", "D087",
        "D088", "D089", "D090", "D091"
    ],

    "Área responsable": [
        "Producción",
        "Producción",
        "Producción",
        "Producción",
        "Producción",
        "Producción",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Logística",
        "Logística",
        "Logística",
        "Logística",
        "Logística",
        "Logística",
        "Calidad",
        "Calidad",
        "Producción",
        "Producción",
        "Producción",
        "Producción",
        "Producción",
        "Producción",
        "Producción",
        "Producción",
        "Producción",
        "Producción",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Mantenimiento",
        "Logística",
        "Logística",
        "Logística",
        "Logística",
        "Logística",
        "Logística",
        "Calidad",
        "Calidad",
        "Calidad",
        "Calidad",
        "MRO",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Mantenimiento",
        "Logística",
        "Herramental",
        "Logística",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental",
        "Herramental"
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
    """
    Procesa el reporte Downtime.

    Extrae:
    - W/C: identificador del centro de trabajo.
    - Horas Downtime: horas registradas.
    - Razones: código de la razón de paro.
    - Description: descripción obtenida del encabezado del Excel.

    Omite:
    - Filas de totales.
    - Encabezados generales.
    - Filas correspondientes a W/C Type.
    """

    data = []

    current_reason_id = None
    current_description = None

    # Ejemplos:
    # D007-AJUSTE POR REBABA
    # D016-CILINDROS O RESORTES DAÑADOS
    # D63.5-DESCRIPCIÓN
    patron_razon = re.compile(
        r"^\s*(D\d+(?:\.\d+)?)\s*-\s*(.+?)\s*$",
        re.IGNORECASE,
    )

    # W/C Type que deben omitirse.
    wc_types_omitidos = {
        "PRESS - PRESS",
        "PRESS - PRESS",  # Incluye variantes de mayúsculas/minúsculas.
        "PROD N5 - PROD N5",
        "WELDING N2 - WELD N2",
        "PROD N4 - PROD N4",
    }

    for _, row in df.iterrows():

        valor = row.get("WorkCenter")

        if pd.isna(valor):
            continue

        texto = str(valor).strip()

        if not texto:
            continue

        texto_upper = texto.upper()

        # ----------------------------------------------------
        # 1. Omitir encabezados generales, W/C Type y totales.
        # ----------------------------------------------------
        if (
            texto_upper.startswith("TOTAL")
            or texto_upper in wc_types_omitidos
            or texto_upper == "DOWN TIME BY WC"
        ):
            continue

        # ----------------------------------------------------
        # 2. Identificar encabezados de razones de paro.
        # ----------------------------------------------------
        if " - " in texto:

            partes = texto.split(" - ", 1)

            izquierda = partes[0].strip()
            derecha = partes[1].strip()

            razon_izquierda = patron_razon.fullmatch(izquierda)
            razon_derecha = patron_razon.fullmatch(derecha)

            # Es un encabezado de razón si ambas partes contienen
            # el mismo código y la misma descripción.
            if razon_izquierda and razon_derecha:

                codigo_izquierdo = razon_izquierda.group(1).upper()
                descripcion_izquierda = razon_izquierda.group(2).strip()

                codigo_derecho = razon_derecha.group(1).upper()
                descripcion_derecha = razon_derecha.group(2).strip()

                if (
                    codigo_izquierdo == codigo_derecho
                    and descripcion_izquierda.casefold()
                    == descripcion_derecha.casefold()
                ):
                    current_reason_id = codigo_izquierdo
                    current_description = descripcion_izquierda
                    continue

            # Para el resto de las filas, tomar el identificador
            # que aparece antes del separador " - ".
            wc = izquierda

        else:
            # Si la fila no tiene el formato esperado, no se
            # puede identificar con seguridad como W/C.
            continue

        # ----------------------------------------------------
        # 3. No procesar centros si todavía no hay una razón.
        # ----------------------------------------------------
        if current_reason_id is None:
            continue

        # Evitar guardar códigos de razón como centros de trabajo.
        if patron_razon.fullmatch(wc):
            continue

        # ----------------------------------------------------
        # 4. Convertir horas y guardar el registro.
        # ----------------------------------------------------
        horas = pd.to_numeric(
            row.get("TotalHours"),
            errors="coerce",
        )

        if pd.isna(horas):
            continue

        data.append({
            "W/C": wc,
            "Horas Downtime": horas,
            "Razones": current_reason_id,
            "Description": current_description,
        })

    columnas_salida = [
        "W/C",
        "Horas Downtime",
        "Razones",
        "Description",
    ]

    return pd.DataFrame(data, columns=columnas_salida)

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
    Genera archivo Excel descargable en memoria.
    Si las columnas son MultiIndex, escribe también el índice para evitar error.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if isinstance(df.columns, pd.MultiIndex):
            df.to_excel(writer, index=True, sheet_name="Resumen")
        else:
            df.to_excel(writer, index=False, sheet_name="Resumen")
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

def procesar_montos_escalera(df):
    """
    Procesa columnas de montos (AF a AQ) en formato datetime con sufijo ".1".
    Devuelve un DataFrame en formato largo con columnas: Item, LMX, Cliente, Unit Price, Mes, Monto.
    """
    columnas_fijas = ["Item", "LMX", "Cliente", "Unit Price"]

    # Detectar columnas de montos (fechas con sufijo ".1")
    columnas_montos = [
        col for col in df.columns
        if (isinstance(col, pd.Timestamp) or isinstance(col, str))
        and ".1" in str(col)
        and "-" in str(col)
    ]

    # Formato largo
    df_montos = df.melt(
        id_vars=columnas_fijas,
        value_vars=columnas_montos,
        var_name="Mes",
        value_name="Monto"
    )

    # Limpiar el nombre de la columna y convertir a datetime
    df_montos["Mes"] = pd.to_datetime(df_montos["Mes"].apply(lambda x: str(x).replace(".1", "")), errors="coerce")
    df_montos.dropna(subset=["Mes", "Monto"], inplace=True)

    return df_montos

@st.cache_data
def cargar_production_timecards(file, skiprows=4):
    """
    Carga y procesa el reporte Production Timecards.

    El reporte contiene:
    - Registros individuales de producción.
    - Totales por W/C.
    - Totales por W/C Type.

    Los campos W/C Type y W/C que vienen vacíos por agrupación
    se heredan del registro anterior correspondiente.
    """

    try:
        # ---------------------------------------------------------
        # 1. Leer archivo
        # ---------------------------------------------------------
        df = pd.read_excel(
            file,
            skiprows=skiprows,
            engine="openpyxl"
        )

        # ---------------------------------------------------------
        # 2. Limpiar encabezados
        # ---------------------------------------------------------
        df.columns = (
            df.columns
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

        # ---------------------------------------------------------
        # 3. Validar columnas requeridas
        # ---------------------------------------------------------
        columnas_faltantes = [
            col
            for col in required_columns
            if col not in df.columns
        ]

        if columnas_faltantes:
            return None, (
                "Faltan las siguientes columnas en "
                f"Production Timecards: {columnas_faltantes}"
            )

        # ---------------------------------------------------------
        # 4. Conservar columnas requeridas
        # ---------------------------------------------------------
        df = df[required_columns].copy()

        # ---------------------------------------------------------
        # 5. Limpiar strings
        # ---------------------------------------------------------
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = (
                    df[col]
                    .astype("string")
                    .str.strip()
                )

        # ---------------------------------------------------------
        # 6. Inicializar clasificación
        # ---------------------------------------------------------
        df["Record Type"] = "Detail"

        df["Total Level"] = pd.NA

        # ---------------------------------------------------------
        # 7. Detectar filas de totales
        # ---------------------------------------------------------
        texto_wc_type = (
            df["W/C Type"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        texto_wc = (
            df["W/C"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        mask_total_wc_type = texto_wc_type.str.startswith(
            "Totals for",
            na=False
        )

        mask_total_wc = texto_wc.str.startswith(
            "Totals for",
            na=False
        )

        # Total por W/C Type
        df.loc[mask_total_wc_type, "Record Type"] = "W/C Type Total"
        df.loc[mask_total_wc_type, "Total Level"] = "W/C Type"

        # Total por W/C
        df.loc[mask_total_wc, "Record Type"] = "W/C Total"
        df.loc[mask_total_wc, "Total Level"] = "W/C"

        # ---------------------------------------------------------
        # 8. Heredar W/C Type y W/C
        # ---------------------------------------------------------

        # Solo usamos los registros de detalle para construir
        # la relación de grupo.
        detail_mask = df["Record Type"] == "Detail"

        df["W/C Type"] = (
            df["W/C Type"]
            .where(detail_mask)
            .ffill()
        )

        df["W/C"] = (
            df["W/C"]
            .where(detail_mask)
            .ffill()
        )

        # ---------------------------------------------------------
        # 9. Restaurar información de los totales
        # ---------------------------------------------------------

        # Recorremos los registros para asignar correctamente
        # el grupo a las filas de totales.
        current_wc_type = None
        current_wc = None

        for idx in df.index:

            record_type = df.loc[idx, "Record Type"]

            if record_type == "Detail":

                if pd.notna(df.loc[idx, "W/C Type"]):
                    current_wc_type = df.loc[idx, "W/C Type"]

                if pd.notna(df.loc[idx, "W/C"]):
                    current_wc = df.loc[idx, "W/C"]

            elif record_type == "W/C Total":

                df.loc[idx, "W/C Type"] = current_wc_type

                texto = str(
                    df.loc[idx, "W/C"]
                ).strip()

                if texto.startswith("Totals for"):
                    df.loc[idx, "W/C"] = texto.replace(
                        "Totals for",
                        "",
                        1
                    ).strip()

            elif record_type == "W/C Type Total":

                texto = str(
                    df.loc[idx, "W/C Type"]
                ).strip()

                if texto.startswith("Totals for"):
                    df.loc[idx, "W/C Type"] = texto.replace(
                        "Totals for",
                        "",
                        1
                    ).strip()

                df.loc[idx, "W/C"] = pd.NA

        # ---------------------------------------------------------
        # 10. Limpiar valores
        # ---------------------------------------------------------
        df = df.replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "None": pd.NA,
                "NaT": pd.NA,
                "-": pd.NA,
                "N/A": pd.NA,
            }
        )

        # ---------------------------------------------------------
        # 11. Convertir fecha
        # ---------------------------------------------------------
        if "Completed On" in df.columns:
            df["Completed On"] = pd.to_datetime(
                df["Completed On"],
                errors="coerce"
            )

        return df, None

    except Exception as e:

        return None, (
            "Error al cargar Production Timecards: "
            f"{str(e)}"
        )

def separar_production_timecards(df):
    """
    Separa Production Timecards en:
    - registros individuales
    - totales por W/C
    - totales por W/C Type
    """

    if df is None or df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Registros individuales
    df_detalle = df[
        df["Record Type"] == "Detail"
    ].copy()

    # Totales por W/C
    df_totales_wc = df[
        df["Record Type"] == "W/C Total"
    ].copy()

    # Totales por W/C Type
    df_totales_wc_type = df[
        df["Record Type"] == "W/C Type Total"
    ].copy()

    return (
        df_detalle,
        df_totales_wc,
        df_totales_wc_type
    )