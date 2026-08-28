import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from utils import (
    cargar_production_timecards,
    separar_production_timecards,
    cargar_datos_columnas_requeridas,
    required_columns,
    required_columns_plan,
    cargar_downtime,
    extraer_downtime,
    catalogo_downtime,
    filtrar_downtime,
)

# ============================================================
# SESSION STATE
# ============================================================

def inicializar_session_state():
    """Inicializa explícitamente todos los DataFrames usados por la aplicación."""
    estados_iniciales = {
        "df_clean": None,
        "df_produccion_detalle": None,
        "df_totales_wc": None,
        "df_totales_wc_type": None,
        "df_plan": None,
        "df_downtime": None,
        "df_downtime_procesado": None,
    }

    for key, value in estados_iniciales.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# ENTRY POINT
# ============================================================

def produccion_app():
    inicializar_session_state()

    menu_produccion = ["Importar Reportes", "Dashboard"]
    option = st.sidebar.selectbox("Acciones:", menu_produccion)

    if option == "Importar Reportes":
        importar_reportes()
    elif option == "Dashboard":
        dashboard()


# ============================================================
# IMPORTACIÓN DE REPORTES
# ============================================================

def importar_reportes():
    st.header("📥 Importar Reportes")

    # --------------------------------------------------------
    # Production Timecard
    # --------------------------------------------------------
    st.subheader("Production Timecard")
    uploaded_file = st.file_uploader(
        "Selecciona el archivo Excel del reporte",
        type=["xlsx"],
        key="production_file",
    )

    if uploaded_file is not None:
        df, error = cargar_production_timecards(
            uploaded_file,
            skiprows=4,
        )

        if df is None:
            st.error(f"❌ {error}")
        else:
                # ---------------------------------------------------------
                # Separar registros de producción y totales del reporte
                # ---------------------------------------------------------

                (
                    df_detalle,
                    df_totales_wc,
                    df_totales_wc_type
                ) = separar_production_timecards(df)

                # DataFrame completo
                st.session_state.df_clean = df

                # Registros individuales
                st.session_state.df_produccion_detalle = df_detalle

                # Totales por W/C
                st.session_state.df_totales_wc = df_totales_wc

                # Totales por W/C Type
                st.session_state.df_totales_wc_type = df_totales_wc_type

                st.success("✅ Archivo de Production Timecard cargado.")

                # ---------------------------------------------------------
                # Información de validación
                # ---------------------------------------------------------

                st.write(
                    f"Registros de producción: **{len(df_detalle):,}**"
                )

                st.write(
                    f"Totales por W/C: **{len(df_totales_wc):,}**"
                )

                st.write(
                    f"Totales por W/C Type: **{len(df_totales_wc_type):,}**"
                )

                if st.checkbox(
                    "Mostrar datos cargados",
                    key="show_production_data"
                ):
                    st.dataframe(
                        df,
                        use_container_width=True
                    )

    # --------------------------------------------------------
    # Scheduled Jobs
    # --------------------------------------------------------
    st.subheader("Scheduled Jobs")
    uploaded_plan = st.file_uploader(
        "Selecciona el archivo Excel de la programación",
        type=["xlsx"],
        key="plan",
    )

    if uploaded_plan is not None:
        df_plan, error = cargar_datos_columnas_requeridas(
            uploaded_plan,
            required_columns_plan,
            skiprows=5,
        )

        if df_plan is None:
            st.error(f"❌ {error}")
        else:
            st.session_state.df_plan = df_plan
            st.success("✅ Archivo de programación cargado.")

            if st.checkbox("Mostrar datos de programación", key="show_plan_data"):
                st.dataframe(df_plan, use_container_width=True)

    # --------------------------------------------------------
    # Downtime
    # --------------------------------------------------------
    st.subheader("Downtime por W/C")
    uploaded_downtime = st.file_uploader(
        "Selecciona el archivo Excel de Downtime",
        type=["xlsx"],
        key="downtime",
    )

    if uploaded_downtime is not None:
        df_downtime = cargar_downtime(uploaded_downtime)

        if df_downtime is None:
            st.error("❌ No se pudo leer el archivo de Downtime.")
        else:
            st.session_state.df_downtime = df_downtime
            df_downtime_procesado = extraer_downtime(df_downtime)
            st.session_state.df_downtime_procesado = df_downtime_procesado

            st.success("✅ Archivo de Downtime cargado y procesado.")

            if st.checkbox("Mostrar Downtime procesado", key="show_downtime_data"):
                st.dataframe(df_downtime_procesado, use_container_width=True)


# ============================================================
# FILTROS GLOBALES
# ============================================================

def obtener_filtros_globales(df):
    """
    Muestra y aplica los filtros globales del dashboard.

    Jerarquía:
        Fecha
          ↓
        Turno
          ↓
        W/C Type
          ↓
        W/C

    Los filtros dependientes se sincronizan para evitar
    conservar selecciones que ya no pertenecen al filtro padre.
    """

    df = df.copy()

    # ============================================================
    # LIMPIEZA BÁSICA
    # ============================================================

    df["Completed On"] = pd.to_datetime(
        df["Completed On"],
        errors="coerce"
    )

    # Limpiar columnas utilizadas en filtros
    for col in ["Shift", "W/C Type", "W/C"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
            )

    # ============================================================
    # FILTRO DE FECHAS
    # ============================================================

    fecha_min = df["Completed On"].min().date()
    fecha_max = df["Completed On"].max().date()

    fechas_globales = st.sidebar.date_input(
        "Selecciona rango de fechas",
        [fecha_min, fecha_max],
        key="filter_dates_global",
    )

    # Protección si Streamlit devuelve una sola fecha
    if not isinstance(fechas_globales, (list, tuple)):
        fechas_globales = [
            fechas_globales,
            fechas_globales
        ]

    if len(fechas_globales) == 1:
        fechas_globales = [
            fechas_globales[0],
            fechas_globales[0]
        ]

    fecha_inicio = pd.to_datetime(fechas_globales[0])

    fecha_fin = (
        pd.to_datetime(fechas_globales[1])
        + pd.Timedelta(days=1)
        - pd.Timedelta(seconds=1)
    )

    df_filtrado = df[
        (df["Completed On"] >= fecha_inicio)
        & (df["Completed On"] <= fecha_fin)
    ].copy()

    # ============================================================
    # FILTRO DE TURNOS
    # ============================================================

    turnos_disponibles = sorted(
        df_filtrado["Shift"]
        .dropna()
        .unique()
        .tolist(),
        key=str
    )

    # Recuperar selección anterior
    turnos_previos = st.session_state.get(
        "filter_shifts_global",
        turnos_disponibles
    )

    # Mantener solamente valores que siguen existiendo
    turnos_validos = [
        turno
        for turno in turnos_previos
        if turno in turnos_disponibles
    ]

    # Si no queda ninguno, seleccionar todos
    if not turnos_validos and turnos_disponibles:
        turnos_validos = turnos_disponibles

    selected_shifts_global = st.sidebar.multiselect(
        "Turno(s)",
        options=turnos_disponibles,
        default=turnos_validos,
        key="filter_shifts_global",
    )

    df_filtrado = df_filtrado[
        df_filtrado["Shift"].isin(selected_shifts_global)
    ].copy()

    # ============================================================
    # FILTRO W/C TYPE
    # ============================================================

    wc_types_disponibles = sorted(
        df_filtrado["W/C Type"]
        .dropna()
        .unique()
        .tolist(),
        key=str
    )

    wc_types_previos = st.session_state.get(
        "filter_wc_types_global",
        wc_types_disponibles
    )

    wc_types_validos = [
        wc_type
        for wc_type in wc_types_previos
        if wc_type in wc_types_disponibles
    ]

    if not wc_types_validos and wc_types_disponibles:
        wc_types_validos = wc_types_disponibles

    selected_wc_types_global = st.sidebar.multiselect(
        "Tipo(s) de Centro de Trabajo",
        options=wc_types_disponibles,
        default=wc_types_validos,
        key="filter_wc_types_global",
    )

    df_filtrado = df_filtrado[
        df_filtrado["W/C Type"].isin(
            selected_wc_types_global
        )
    ].copy()

    # ============================================================
    # FILTRO W/C
    # ============================================================

    wc_options = sorted(
        df_filtrado["W/C"]
        .dropna()
        .unique()
        .tolist(),
        key=str
    )

    # ------------------------------------------------------------
    # IMPORTANTE:
    # Sincronizar W/C con el W/C Type seleccionado
    # ------------------------------------------------------------

    wcs_previos = st.session_state.get(
        "filter_wcs_global",
        wc_options
    )

    wcs_validos = [
        wc
        for wc in wcs_previos
        if wc in wc_options
    ]

    # Si cambió W/C Type y los W/C anteriores ya no existen,
    # seleccionar automáticamente todos los W/C disponibles.
    if not wcs_validos and wc_options:
        wcs_validos = wc_options

    selected_wcs_global = st.sidebar.multiselect(
        "Centro(s) de Trabajo",
        options=wc_options,
        default=wcs_validos,
        key="filter_wcs_global",
    )

    df_wc = df_filtrado[
        df_filtrado["W/C"].isin(
            selected_wcs_global
        )
    ].copy()

    # ============================================================
    # DEBUG TEMPORAL
    # ============================================================

    # Puedes quitar esta sección después de validar el comportamiento.

    # st.sidebar.write("DEBUG")
    # st.sidebar.write("W/C Type:", selected_wc_types_global)
    # st.sidebar.write("W/C disponibles:", wc_options)
    # st.sidebar.write("W/C seleccionados:", selected_wcs_global)
    # st.sidebar.write("Registros:", len(df_wc))

    return (
        df_filtrado,
        df_wc,
        fechas_globales,
        selected_shifts_global,
        selected_wc_types_global,
        selected_wcs_global,
    )


# ============================================================
# PREPARACIÓN DE DOWNTIME
# ============================================================

def preparar_downtime(
    fechas_globales,
    selected_shifts_global,
    selected_wc_types_global,
    selected_wcs_global,
):
    """Filtra Downtime y agrega Description y Área responsable desde el catálogo."""

    df_downtime = st.session_state.df_downtime_procesado

    if df_downtime is None:
        return None

    df_downtime_filtrado = filtrar_downtime(
        df_downtime.copy(),
        fechas=fechas_globales,
        turnos=selected_shifts_global,
        wc_types=selected_wc_types_global,
        wcs=selected_wcs_global,
    )

    if df_downtime_filtrado is None:
        return None

    if df_downtime_filtrado.empty:
        return df_downtime_filtrado

    # Asegurar que Reason ID sea texto para que D63.5 / D69.5
    # se mantengan correctamente.
    df_downtime_filtrado["Razones"] = (
        df_downtime_filtrado["Razones"]
        .astype("string")
        .str.strip()
    )

    catalogo = catalogo_downtime.copy()
    catalogo["Reason ID"] = (
        catalogo["Reason ID"]
        .astype("string")
        .str.strip()
    )

    columnas_catalogo = ["Reason ID", "Description"]

    # Área responsable es opcional para mantener compatibilidad
    # mientras se actualiza utils.py.
    if "Área responsable" in catalogo.columns:
        columnas_catalogo.append("Área responsable")
    else:
        st.warning(
            "⚠️ El catálogo de Downtime todavía no contiene la columna "
            "'Área responsable'. Actualiza catalogo_downtime en utils.py."
        )

    # Evitar duplicación accidental si el catálogo tiene Reason ID repetido.
    catalogo = catalogo[columnas_catalogo].drop_duplicates(
        subset=["Reason ID"],
        keep="first",
    )

    df_downtime_filtrado = df_downtime_filtrado.merge(
        catalogo,
        left_on="Razones",
        right_on="Reason ID",
        how="left",
        validate="many_to_one",
    )

    return df_downtime_filtrado


# ============================================================
# KPI GENERALES
# ============================================================

def mostrar_kpis(df_filtrado):

    st.subheader("Resumen General")

    if df_filtrado is None or df_filtrado.empty:
        st.info("No hay datos para los filtros seleccionados.")
        return

    # --------------------------------------------------------
    # Obtener W/C Type seleccionados
    # --------------------------------------------------------

    wc_types_seleccionados = (
        df_filtrado["W/C Type"]
        .dropna()
        .unique()
        .tolist()
    )

    # --------------------------------------------------------
    # Obtener los totales por W/C Type
    # --------------------------------------------------------

    df_totales_wc_type = st.session_state.get(
        "df_totales_wc_type"
    )

    if (
        df_totales_wc_type is None
        or df_totales_wc_type.empty
    ):
        st.warning(
            "No se encontraron los totales por W/C Type "
            "del archivo Production Timecards."
        )
        return

    # --------------------------------------------------------
    # Filtrar total correspondiente al W/C Type
    # --------------------------------------------------------

    df_total_seleccionado = df_totales_wc_type[
        df_totales_wc_type["W/C Type"].isin(
            wc_types_seleccionados
        )
    ].copy()

    if df_total_seleccionado.empty:
        st.warning(
            "No se encontró el total correspondiente "
            "al W/C Type seleccionado."
        )
        return

    # --------------------------------------------------------
    # Convertir valores numéricos
    # --------------------------------------------------------

    columnas_numericas = [
        "Efficiency",
        "OEE",
        "Quantity",
        "Non-production Downtime Hours",
    ]

    for columna in columnas_numericas:

        if columna in df_total_seleccionado.columns:

            df_total_seleccionado[columna] = pd.to_numeric(
                df_total_seleccionado[columna],
                errors="coerce"
            )

    # ========================================================
    # CASO 1: UN SOLO W/C TYPE SELECCIONADO
    # ========================================================

    if len(wc_types_seleccionados) == 1:

        total = df_total_seleccionado.iloc[0]

        eficiencia = total["Efficiency"]
        oee = total["OEE"]
        cantidad = total["Quantity"]
        horas_no_produccion = total[
            "Non-production Downtime Hours"
        ]

    # ========================================================
    # CASO 2: VARIOS W/C TYPE SELECCIONADOS
    # ========================================================

    else:

        # Para Quantity y Non-production podemos sumar
        cantidad = df_total_seleccionado[
            "Quantity"
        ].sum()

        horas_no_produccion = df_total_seleccionado[
            "Non-production Downtime Hours"
        ].sum()

        # ----------------------------------------------------
        # IMPORTANTE:
        # No hacemos simplemente .mean() de Efficiency/OEE
        # porque los W/C Type pueden tener diferente volumen.
        #
        # Por ahora mostramos el promedio ponderado por Hours.
        # ----------------------------------------------------

        if "Hours" in df_total_seleccionado.columns:

            df_total_seleccionado["Hours"] = pd.to_numeric(
                df_total_seleccionado["Hours"],
                errors="coerce"
            ).fillna(0)

            horas = df_total_seleccionado["Hours"]

            if horas.sum() > 0:

                eficiencia = (
                    (
                        df_total_seleccionado["Efficiency"]
                        * horas
                    ).sum()
                    / horas.sum()
                )

                oee = (
                    (
                        df_total_seleccionado["OEE"]
                        * horas
                    ).sum()
                    / horas.sum()
                )

            else:
                eficiencia = df_total_seleccionado[
                    "Efficiency"
                ].mean()

                oee = df_total_seleccionado[
                    "OEE"
                ].mean()

        else:

            eficiencia = df_total_seleccionado[
                "Efficiency"
            ].mean()

            oee = df_total_seleccionado[
                "OEE"
            ].mean()

    # ========================================================
    # MOSTRAR KPIs
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Eficiencia",
        (
            f"{eficiencia:.2f}%"
            if pd.notna(eficiencia)
            else "N/D"
        ),
    )

    col2.metric(
        "OEE",
        (
            f"{oee:.2f}%"
            if pd.notna(oee)
            else "N/D"
        ),
    )

    col3.metric(
        "Cantidad Producida",
        (
            f"{cantidad:,.0f}"
            if pd.notna(cantidad)
            else "N/D"
        ),
    )

    col4.metric(
        "Horas No-Producción",
        (
            f"{horas_no_produccion:,.2f}"
            if pd.notna(horas_no_produccion)
            else "N/D"
        ),
    )

# ============================================================
# HELPERS PARA GRÁFICAS
# ============================================================

def configurar_layout(fig, height=500, margin_bottom=50):
    """Aplica el layout común a las gráficas Plotly."""
    fig.update_layout(
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        title_font=dict(size=18, color="white", family="Arial"),
        font=dict(size=12),
        margin=dict(t=50, l=50, r=30, b=margin_bottom),
    )
    return fig


def configurar_ejes(fig, x_grid=True, y_grid=False, x_title=None, y_title=None):
    fig.update_layout(
        xaxis=dict(
            showgrid=x_grid,
            gridcolor="lightgrey",
        ),
        yaxis=dict(
            showgrid=y_grid,
        ),
    )

    if x_title is not None:
        fig.update_layout(xaxis_title=x_title)
    if y_title is not None:
        fig.update_layout(yaxis_title=y_title)

    return fig


def agregar_texto_barra(fig, formato="%{text:.2f}", position="inside"):
    fig.update_traces(
        texttemplate=formato,
        textposition=position,
        insidetextanchor="middle",
    )
    return fig


# ============================================================
# GRÁFICAS DE PRODUCCIÓN
# ============================================================

def grafica_eficiencia_wc(df_wc):

    df_totales_wc = st.session_state.get(
        "df_totales_wc"
    )

    if (
        df_totales_wc is None
        or df_totales_wc.empty
    ):
        st.info(
            "No hay totales por W/C disponibles "
            "para calcular la eficiencia."
        )
        return

    # --------------------------------------------------------
    # W/C correspondientes al filtro actual
    # --------------------------------------------------------

    wc_seleccionados = (
        df_wc["W/C"]
        .dropna()
        .unique()
    )

    # --------------------------------------------------------
    # Obtener eficiencia del Total de cada W/C
    # --------------------------------------------------------

    efficiency_wc = (
        df_totales_wc[
            df_totales_wc["W/C"].isin(
                wc_seleccionados
            )
        ][
            ["W/C", "Efficiency"]
        ]
        .copy()
    )

    # --------------------------------------------------------
    # Conversión numérica
    # --------------------------------------------------------

    efficiency_wc["Efficiency"] = pd.to_numeric(
        efficiency_wc["Efficiency"],
        errors="coerce"
    )

    # Eliminar valores sin eficiencia
    efficiency_wc = efficiency_wc.dropna(
        subset=["Efficiency"]
    )

    # Ordenar de menor a mayor
    efficiency_wc = efficiency_wc.sort_values(
        by="Efficiency",
        ascending=True
    )

    if efficiency_wc.empty:
        st.info(
            "No hay datos de eficiencia para "
            "los filtros seleccionados."
        )
        return

    # --------------------------------------------------------
    # Gráfica
    # --------------------------------------------------------

    fig = px.bar(
        efficiency_wc,
        x="W/C",
        y="Efficiency",
        text="Efficiency",
        color="Efficiency",
        color_continuous_scale="RdYlGn",
        title="Eficiencia por W/C",
        labels={
            "W/C": "Centro de Trabajo (W/C)",
            "Efficiency": "Eficiencia (%)",
        },
        height=500,
    )

    agregar_texto_barra(
        fig,
        "%{text:.1f}%"
    )

    configurar_layout(
        fig,
        margin_bottom=80
    )

    configurar_ejes(
        fig,
        x_grid=False,
        y_grid=True,
        x_title="Centro de Trabajo (W/C)",
        y_title="Eficiencia (%)",
    )

    fig.update_yaxes(
        range=[0, 100]
    )

    fig.update_xaxes(
        tickangle=35
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

def grafica_produccion_wc(df_wc):
    df_unique = df_wc.drop_duplicates(subset=["Timesheet #"])

    quantity_wc = (
        df_unique.groupby("W/C")["Quantity"]
        .sum()
        .reset_index()
        .sort_values(by="Quantity", ascending=True)
    )

    fig = px.bar(
        quantity_wc,
        x="Quantity",
        y="W/C",
        text="Quantity",
        color="Quantity",
        color_continuous_scale="RdYlGn",
        title="Golpes por W/C",
        labels={
            "Quantity": "Golpes por W/C",
            "W/C": "Centro de Trabajo (W/C)",
        },
        height=500,
    )

    agregar_texto_barra(fig, "%{text:,}")
    configurar_layout(fig)
    configurar_ejes(
        fig,
        x_grid=True,
        y_grid=False,
        x_title="Golpes por W/C",
        y_title="Centro de Trabajo (W/C)",
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# GRÁFICAS DE DOWNTIME
# ============================================================

def grafica_downtime_wc(df_downtime):
    downtime_wc = (
        df_downtime.groupby("W/C")["Horas Downtime"]
        .sum()
        .reset_index()
        .sort_values(by="Horas Downtime", ascending=True)
    )

    if downtime_wc.empty:
        st.info("No hay datos de Downtime para mostrar.")
        return

    fig = px.bar(
        downtime_wc,
        y="W/C",
        x="Horas Downtime",
        orientation="h",
        text="Horas Downtime",
        color="Horas Downtime",
        color_continuous_scale="RdYlGn_r",
        title="Downtime Total por W/C",
        labels={
            "W/C": "Centro de Trabajo (W/C)",
            "Horas Downtime": "Downtime (hrs)",
        },
        height=600,
    )

    agregar_texto_barra(fig, "%{text:.2f}")
    configurar_layout(fig, height=600)
    configurar_ejes(
        fig,
        x_grid=True,
        y_grid=False,
        x_title="Downtime (hrs)",
        y_title="Centro de Trabajo (W/C)",
    )

    st.plotly_chart(fig, use_container_width=True)


def grafica_downtime_area(df_downtime):
    if "Área responsable" not in df_downtime.columns:
        st.warning("No existe 'Área responsable' en el catálogo de Downtime.")
        return

    downtime_area = (
        df_downtime.groupby("Área responsable")["Horas Downtime"]
        .sum()
        .reset_index()
        .sort_values(by="Horas Downtime", ascending=True)
    )

    if downtime_area.empty:
        st.info("No hay datos de Downtime para mostrar.")
        return

    fig = px.bar(
        downtime_area,
        x="Horas Downtime",
        y="Área responsable",
        orientation="h",
        text="Horas Downtime",
        color="Horas Downtime",
        color_continuous_scale="RdYlGn_r",
        title="Downtime Total por Área Responsable",
        labels={
            "Horas Downtime": "Downtime (hrs)",
            "Área responsable": "Área Responsable",
        },
        height=500,
    )

    agregar_texto_barra(fig, "%{text:.2f}")
    configurar_layout(fig)
    configurar_ejes(
        fig,
        x_grid=True,
        y_grid=False,
        x_title="Downtime (hrs)",
        y_title="Área Responsable",
    )

    st.plotly_chart(fig, use_container_width=True)


def grafica_top_razones_downtime(df_downtime):
    if "Description" not in df_downtime.columns:
        st.warning("No existe 'Description' en el catálogo de Downtime.")
        return

    top_razones = (
        df_downtime.groupby("Description")["Horas Downtime"]
        .sum()
        .reset_index()
        .sort_values(by="Horas Downtime", ascending=False)
        .head(10)
        .sort_values(by="Horas Downtime", ascending=True)
    )

    if top_razones.empty:
        st.info("No hay razones de Downtime para mostrar.")
        return

    fig = px.bar(
        top_razones,
        x="Horas Downtime",
        y="Description",
        orientation="h",
        text="Horas Downtime",
        color="Horas Downtime",
        color_continuous_scale="RdYlGn_r",
        title="Top 10 Razones de Downtime",
        labels={
            "Horas Downtime": "Downtime (hrs)",
            "Description": "Razón",
        },
        height=550,
    )

    agregar_texto_barra(fig, "%{text:.2f}")
    configurar_layout(fig, height=550)
    configurar_ejes(
        fig,
        x_grid=True,
        y_grid=False,
        x_title="Downtime (hrs)",
        y_title="Razón",
    )

    st.plotly_chart(fig, use_container_width=True)


def grafica_downtime_area_wc(df_downtime):
    if "Área responsable" not in df_downtime.columns:
        st.warning("No existe 'Área responsable' en el catálogo de Downtime.")
        return

    downtime_area_wc = (
        df_downtime.groupby(
            ["Área responsable", "W/C"]
        )["Horas Downtime"]
        .sum()
        .reset_index()
    )

    if downtime_area_wc.empty:
        st.info("No hay datos de Downtime para mostrar.")
        return

    fig = px.bar(
        downtime_area_wc,
        x="Horas Downtime",
        y="W/C",
        color="Área responsable",
        orientation="h",
        barmode="group",
        title="Downtime por Área y Centro de Trabajo",
        labels={
            "Horas Downtime": "Downtime (hrs)",
            "W/C": "Centro de Trabajo",
            "Área responsable": "Área Responsable",
        },
        height=600,
    )

    configurar_layout(fig, height=600)
    configurar_ejes(
        fig,
        x_grid=True,
        y_grid=False,
        x_title="Downtime (hrs)",
        y_title="Centro de Trabajo (W/C)",
    )
    fig.update_layout(legend_title_text="Área Responsable")

    st.plotly_chart(fig, use_container_width=True)


def mostrar_kpis_downtime(df_downtime):
    total_downtime = df_downtime["Horas Downtime"].sum()
    total_areas = (
        df_downtime["Área responsable"].nunique()
        if "Área responsable" in df_downtime.columns
        else 0
    )
    total_razones = (
        df_downtime["Description"].nunique()
        if "Description" in df_downtime.columns
        else df_downtime["Razones"].nunique()
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Downtime Total", f"{total_downtime:,.2f} h")
    col2.metric("Áreas Responsables", total_areas)
    col3.metric("Razones Registradas", total_razones)


def mostrar_seccion_downtime(df_downtime):
    st.subheader("⏱️ Análisis de Downtime")

    if df_downtime is None:
        st.warning(
            "Debes cargar y procesar el archivo de Downtime para mostrar esta sección."
        )
        return

    if df_downtime.empty:
        st.info("No hay datos de Downtime con los filtros seleccionados.")
        return

    mostrar_kpis_downtime(df_downtime)

    col_a, col_b = st.columns(2)

    with col_a:
        grafica_downtime_wc(df_downtime)

    with col_b:
        grafica_downtime_area(df_downtime)

    col_c, col_d = st.columns(2)

    with col_c:
        grafica_top_razones_downtime(df_downtime)

    with col_d:
        grafica_downtime_area_wc(df_downtime)


# ============================================================
# GRÁFICAS OPERATIVAS
# ============================================================

def grafica_eficiencia_empleado(df_wc):
    eficiencia_empleado = (
        df_wc.groupby("Employee")["Efficiency"]
        .mean()
        .reset_index()
        .sort_values(by="Efficiency", ascending=False)
    )

    fig = px.bar(
        eficiencia_empleado,
        x="Efficiency",
        y="Employee",
        text=eficiencia_empleado["Efficiency"].round(1).astype(str) + "%",
        color="Efficiency",
        color_continuous_scale="RdYlGn",
        title="Eficiencia Promedio por Empleado",
        labels={
            "Efficiency": "Eficiencia (%)",
            "Employee": "Empleado",
        },
        height=600,
    )

    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle",
    )
    configurar_layout(fig, height=600)
    configurar_ejes(
        fig,
        x_grid=True,
        y_grid=False,
        x_title="Eficiencia (%)",
        y_title="Empleado",
    )
    fig.update_xaxes(range=[0, 100])

    st.plotly_chart(fig, use_container_width=True)


def grafica_oee_wc(df_wc):
    oee_wc = (
        df_wc.groupby("W/C")["OEE"]
        .mean()
        .reset_index()
        .sort_values(by="OEE", ascending=False)
    )

    if oee_wc.empty:
        st.info("No hay datos de OEE para mostrar.")
        return

    max_value = oee_wc["OEE"].max()
    oee_wc["TextPosition"] = oee_wc["OEE"].apply(
        lambda x: "inside" if x > max_value * 0.15 else "outside"
    )

    fig = px.bar(
        oee_wc,
        y="W/C",
        x="OEE",
        text=oee_wc["OEE"].apply(lambda x: f"{x:.2f}%"),
        color="OEE",
        color_continuous_scale="RdYlGn",
        title="OEE Promedio por W/C",
        labels={
            "OEE": "OEE Promedio (%)",
            "W/C": "Centro de Trabajo (W/C)",
        },
        height=500,
    )

    fig.update_traces(
        textposition=oee_wc["TextPosition"],
        insidetextanchor="middle",
    )
    configurar_layout(fig)
    configurar_ejes(
        fig,
        x_grid=True,
        y_grid=False,
        x_title="OEE Promedio (%)",
        y_title="Centro de Trabajo (W/C)",
    )
    fig.update_xaxes(range=[0, 100])

    st.plotly_chart(fig, use_container_width=True)

def grafica_horas_wc(df_wc):

    # ========================================================
    # Obtener totales por W/C
    # ========================================================

    df_totales_wc = st.session_state.get(
        "df_totales_wc"
    )

    if (
        df_totales_wc is None
        or df_totales_wc.empty
    ):
        st.info(
            "No hay totales por W/C disponibles "
            "para calcular las horas."
        )
        return

    # ========================================================
    # W/C correspondientes al filtro actual
    # ========================================================

    wc_seleccionados = (
        df_wc["W/C"]
        .dropna()
        .unique()
    )

    # ========================================================
    # Obtener Hours del Total de cada W/C
    # ========================================================

    horas_wc = (
        df_totales_wc[
            df_totales_wc["W/C"].isin(
                wc_seleccionados
            )
        ][
            ["W/C", "Hours"]
        ]
        .copy()
    )

    # ========================================================
    # Conversión numérica
    # ========================================================

    horas_wc["Hours"] = pd.to_numeric(
        horas_wc["Hours"],
        errors="coerce"
    )

    # Eliminar W/C sin valor de horas
    horas_wc = horas_wc.dropna(
        subset=["Hours"]
    )

    # Ordenar de mayor a menor
    horas_wc = horas_wc.sort_values(
        by="Hours",
        ascending=False
    )

    if horas_wc.empty:
        st.info(
            "No hay datos de horas para "
            "los filtros seleccionados."
        )
        return

    # ========================================================
    # Posición del texto
    # ========================================================

    max_value = horas_wc["Hours"].max()

    horas_wc["TextPosition"] = horas_wc["Hours"].apply(
        lambda x: (
            "inside"
            if x > max_value * 0.15
            else "outside"
        )
    )

    # ========================================================
    # Gráfica
    # ========================================================

    fig = px.bar(
        horas_wc,
        y="W/C",
        x="Hours",
        text="Hours",
        color="Hours",
        color_continuous_scale="RdYlGn",
        title="Total de Horas por W/C",
        labels={
            "Hours": "Total de Horas",
            "W/C": "Centro de Trabajo (W/C)",
        },
        height=500,
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition=horas_wc["TextPosition"],
        insidetextanchor="middle",
    )

    configurar_layout(fig)

    configurar_ejes(
        fig,
        x_grid=True,
        y_grid=False,
        x_title="Total de Horas",
        y_title="Centro de Trabajo (W/C)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


def grafica_nonproduction_wc(df_wc): 
    df_unique = df_wc.drop_duplicates(subset=["Timesheet #"]) 
    non_prod_wc = ( 
        df_unique.groupby("W/C")["Non-production Downtime Hours"] 
        .sum() 
        .reset_index() 
        .sort_values(by="Non-production Downtime Hours", ascending=False) 
        ) 

    if non_prod_wc.empty: 
        st.info("No hay datos de horas no-producción para mostrar.") 
        return 

    max_value = non_prod_wc["Non-production Downtime " \
    "Hours"].max() 
    non_prod_wc["TextPosition"] = non_prod_wc["Non-production Downtime Hours"].apply( 
        lambda x: "inside" if x > max_value * 0.15 else "outside" 
        )

    fig = px.bar( 
        non_prod_wc, 
        y="W/C", 
        x="Non-production Downtime Hours", 
        text=non_prod_wc["Non-production Downtime Hours"].round(2).astype(str), 
        color="Non-production Downtime Hours", 
        color_continuous_scale="RdYlGn_r", 
        title="Total de Horas No-Producción por W/C", 
        labels={ "Non-production Downtime Hours": "Horas No-Producción", "W/C": "Centro de Trabajo (W/C)", }, 
        height=500, 
        )
     
    fig.update_traces( 
        textposition=non_prod_wc["TextPosition"], 
        insidetextanchor="middle", 
        )
    
    configurar_layout(fig) 
    configurar_ejes( 
        fig, 
        x_grid=True, 
        y_grid=False, 
        x_title="Total de Horas No-Producción", 
        y_title="Centro de Trabajo (W/C)", 
        )
    st.plotly_chart(fig, use_container_width=True)

def grafica_scrap_wc(df_wc):

    # ========================================================
    # Obtener totales por W/C
    # ========================================================

    df_totales_wc = st.session_state.get(
        "df_totales_wc"
    )

    if (
        df_totales_wc is None
        or df_totales_wc.empty
    ):
        st.info(
            "No hay totales por W/C disponibles "
            "para calcular el Scrap."
        )
        return

    # ========================================================
    # W/C correspondientes al filtro actual
    # ========================================================

    wc_seleccionados = (
        df_wc["W/C"]
        .dropna()
        .unique()
    )

    # ========================================================
    # Obtener Scrap del Total de cada W/C
    # ========================================================

    scrap_wc = (
        df_totales_wc[
            df_totales_wc["W/C"].isin(
                wc_seleccionados
            )
        ][
            ["W/C", "Scrap"]
        ]
        .copy()
    )

    # ========================================================
    # Conversión numérica
    # ========================================================

    scrap_wc["Scrap"] = pd.to_numeric(
        scrap_wc["Scrap"],
        errors="coerce"
    )

    # Eliminar valores sin dato
    scrap_wc = scrap_wc.dropna(
        subset=["Scrap"]
    )

    # Ordenar de mayor a menor
    scrap_wc = scrap_wc.sort_values(
        by="Scrap",
        ascending=False
    )

    if scrap_wc.empty:
        st.info(
            "No hay datos de Scrap "
            "para los filtros seleccionados."
        )
        return

    # ========================================================
    # Posición del texto
    # ========================================================

    max_value = scrap_wc["Scrap"].max()

    scrap_wc["TextPosition"] = scrap_wc["Scrap"].apply(
        lambda x:
            "inside"
            if x > max_value * 0.15
            else "outside"
    )

    # ========================================================
    # Gráfica
    # ========================================================

    fig = px.bar(
        scrap_wc,
        y="W/C",
        x="Scrap",
        text="Scrap",
        color="Scrap",
        color_continuous_scale="RdYlGn_r",
        title="Scrap por W/C",
        labels={
            "Scrap": "Scrap (Pzas)",
            "W/C": "Centro de Trabajo (W/C)",
        },
        height=500,
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition=scrap_wc["TextPosition"],
        insidetextanchor="middle",
    )

    configurar_layout(fig)

    configurar_ejes(
        fig,
        x_grid=True,
        y_grid=False,
        x_title="Scrap (Pzas)",
        y_title="Centro de Trabajo (W/C)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

def grafica_runrate_wc(df_wc, selected_shifts_global):

    # ========================================================
    # Obtener totales por W/C
    # ========================================================

    df_totales_wc = st.session_state.get(
        "df_totales_wc"
    )

    if (
        df_totales_wc is None
        or df_totales_wc.empty
    ):
        st.info(
            "No hay totales por W/C disponibles "
            "para calcular el Run Rate."
        )
        return

    # ========================================================
    # W/C correspondientes al filtro actual
    # ========================================================

    wc_seleccionados = (
        df_wc["W/C"]
        .dropna()
        .unique()
    )

    # ========================================================
    # Obtener Run Rate del Total de cada W/C
    # ========================================================

    runrate_wc = (
        df_totales_wc[
            df_totales_wc["W/C"].isin(
                wc_seleccionados
            )
        ][
            [
                "W/C",
                "Expected Run Rate /hr",
                "Actual Run Rate /hr",
            ]
        ]
        .copy()
    )

    # ========================================================
    # Conversión numérica
    # ========================================================

    runrate_wc["Expected Run Rate /hr"] = pd.to_numeric(
        runrate_wc["Expected Run Rate /hr"],
        errors="coerce",
    )

    runrate_wc["Actual Run Rate /hr"] = pd.to_numeric(
        runrate_wc["Actual Run Rate /hr"],
        errors="coerce",
    )

    # ========================================================
    # Eliminar W/C sin datos
    # ========================================================

    runrate_wc = runrate_wc.dropna(
        subset=[
            "Expected Run Rate /hr",
            "Actual Run Rate /hr",
        ]
    )

    # Ordenar por Expected Run Rate
    runrate_wc = runrate_wc.sort_values(
        by="Expected Run Rate /hr",
        ascending=False,
    )

    if runrate_wc.empty:
        st.info(
            "No hay datos de Run Rate "
            "para los filtros seleccionados."
        )
        return

    # ========================================================
    # Convertir a formato largo para Plotly
    # ========================================================

    runrate_wc_melted = runrate_wc.melt(
        id_vars="W/C",
        value_vars=[
            "Expected Run Rate /hr",
            "Actual Run Rate /hr",
        ],
        var_name="Tipo",
        value_name="Run Rate",
    )

    # ========================================================
    # Posición del texto
    # ========================================================

    max_value = runrate_wc_melted["Run Rate"].max()

    runrate_wc_melted["TextPosition"] = (
        runrate_wc_melted["Run Rate"].apply(
            lambda x:
                "inside"
                if x > max_value * 0.15
                else "outside"
        )
    )

    # ========================================================
    # Gráfica
    # ========================================================

    fig = px.bar(
        runrate_wc_melted,
        y="W/C",
        x="Run Rate",
        color="Tipo",
        text=runrate_wc_melted["Run Rate"].apply(
            lambda x: f"{x:.2f}"
        ),
        barmode="group",
        color_discrete_map={
            "Expected Run Rate /hr": "#1f77b4",
            "Actual Run Rate /hr": "#ff7f0e",
        },
        labels={
            "Run Rate": "Run Rate (unidades/hr)",
            "W/C": "Centro de Trabajo (W/C)",
        },
        title="Expected vs Actual Run Rate por W/C",
        height=550,
    )

    fig.update_traces(
        textposition=runrate_wc_melted["TextPosition"],
        insidetextanchor="middle",
    )

    configurar_layout(
        fig,
        height=550
    )

    configurar_ejes(
        fig,
        x_grid=True,
        y_grid=False,
        x_title="Run Rate (unidades/hr)",
        y_title="Centro de Trabajo (W/C)",
    )

    fig.update_layout(
        legend_title_text=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# GRÁFICAS DE PERSONAL / TURNOS
# ============================================================

def grafica_empleados_turno(df_wc):
    empleados_turno = (
        df_wc.groupby("Shift")["Employee"]
        .nunique()
        .reset_index()
        .sort_values(by="Employee", ascending=True)
    )

    fig = px.bar(
        empleados_turno,
        x="Shift",
        y="Employee",
        text=empleados_turno["Employee"].astype(str),
        color="Employee",
        color_continuous_scale="RdYlGn",
        title="Empleados por Turno",
        labels={
            "Shift": "Turno",
            "Employee": "Empleados únicos",
        },
        height=500,
    )

    agregar_texto_barra(fig, "%{text}")
    configurar_layout(fig)
    configurar_ejes(
        fig,
        x_grid=False,
        y_grid=True,
        x_title="Turno",
        y_title="Empleados únicos",
    )

    st.plotly_chart(fig, use_container_width=True)


def grafica_wo_turno(df_wc):
    wo_por_turno = (
        df_wc.groupby("Shift")["Job #"]
        .nunique()
        .reset_index()
        .sort_values(by="Job #", ascending=True)
    )

    if wo_por_turno.empty:
        st.info("No hay Work Orders para mostrar.")
        return

    max_value = wo_por_turno["Job #"].max()
    wo_por_turno["TextPosition"] = wo_por_turno["Job #"].apply(
        lambda x: "inside" if x > max_value * 0.15 else "outside"
    )

    fig = px.bar(
        wo_por_turno,
        x="Shift",
        y="Job #",
        text=wo_por_turno["Job #"].apply(lambda x: f"{x:.0f}"),
        color="Job #",
        color_continuous_scale="RdYlGn",
        labels={
            "Job #": "Cantidad de Work Orders",
            "Shift": "Turno",
        },
        title="Work Orders por Turno",
        height=400,
    )

    fig.update_traces(
        textposition=wo_por_turno["TextPosition"],
        insidetextanchor="middle",
    )
    configurar_layout(fig, height=400)
    configurar_ejes(
        fig,
        x_grid=False,
        y_grid=True,
        x_title="Turno",
        y_title="Cantidad de Work Orders",
    )
    fig.update_layout(showlegend=False)

    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# TOP 5 CENTROS CRÍTICOS
# ============================================================

def mostrar_top5_centros(df_wc):
    st.subheader("📉 Centros de Trabajo con Indicadores Críticos")

    col_x, col_y, col_z = st.columns(3)

    # ========================================================
    # TOP 5 MENOR EFICIENCIA
    # ========================================================

    with col_x:
        st.markdown("**Menor Eficiencia (Top 5)**")

        df_totales_wc = st.session_state.get(
            "df_totales_wc"
        )

        if (
            df_totales_wc is None
            or df_totales_wc.empty
        ):
            st.info("No hay totales por W/C disponibles.")
        else:

            # Obtener únicamente los W/C que están presentes
            # en el filtro actual
            wc_seleccionados = (
                df_wc["W/C"]
                .dropna()
                .unique()
            )

            top5_low_eff = (
                df_totales_wc[
                    df_totales_wc["W/C"].isin(
                        wc_seleccionados
                    )
                ][
                    ["W/C", "Efficiency"]
                ]
                .copy()
                .sort_values(
                    by="Efficiency",
                    ascending=True
                )
                .head(5)
            )

            top5_low_eff["Efficiency"] = pd.to_numeric(
                top5_low_eff["Efficiency"],
                errors="coerce"
            )

            st.dataframe(
                top5_low_eff,
                use_container_width=True,
                hide_index=True
            )

    # ========================================================
    # TOP 5 DOWNTIME
    # ========================================================

    with col_y:
        st.markdown("**Más Tiempo de Downtime (Top 5)**")

        top5_downtime = (
            df_wc.groupby("W/C")[
                "Production Downtime Hours"
            ]
            .sum()
            .reset_index()
            .sort_values(
                by="Production Downtime Hours",
                ascending=False,
            )
            .head(5)
        )

        st.dataframe(
            top5_downtime,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # TOP 5 SCRAP
    # ========================================================

    with col_z:
        st.markdown("**Más Scrap (Top 5)**")

        top5_scrap = (
            df_wc.groupby("W/C")["Scrap"]
            .sum()
            .reset_index()
            .sort_values(
                by="Scrap",
                ascending=False
            )
            .head(5)
        )

        st.dataframe(
            top5_scrap,
            use_container_width=True,
            hide_index=True
        )
# ============================================================
# CUMPLIMIENTO AL PLAN
# ============================================================

def mostrar_cumplimiento_plan(df_filtrado):
    st.subheader("📈 Cumplimiento al Plan de Producción por W/C")

    if st.session_state.df_plan is None:
        st.info(
            "Carga primero el archivo de Scheduled Jobs para mostrar esta sección."
        )
        return

    df_plan = st.session_state.df_plan

    wc_types_local = sorted(
        df_filtrado["W/C Type"].dropna().unique().tolist(),
        key=str,
    )

    if not wc_types_local:
        st.info("No hay W/C Type disponibles con los filtros seleccionados.")
        return

    col_reset, col_filters = st.columns([1, 5])

    with col_filters:
        selected_plan_wc_type = st.selectbox(
            "Selecciona W/C Type para Cumplimiento al Plan:",
            options=wc_types_local,
            key="plan_wc_type",
        )

        df_plan_filtrado = df_plan[
            df_plan["W/C Type"] == selected_plan_wc_type
        ].copy()

        wc_local = sorted(
            df_plan_filtrado["W/C"].dropna().unique().tolist(),
            key=str,
        )

        selected_plan_wcs = st.multiselect(
            "Selecciona W/C (vacío = todos):",
            options=wc_local,
            key="plan_wcs",
        )

    if selected_plan_wcs:
        df_plan_filtrado = df_plan_filtrado[
            df_plan_filtrado["W/C"].isin(selected_plan_wcs)
        ].copy()

    if df_plan_filtrado.empty:
        st.info("No hay datos del plan para los filtros seleccionados.")
        return

    # --------------------------------------------------------
    # Cumplimiento agrupado
    # --------------------------------------------------------
    cumplimiento_plan = (
        df_plan_filtrado.groupby("W/C")[
            ["To Make", "Produced", "Can Make", "Remaining"]
        ]
        .sum()
        .reset_index()
    )

    denominador = cumplimiento_plan["To Make"].replace(0, pd.NA)

    cumplimiento_plan["Cumplimiento (%)"] = (
        cumplimiento_plan["Produced"]
        .div(denominador)
        .mul(100)
        .fillna(0)
        .round(2)
    )

    cumplimiento_plan = cumplimiento_plan.sort_values(
        by="Cumplimiento (%)",
        ascending=True,
    )

    fig = px.bar(
        cumplimiento_plan,
        x="W/C",
        y="Cumplimiento (%)",
        text=cumplimiento_plan["Cumplimiento (%)"].apply(
            lambda x: f"{x:.1f}%"
        ),
        color="Cumplimiento (%)",
        color_continuous_scale="teal",
        title=f"Cumplimiento al Plan ({selected_plan_wc_type})",
        labels={
            "Cumplimiento (%)": "Cumplimiento (%)",
            "W/C": "Centro de Trabajo",
        },
        height=450,
    )

    fig.update_traces(textposition="outside")
    configurar_layout(fig, height=450)
    configurar_ejes(
        fig,
        x_grid=False,
        y_grid=True,
        x_title="Centro de Trabajo",
        y_title="Cumplimiento (%)",
    )

    st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------------
    # Piezas faltantes
    # --------------------------------------------------------
    st.subheader("Piezas faltantes para cumplimiento")

    piezas_faltantes = (
        df_plan_filtrado.groupby("W/C")[["Can Make", "Remaining"]]
        .sum()
        .reset_index()
    )

    piezas_faltantes["Piezas Faltantes"] = piezas_faltantes["Remaining"]
    piezas_faltantes = piezas_faltantes.sort_values(
        by="Piezas Faltantes",
        ascending=True,
    )

    fig_faltantes = px.bar(
        piezas_faltantes,
        x="W/C",
        y="Piezas Faltantes",
        text=piezas_faltantes["Piezas Faltantes"],
        color="Piezas Faltantes",
        color_continuous_scale="oranges",
        title=f"Piezas Faltantes ({selected_plan_wc_type})",
        labels={
            "Piezas Faltantes": "Piezas Faltantes",
            "W/C": "Centro de Trabajo",
        },
        height=450,
    )

    fig_faltantes.update_traces(textposition="outside")
    configurar_layout(fig_faltantes, height=450)
    configurar_ejes(
        fig_faltantes,
        x_grid=False,
        y_grid=True,
        x_title="Centro de Trabajo",
        y_title="Piezas Faltantes",
    )

    st.plotly_chart(fig_faltantes, use_container_width=True)

    # --------------------------------------------------------
    # Tablas
    # --------------------------------------------------------
    st.subheader("📄 Datos Filtrados para Cumplimiento al Plan")

    columnas_plan = [
        "W/C Type",
        "W/C",
        "Job #",
        "Item",
        "To Make",
        "Can Make",
        "Remaining",
        "Produced",
    ]

    columnas_disponibles = [
        col for col in columnas_plan
        if col in df_plan_filtrado.columns
    ]

    st.dataframe(
        df_plan_filtrado[columnas_disponibles],
        use_container_width=True,
    )

    st.subheader("📊 Cumplimiento Agrupado por W/C")
    st.dataframe(cumplimiento_plan, use_container_width=True)


# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================

def dashboard():
    if st.session_state.df_produccion_detalle is None:
        st.warning(
            "Primero carga el reporte Production Timecard."
        )
        return

    df = st.session_state.df_produccion_detalle

    # --------------------------------------------------------
    # Filtros globales
    # --------------------------------------------------------
    (
        df_filtrado,
        df_wc,
        fechas_globales,
        selected_shifts_global,
        selected_wc_types_global,
        selected_wcs_global,
    ) = obtener_filtros_globales(df)

    if df_filtrado.empty:
        st.warning("No existen registros con los filtros seleccionados.")
        return

    # --------------------------------------------------------
    # KPIs
    # --------------------------------------------------------
    mostrar_kpis(df_filtrado)

    # --------------------------------------------------------
    # Top 5 críticos
    # --------------------------------------------------------
    if not df_wc.empty:
        mostrar_top5_centros(df_wc)

    # --------------------------------------------------------
    # Producción
    # --------------------------------------------------------
    st.subheader("Indicadores de Producción")

    col_a, col_b = st.columns(2)

    with col_a:
        grafica_eficiencia_wc(df_wc)

    with col_b:
        grafica_produccion_wc(df_wc)

    # --------------------------------------------------------
    # Downtime
    # --------------------------------------------------------
    df_downtime_filtrado = preparar_downtime(
        fechas_globales=fechas_globales,
        selected_shifts_global=selected_shifts_global,
        selected_wc_types_global=selected_wc_types_global,
        selected_wcs_global=selected_wcs_global,
    )

    mostrar_seccion_downtime(df_downtime_filtrado)

    # --------------------------------------------------------
    # Indicadores operativos
    # --------------------------------------------------------
    st.subheader("⚙️ Indicadores Operativos")

    col_a, col_b = st.columns(2)

    with col_a:
        grafica_eficiencia_empleado(df_wc)

    with col_b:
        grafica_oee_wc(df_wc)

    col_c, col_d = st.columns(2)

    with col_c:
        grafica_horas_wc(df_wc)

    with col_d:
        grafica_nonproduction_wc(df_wc)

    col_e, col_f = st.columns(2)

    with col_e:
        grafica_scrap_wc(df_wc)

    with col_f:
        grafica_runrate_wc(
            df_wc,
            selected_shifts_global,
        )

    # --------------------------------------------------------
    # Personal y Work Orders
    # --------------------------------------------------------
    st.subheader("👥 Indicadores de Personal y Carga de Trabajo")

    col_a, col_b = st.columns(2)

    with col_a:
        grafica_empleados_turno(df_wc)

    with col_b:
        grafica_wo_turno(df_wc)

    # --------------------------------------------------------
    # Plan de Producción
    # --------------------------------------------------------
    mostrar_cumplimiento_plan(df_filtrado)