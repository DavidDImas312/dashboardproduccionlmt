import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import locale
from utils import cargar_datos_columnas_requeridas, convertir_columnas_fecha, convertir_columnas_numericas, filter_by_columns, exportar_excel, procesar_montos_escalera


def ventas_app():
    menuventas = ["Importar Reportes", "Comparativa", "Órdenes por Plataforma", "Forecast de Compras"]
    option = st.sidebar.selectbox("Acciones:", menuventas)

    if option == "Importar Reportes":
        importar_ventas()

    elif option == "Comparativa":
        comparativa_grafica()
    
    elif option == "Órdenes por Plataforma":
        analizar_ordenes_por_plataforma()

    elif option == "Forecast de Compras":
        analizar_forecast_compras()

def importar_ventas():
    st.subheader("📥 Cargar Archivos")

    columnas_orders = ["Ship On", "Customer", "Item", "Amount"]
    columnas_sales = ["Invoice Date", "Customer", "Item", "Amount"]

    uploaded_orders = st.file_uploader("📄 Archivo de Orders", type=["xlsx"], key="orders")
    uploaded_sales = st.file_uploader("📄 Archivo de Ventas", type=["xlsx"], key="sales")


    uploaded_escalera = st.file_uploader("📄 Archivo Escalera de Ventas (con fechas)", type=["xlsx"], key="escalera")

    if uploaded_escalera:
        try:
            df_escalera_raw = pd.read_excel(uploaded_escalera)
            df_montos_escalera = procesar_montos_escalera(df_escalera_raw)

            st.session_state["df_escalera"] = df_montos_escalera
            st.success("✅ Archivo escalera procesado correctamente")

            if st.checkbox("🔍 Mostrar datos procesados de escalera"):
                st.dataframe(df_montos_escalera.head())

        except Exception as e:
            st.error(f"❌ Error procesando archivo escalera: {e}")

    if uploaded_orders and uploaded_sales:
        df_orders, error_orders = cargar_datos_columnas_requeridas(uploaded_orders, columnas_orders, skiprows=4)
        df_sales, error_sales = cargar_datos_columnas_requeridas(uploaded_sales, columnas_sales, skiprows=8)

        if error_orders:
            st.error(f"Error en Orders: {error_orders}")
            return
        if error_sales:
            st.error(f"Error en Ventas: {error_sales}")
            return

        # 📌 Guardar en session_state
        st.session_state.df_orders = df_orders
        st.session_state.df_sales = df_sales

        st.success("✅ Archivos cargados correctamente. Dirígete a la pestaña de Comparativa.")

        # Si quieres mostrar los datos cargados opcionalmente
        if st.checkbox("Mostrar Orders cargado"):
            st.dataframe(df_orders)

        if st.checkbox("Mostrar Ventas cargadas"):
            st.dataframe(df_sales)

def comparativa_grafica():

    st.title("📊 Comparativa Pronóstico vs Ventas")

    # 📌 Obtener los dataframes de sesión
    df_orders = st.session_state.get("df_orders", pd.DataFrame())
    df_sales = st.session_state.get("df_sales", pd.DataFrame())
    df_escalera = st.session_state.get("df_escalera", None)

    if df_escalera is not None and (
        "df_orders" not in st.session_state or st.session_state["df_orders"].empty
    ) and (
        "df_sales" not in st.session_state or st.session_state["df_sales"].empty
    ):
        clientes_disponibles = sorted(df_escalera["Cliente"].dropna().unique())
        clientes_filtrados = st.multiselect(
            "🔎 Filtrar por Cliente (opcional)",
            options=clientes_disponibles,
            default=clientes_disponibles
        )

        # Aplicar filtro
        df_escalera = df_escalera[df_escalera["Cliente"].isin(clientes_filtrados)]

        # 📊 Gráfico por Cliente
        resumen_cliente = df_escalera.groupby("Cliente")["Monto"].sum().reset_index()
        fig_cliente = px.bar(resumen_cliente, x="Cliente", y="Monto", text="Monto",
                            title="Ventas Totales por Cliente")
        fig_cliente.update_traces(texttemplate="%{text:$,.0f}", textposition="outside")
        fig_cliente.update_layout(yaxis_tickformat="$,.0f")
        st.plotly_chart(fig_cliente, use_container_width=True)

        # 📈 Gráfico por Mes
        
        # Crear rango completo de meses desde el mínimo al máximo
        fecha_inicio = df_escalera["Mes"].min().replace(day=1)
        fecha_fin = df_escalera["Mes"].max().replace(day=1)

        rango_completo = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='MS')

        # Agrupar ventas por mes
        resumen_mes = df_escalera.groupby("Mes")["Monto"].sum().reset_index()

        # Reindexar para incluir todos los meses, rellenando con 0 donde no hay datos
        resumen_mes = resumen_mes.set_index("Mes").reindex(rango_completo, fill_value=0).rename_axis("Mes").reset_index()
        
        resumen_mes["Mes_str"] = resumen_mes["Mes"].dt.strftime("%b-%Y")
        fig_mes = px.line(resumen_mes, x="Mes_str", y="Monto", markers=True,
                  title="Tendencia de Ventas por Mes",
                  labels={"Monto": "Monto ($)", "Mes_str": "Mes"})
        fig_mes.update_traces(mode="lines+markers", line=dict(width=3), marker=dict(size=6))
        fig_mes.update_layout(yaxis_tickformat="$,.0f", hovermode="x unified")
        st.plotly_chart(fig_mes, use_container_width=True)

        if df_escalera.empty:
            st.warning("⚠️ No hay datos para los clientes seleccionados.")
            st.stop()

    # 📌 Validar si NO hay orders ni sales ni escalera
    if df_orders.empty and df_sales.empty and df_escalera is None:
        st.warning("⚠️ No hay datos cargados. Ve a 'Importar Reportes' para cargar al menos un archivo.")
    st.stop()

    # 📌 Procesamiento de columnas
    df_orders = convertir_columnas_fecha(df_orders, ["Ship On"])
    df_sales = convertir_columnas_fecha(df_sales, ["Invoice Date"])
    df_orders["Amount"] = pd.to_numeric(df_orders["Amount"], errors='coerce')
    df_sales["Amount"] = pd.to_numeric(df_sales["Amount"], errors='coerce')

    # 📌 Filtro de cliente único o todos
    clientes_unicos = sorted(df_orders["Customer"].dropna().unique().tolist())
    cliente_seleccionado = st.sidebar.selectbox("📌 Filtrar por Cliente", ["Todos"] + clientes_unicos)

    # 📌 Agrupación temporal
    agrupacion = st.sidebar.radio("📊 Agrupar por:", ["Semana", "Mes"])

    if agrupacion == "Semana":
        df_orders["Periodo"] = df_orders["Ship On"].dt.to_period("W").dt.start_time
        df_sales["Periodo"] = df_sales["Invoice Date"].dt.to_period("W").dt.start_time
    else:
        df_orders["Periodo"] = df_orders["Ship On"].dt.to_period("M").dt.start_time
        df_sales["Periodo"] = df_sales["Invoice Date"].dt.to_period("M").dt.start_time

    # 📌 Obtener periodos disponibles después de crear 'Periodo'
    periodos_disponibles = sorted(df_sales["Periodo"].dropna().unique())

    # 📌 Formato de nombre según agrupación
    if agrupacion == "Semana":
        periodos_opciones = ["Todos"] + [p.strftime("Semana %U (%d-%b)") for p in periodos_disponibles]
        label_filtro = "📅 Filtrar por Semana"
    else:
        periodos_opciones = ["Todos"] + [p.strftime("%B %Y") for p in periodos_disponibles]
        label_filtro = "📅 Filtrar por Mes"

    # 📌 Filtro dinámico
    periodo_seleccionado = st.sidebar.selectbox(label_filtro, periodos_opciones)

    # 📌 Obtener datetime según selección
    if periodo_seleccionado != "Todos":
        index_seleccionado = periodos_opciones.index(periodo_seleccionado) - 1
        periodo_dt = periodos_disponibles[index_seleccionado]
    else:
        periodo_dt = None

    # 📌 Filtrar por periodo seleccionado
    if periodo_dt:
        df_orders_periodo = df_orders[df_orders["Periodo"] == periodo_dt]
        df_sales_periodo = df_sales[df_sales["Periodo"] == periodo_dt]
    else:
        df_orders_periodo = df_orders.copy()
        df_sales_periodo = df_sales.copy()

    # 📊 Resumen completo sin filtro de periodo (para gráfica general)
    periodos_totales_completo = sorted(set(df_orders["Periodo"]).union(set(df_sales["Periodo"])))
    clientes_totales_completo = sorted(
        set(df_orders["Customer"].dropna()).union(set(df_sales["Customer"].dropna())))

    base_completa = pd.MultiIndex.from_product([periodos_totales_completo, clientes_totales_completo],
                                               names=["Periodo", "Customer"]).to_frame(index=False)

    resumen_orders_completo = df_orders.groupby(["Periodo", "Customer"])["Amount"].sum().reset_index(
        name="Pronosticado")
    resumen_sales_completo = df_sales.groupby(["Periodo", "Customer"])["Amount"].sum().reset_index(name="Vendido")

    resumen_completo = base_completa.merge(resumen_orders_completo, on=["Periodo", "Customer"], how="left")
    resumen_completo = resumen_completo.merge(resumen_sales_completo, on=["Periodo", "Customer"], how="left")
    resumen_completo.fillna(0, inplace=True)
    resumen_completo["Diferencia"] = resumen_completo["Vendido"] - resumen_completo["Pronosticado"]

    col3, col4 = st.columns(2)
    with col3:
        st.metric("Órdenes Pronosticadas", f"${df_orders['Amount'].sum():,.2f}")
    with col4:
        st.metric("Ventas Totales", f"${df_sales['Amount'].sum():,.2f}")


    # 📊 Top 5 Clientes con Más Ventas en el periodo seleccionado
    resumen_ventas_periodo = df_sales_periodo.groupby("Customer")["Amount"].sum().reset_index(name="Vendido")

    # Si no hay ventas, evitar error
    if resumen_ventas_periodo.empty:
        st.warning("⚠️ No hay ventas registradas para este periodo.")
    else:
        resumen_ventas_periodo = resumen_ventas_periodo.sort_values("Vendido", ascending=False)

        top_mas = resumen_ventas_periodo.head(5)
        top_menos = resumen_ventas_periodo.tail(5).sort_values("Vendido")

        col1, col2 = st.columns(2)
        with col1:
            st.write("### 📉 Top 5 con Menos Ventas Realizadas")
            st.dataframe(top_menos.style.format({"Vendido": "${:,.2f}"}))

        with col2:
            st.write("### 📈 Top 5 con Más Ventas Realizadas")
            st.dataframe(top_mas.style.format({"Vendido": "${:,.2f}"}))


    # 📊 Ventas por Cliente (solo filtra por periodo)
    st.subheader("📊 Ventas por Cliente")

    # 📌 Obtener lista de clientes únicos
    clientes_unicos = sorted(set(df_orders["Customer"].dropna()).union(set(df_sales["Customer"].dropna())))

    # 📌 Expander con multiselect
    with st.expander("🔎 Filtro opcional por Cliente"):
        clientes_seleccionados = st.multiselect("Selecciona uno o más clientes", clientes_unicos)

    # 📌 Filtrar por periodo
    if periodo_dt:
        ventas_mes = df_sales_periodo.groupby("Customer")["Amount"].sum().reset_index(name="Vendido")
        pron_mes = df_orders_periodo.groupby("Customer")["Amount"].sum().reset_index(name="Pronosticado")
        titulo_mes = f" en {periodo_seleccionado}"
    else:
        # ✅ NUEVO: limitar pronóstico hasta la última venta real
        fecha_max_ventas = df_sales["Invoice Date"].max()
        df_orders_filtrado = df_orders[df_orders["Ship On"] <= fecha_max_ventas]

        ventas_mes = df_sales.groupby("Customer")["Amount"].sum().reset_index(name="Vendido")
        pron_mes = df_orders_filtrado.groupby("Customer")["Amount"].sum().reset_index(name="Pronosticado")
        titulo_mes = " (Todos los periodos)"


    # 📌 Unir ambos DataFrames
    df_ventas_completo = pd.merge(ventas_mes, pron_mes, on="Customer", how="outer").fillna(0)

    # 📌 Filtrar si se seleccionaron clientes específicos
    if clientes_seleccionados:
        df_ventas_completo = df_ventas_completo[df_ventas_completo["Customer"].isin(clientes_seleccionados)]

    # 📌 Ordenar por ventas
    df_ventas_completo = df_ventas_completo.sort_values("Vendido", ascending=True)

    # 📊 Gráfica combinada
    fig_mes = go.Figure()

    fig_mes.add_trace(go.Bar(
        x=df_ventas_completo["Customer"],
        y=df_ventas_completo["Vendido"],
        name="Vendido",
        marker_color="#F58518",
        text=df_ventas_completo["Vendido"],
        texttemplate="%{text:$,.0f}",
        textposition="outside"
    ))

    fig_mes.add_trace(go.Scatter(
        x=df_ventas_completo["Customer"],
        y=df_ventas_completo["Pronosticado"],
        mode="lines+markers",
        name="Pronosticado",
        line=dict(color="#1f77b4", width=3),
        marker=dict(size=6),
        hovertemplate="Pronosticado: %{y:$,.2f}<br>Cliente: %{x}<extra></extra>"
    ))

    fig_mes.update_layout(
        title=f"Ventas vs Pronóstico por Cliente{titulo_mes}",
        xaxis_title="Cliente",
        yaxis_title="Monto ($)",
        yaxis_tickformat="$,.2f",
        barmode="group",
        hovermode="x unified",
        template="plotly_white",
        xaxis_tickangle=-45,
        height=500
    )

    st.plotly_chart(fig_mes, use_container_width=True)

    st.subheader("📈 Ventas vs Pronóstico por Mes")

    # 📌 Copia y conversión de fechas
    df_orders_mes = df_orders.copy()
    df_sales_mes = df_sales.copy()

    df_orders_mes = convertir_columnas_fecha(df_orders_mes, ["Ship On"])
    df_sales_mes = convertir_columnas_fecha(df_sales_mes, ["Invoice Date"])

    # 📌 Crear columna de periodo mensual (primer día del mes)
    df_orders_mes["Periodo"] = df_orders_mes["Ship On"].dt.to_period("M").dt.to_timestamp()
    df_sales_mes["Periodo"] = df_sales_mes["Invoice Date"].dt.to_period("M").dt.to_timestamp()

    # 📌 Agrupar por mes
    ventas_por_mes = df_sales_mes.groupby("Periodo")["Amount"].sum().reset_index(name="Vendido")
    pronostico_por_mes = df_orders_mes.groupby("Periodo")["Amount"].sum().reset_index(name="Pronosticado")

    # 📌 Generar rango completo de meses
    min_fecha = min(ventas_por_mes["Periodo"].min(), pronostico_por_mes["Periodo"].min())
    max_fecha = max(ventas_por_mes["Periodo"].max(), pronostico_por_mes["Periodo"].max())
    rango_meses = pd.date_range(start=min_fecha, end=max_fecha, freq="MS")

    df_base = pd.DataFrame({"Periodo": rango_meses})

    # 📌 Unir datos con la base completa de meses
    df_mes = df_base.merge(ventas_por_mes, on="Periodo", how="left")
    df_mes = df_mes.merge(pronostico_por_mes, on="Periodo", how="left")
    df_mes.fillna(0, inplace=True)
    df_mes = df_mes.sort_values("Periodo")

    # 📊 Gráfica combinada
    fig_mes_tendencia = go.Figure()

    fig_mes_tendencia.add_trace(go.Bar(
        x=df_mes["Periodo"],
        y=df_mes["Vendido"],
        name="Vendido",
        marker_color="#F58518",
        text=df_mes["Vendido"],
        texttemplate="%{text:$,.0f}",
        textposition="outside"
    ))

    fig_mes_tendencia.add_trace(go.Scatter(
        x=df_mes["Periodo"],
        y=df_mes["Pronosticado"],
        mode="lines+markers",
        name="Pronosticado",
        line=dict(color="#1f77b4", width=3),
        marker=dict(size=6),
        hovertemplate="Pronosticado: %{y:$,.2f}<br>Mes: %{x|%B %Y}<extra></extra>"
    ))

    fig_mes_tendencia.update_layout(
        title="📊 Tendencia Mensual: Ventas vs Pronóstico",
        xaxis_title="Mes",
        yaxis_title="Monto ($)",
        yaxis_tickformat="$,.2f",
        barmode="group",
        hovermode="x unified",
        template="plotly_white",
        height=500
    )

    # ✅ Mostrar todos los meses en el eje X
    fig_mes_tendencia.update_xaxes(
        type="date",
        tickformat="%b %Y",
        tickangle=-45,
        tickvals=df_mes["Periodo"]
    )

    st.plotly_chart(fig_mes_tendencia, use_container_width=True)

    if cliente_seleccionado != "Todos" and periodo_dt:
        # 📊 Selector de tipo de gráfica
        tipo_grafica = st.sidebar.radio("📈 Tipo de gráfica:", ["Barras", "Líneas", "Dispersión", "Área"])

        # 📌 Filtrar resumen_completo según cliente
        resumen_filtrado = resumen_completo.copy()

        if cliente_seleccionado != "Todos":
            resumen_filtrado = resumen_filtrado[resumen_filtrado["Customer"] == cliente_seleccionado]

        # 📌 Quitar periodos sin datos (ambos en 0)
        resumen_filtrado = resumen_filtrado[
            ~((resumen_filtrado["Pronosticado"] == 0) & (resumen_filtrado["Vendido"] == 0))
        ]

        # 📌 Transformar a formato long para graficar
        resumen_melt = resumen_filtrado.melt(id_vars=["Periodo", "Customer"],
                                             value_vars=["Pronosticado", "Vendido"],
                                             var_name="Tipo", value_name="Monto")

        colores_personalizados = {
            "Pronosticado": "#4C78A8",
            "Vendido": "#F58518"
        }

        # 📊 Generar gráfica según tipo seleccionado
        if tipo_grafica == "Líneas":
            fig = px.line(resumen_melt, x="Periodo", y="Monto", color="Tipo", line_group="Customer",
                          custom_data=["Customer"], color_discrete_map=colores_personalizados,
                          title=f"Pronosticado vs Vendido: {cliente_seleccionado} - ({agrupacion})")

        elif tipo_grafica == "Dispersión":
            fig = px.scatter(resumen_melt, x="Periodo", y="Monto", color="Tipo", symbol="Customer",
                             custom_data=["Customer"], color_discrete_map=colores_personalizados,
                             title=f"Dispersión Pronosticado vs Vendido: {cliente_seleccionado} - ({agrupacion})")

        elif tipo_grafica == "Área":
            fig = px.area(resumen_melt, x="Periodo", y="Monto", color="Tipo", line_group="Customer",
                          custom_data=["Customer"], color_discrete_map=colores_personalizados,
                          title=f"Área Acumulada Pronosticado vs Vendido: {cliente_seleccionado} - ({agrupacion})")

        elif tipo_grafica == "Barras":
            fig = px.bar(resumen_melt, x="Periodo", y="Monto", color="Tipo",
                         barmode="group", custom_data=["Customer"],
                         color_discrete_map=colores_personalizados,
                         title=f"Pronosticado vs Vendido: {cliente_seleccionado} - ({agrupacion})")

        # 📌 Ajustes comunes a todas las gráficas
        fig.update_yaxes(tickformat="$,.2f")
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Cliente: %{customdata[0]}<br>Monto: %{y:$,.2f}<extra></extra>")
        fig.update_xaxes(type="date", 
                        tickformat="%b %Y",
                        tickangle=-45,
                        tickvals=df_mes["Periodo"])
        fig.update_layout(legend_title_text="Concepto", hovermode="x unified")

        st.plotly_chart(fig, use_container_width=True)

        # 📊 Gráfica detalle por Item de un cliente en ese mes
        st.subheader(f"📊 Detalle por Item de {cliente_seleccionado} en {periodo_seleccionado}")

        pron_item = df_orders[
            (df_orders["Periodo"] == periodo_dt) & (df_orders["Customer"] == cliente_seleccionado)
            ].groupby("Item")["Amount"].sum().reset_index(name="Pronosticado")

        vent_item = df_sales[
            (df_sales["Periodo"] == periodo_dt) & (df_sales["Customer"] == cliente_seleccionado)
            ].groupby("Item")["Amount"].sum().reset_index(name="Vendido")

        detalle_item = pd.merge(pron_item, vent_item, on="Item", how="outer").fillna(0)
        detalle_item["Diferencia"] = detalle_item["Vendido"] - detalle_item["Pronosticado"]

        # Derretir para gráfica
        detalle_melt = detalle_item.melt(id_vars="Item", value_vars=["Pronosticado", "Vendido"])

        # 📊 Gráfica de barras horizontal
        fig_items = px.bar(detalle_melt,
                           y="Item", x="value", color="variable",
                           color_discrete_map=colores_personalizados,
                           barmode="group",
                           title=f"Pronosticado vs Vendido por Item")

        fig_items.update_xaxes(tickformat="$,.2f")
        fig_items.update_layout(
            yaxis=dict(type="category", automargin=True),  # Forzar mostrar todos los items completos
            height=max(400, len(detalle_item) * 20),  # Ajustar altura dinámica según cantidad de items
            legend_title_text="Concepto",
            bargap=0.2
        )
        st.plotly_chart(fig_items, use_container_width=True)

        if st.checkbox("Mostrar Tabla Completa de Resumen"):
            st.dataframe(resumen_melt)
    else:
        st.info("Selecciona un cliente en el filtro lateral para ver más detalles.")


def analizar_ordenes_por_plataforma():
    st.subheader("📦 Análisis de Órdenes por Plataforma")

    uploaded_orders = st.file_uploader("📄 Cargar archivo de órdenes", type=["xlsx"], key="orders_platform")

    if uploaded_orders:
        columnas_requeridas = [
            "Week Of", "Ship From", "Customer", "Ship To", "Item", "On Hand",
            "Customer PO", "Order #", "Customer Item", "Wanted On", "Ship On",
            "Quantity", "Unit Price", "Amount", "Firm/Planned", "Platform"
        ]

        df_orders, error = cargar_datos_columnas_requeridas(uploaded_orders, columnas_requeridas, skiprows=4)

        if error:
            st.error(f"❌ Error en columnas: {error}")
            return

        df_orders = convertir_columnas_numericas(df_orders, ["Quantity", "Amount"])
        df_orders = convertir_columnas_fecha(df_orders, ["Wanted On"])

        # ==== FILTROS ====
        col1, col2, col3 = st.columns(3)

        with col1:
            plataformas = sorted(df_orders["Platform"].dropna().unique())
            plataformas_seleccionadas = st.multiselect("🎯 Plataforma(s)", plataformas, default=plataformas)

        # Actualizar ship_to dinámicamente según plataformas seleccionadas
        df_temp = df_orders[df_orders["Platform"].isin(plataformas_seleccionadas)] if plataformas_seleccionadas else df_orders
        destinos_disponibles = sorted(df_temp["Ship To"].dropna().unique())

        with col2:
            destinos_seleccionados = st.multiselect("🚚 Ship To", destinos_disponibles, default=destinos_disponibles)

        with col3:
            fechas_disponibles = df_temp["Wanted On"].dropna()

            if not fechas_disponibles.empty:
                min_date = fechas_disponibles.min().date()
                max_date = fechas_disponibles.max().date()

                fechas_seleccionadas = st.date_input(
                    "📆 Rango de fechas (Wanted On)",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )

                # 🔐 Forzamos validación
                if isinstance(fechas_seleccionadas, tuple) and len(fechas_seleccionadas) == 2:
                    fecha_inicio, fecha_fin = fechas_seleccionadas
                else:
                    st.warning("⚠️ Selecciona una fecha de inicio y una fecha final para mostrar los resultados.")
                    return
            else:
                st.warning("⚠️ No hay fechas disponibles en los datos para aplicar filtro.")
                return
    
        # ==== VALIDACIÓN DE FECHAS ====
        if not fecha_inicio or not fecha_fin:
            st.warning("⚠️ Por favor selecciona un rango de fechas válido para continuar.")
            return

        # ==== APLICAR FILTROS ====
        df_filtrado = df_orders.copy()
        if plataformas_seleccionadas:
            df_filtrado = df_filtrado[df_filtrado["Platform"].isin(plataformas_seleccionadas)]
        if destinos_seleccionados:
            df_filtrado = df_filtrado[df_filtrado["Ship To"].isin(destinos_seleccionados)]

        df_filtrado = df_filtrado[
            (df_filtrado["Wanted On"] >= pd.to_datetime(fecha_inicio)) &
            (df_filtrado["Wanted On"] <= pd.to_datetime(fecha_fin))
        ]

        if df_filtrado.empty:
            st.warning("⚠️ No hay datos para los filtros seleccionados.")
            return

        # ==== RESUMEN POR PLATAFORMA ====
        resumen = df_filtrado.groupby("Platform").agg(
            Total_Piezas=("Quantity", "sum"),
            Total_Monto=("Amount", "sum")
        ).reset_index()

        # Aplicar formatos
        resumen["Total_Piezas"] = resumen["Total_Piezas"].map("{:,.0f}".format)
        resumen["Total_Monto"] = resumen["Total_Monto"].map("${:,.2f}".format)

        st.markdown("### 📊 Resumen por Plataforma")
        st.dataframe(resumen)

        # ==== GRÁFICAS ====
        resumen_chart = df_filtrado.groupby("Platform").agg(
            Total_Piezas=("Quantity", "sum"),
            Total_Monto=("Amount", "sum")
        ).reset_index()

        col_pie1, col_pie2 = st.columns(2)
        with col_pie1:
            fig_piezas = px.pie(resumen_chart, values="Total_Piezas", names="Platform", title="Distribución de Piezas")
            st.plotly_chart(fig_piezas, use_container_width=True)

        with col_pie2:
            fig_monto = px.pie(resumen_chart, values="Total_Monto", names="Platform", title="Distribución de Monto")
            st.plotly_chart(fig_monto, use_container_width=True)

        # ==== RESUMEN POR DESTINO ====
        st.markdown("### 📦 Destino de Órdenes")
        destino_resumen = df_filtrado.groupby("Ship To").agg(
            Piezas=("Quantity", "sum"),
            Monto=("Amount", "sum")
        ).reset_index()

        destino_resumen["Piezas"] = destino_resumen["Piezas"].map("{:,.0f}".format)
        destino_resumen["Monto"] = destino_resumen["Monto"].map("${:,.2f}".format)

        st.dataframe(destino_resumen)

        # ==== EXPORTACIÓN ====
        st.download_button(
            label="⬇️ Descargar resumen en Excel",
            data=exportar_excel(resumen_chart),
            file_name="resumen_por_plataforma.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def analizar_forecast_compras():
    st.subheader("📦 Análisis de Forecast de Compras")

    uploaded_file = st.file_uploader("📄 Cargar archivo de forecast de compras", type=["xlsx"], key="forecast_compras")

    if uploaded_file:
        columnas_requeridas = ["Item", "Type", "Wanted On", "Quantity", "Datos", "Vendor", "PO", "Unit Price (MXN)", "Total"]
        df, error = cargar_datos_columnas_requeridas(uploaded_file, columnas_requeridas)

        if error:
            st.error(f"❌ Error en archivo: {error}")
            return

        # Procesar columnas
        df = convertir_columnas_fecha(df, ["Wanted On"])
        df = convertir_columnas_numericas(df, ["Quantity", "Unit Price (MXN)", "Total"])

        # ==== FILTROS DINÁMICOS EN LA SIDEBAR ====
        with st.sidebar:
            st.markdown("### 🎯 Filtros de Forecast de Compras")

            # ==== FILTRO 1: Type ====
            types_disponibles = sorted(df["Type"].dropna().unique())
            type_seleccionado = st.multiselect("🏷️ Tipo(s)", types_disponibles, default=types_disponibles)

            df_temp = df[df["Type"].isin(type_seleccionado)] if type_seleccionado else df.copy()

            # ==== FILTRO 2: Vendor ====
            vendors_disponibles = sorted(df_temp["Vendor"].dropna().unique())
            proveedores_seleccionados = st.multiselect("🏢 Proveedor(es)", vendors_disponibles, default=vendors_disponibles)

            df_temp = df_temp[df_temp["Vendor"].isin(proveedores_seleccionados)] if proveedores_seleccionados else df_temp

            # ==== FILTRO 3: PO ====
            pos_disponibles = sorted(df_temp["PO"].dropna().unique())
            pos_seleccionadas = st.multiselect("📄 Orden(es) de Compra (PO)", pos_disponibles, default=pos_disponibles)

            df_temp = df_temp[df_temp["PO"].isin(pos_seleccionadas)] if pos_seleccionadas else df_temp

            # ==== FILTRO 4: Fecha ====
            fechas_disponibles = df_temp["Wanted On"].dropna()
            if not fechas_disponibles.empty:
                min_date = fechas_disponibles.min().date()
                max_date = fechas_disponibles.max().date()

                fechas_seleccionadas = st.date_input(
                    "📆 Rango de fechas (Wanted On)",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )

                if isinstance(fechas_seleccionadas, (tuple, list)) and len(fechas_seleccionadas) == 2:
                    fecha_inicio, fecha_fin = fechas_seleccionadas
                    df_filtrado = df_temp[
                        (df_temp["Wanted On"] >= pd.to_datetime(fecha_inicio)) &
                        (df_temp["Wanted On"] <= pd.to_datetime(fecha_fin))
                    ]
                else:
                    st.warning("⚠️ Selecciona una fecha de inicio y una final.")
                    st.stop()
            else:
                st.warning("⚠️ No hay fechas disponibles.")
                st.stop()

        # ==== APLICAR FILTROS ====
        df_filtrado = df[
            (df["Wanted On"] >= pd.to_datetime(fecha_inicio)) &
            (df["Wanted On"] <= pd.to_datetime(fecha_fin)) &
            (df["Vendor"].isin(proveedores_seleccionados)) &
            (df["PO"].isin(pos_seleccionadas))
        ]

        if type_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Type"].isin(type_seleccionado)]

        if df_filtrado.empty:
            st.warning("⚠️ No hay datos para los filtros seleccionados.")
            return

        # ==== RESÚMENES ====
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🧾 Total de Compras", f"${df_filtrado['Total'].sum():,.2f}")
        with col2:
            st.metric("📦 Total de Piezas", f"{df_filtrado['Quantity'].sum():,.0f}")

        st.markdown("### 📊 Compras por Proveedor")
        resumen_vendor = df_filtrado.groupby("Vendor").agg(
            Total_Compra=("Total", "sum"),
            Piezas=("Quantity", "sum")
        ).reset_index()

        resumen_vendor["Total_Compra"] = resumen_vendor["Total_Compra"].map("${:,.2f}".format)
        resumen_vendor["Piezas"] = resumen_vendor["Piezas"].map("{:,.0f}".format)

        st.dataframe(resumen_vendor)

        # ==== GRÁFICAS ====
        df_viz = df_filtrado.copy()
        df_viz["Wanted On"] = df_viz["Wanted On"].dt.date

        colg1, colg2 = st.columns(2)
        with colg1:
            fig_vendor = px.bar(
                df_viz.groupby("Vendor").agg(Total=("Total", "sum"), Piezas=("Quantity", "sum")).reset_index(),
                x="Vendor", y="Total", text="Piezas",
                title="Total por Proveedor",
                labels={"Total": "Monto ($)", "Piezas": "Piezas"}
            )
            fig_vendor.update_traces(textposition="outside")
            fig_vendor.update_layout(xaxis_tickangle=-45, yaxis_tickformat="$,.0f")
            st.plotly_chart(fig_vendor, use_container_width=True)

        with colg2:
            # Agrupar y asegurar formato correcto de fechas
            resumen_fecha = df_viz.groupby("Wanted On").agg(Total=("Total", "sum"), Piezas=("Quantity", "sum")).reset_index()
            resumen_fecha["Wanted On"] = pd.to_datetime(resumen_fecha["Wanted On"]).dt.date
            resumen_fecha = resumen_fecha.sort_values("Wanted On")  # asegurar orden

            fig_fecha = px.bar(
                resumen_fecha,
                x="Wanted On",
                y="Total",
                text="Piezas",
                title="Compras por Fecha",
                labels={"Wanted On": "Fecha", "Total": "Monto ($)", "Piezas": "Piezas"}
            )

            fig_fecha.update_traces(texttemplate="%{text:.0f} piezas", textposition="outside")
            fig_fecha.update_layout(
                xaxis=dict(type="category", tickangle=-45),
                yaxis_tickformat="$,.0f",
                hovermode="x unified"
            )
            st.plotly_chart(fig_fecha, use_container_width=True)
            
        # ==== DESCARGA ====
        st.markdown("### 📤 Descargar Análisis")
        st.download_button(
            label="⬇️ Descargar en Excel",
            data=exportar_excel(df_filtrado),
            file_name="analisis_forecast_compras.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


        # =========================
        # 📊 TABLA TIPO CALENDARIO
        # =========================
        st.markdown("## 📅 Cantidades por Tipo, Mes y Año")

        # Preparar datos
        df_calendario = df_filtrado.copy()
        df_calendario["Mes"] = df_calendario["Wanted On"].dt.month_name()
        df_calendario["Mes_Num"] = df_calendario["Wanted On"].dt.month
        df_calendario["Año"] = df_calendario["Wanted On"].dt.year

        # Ordenar meses correctamente
        orden_meses_en = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        df_calendario["Mes"] = pd.Categorical(df_calendario["Mes"], categories=orden_meses_en, ordered=True)

        # Filtro de años
        años_disponibles = sorted(df_calendario["Año"].dropna().unique())
        años_seleccionados = st.multiselect("📆 Selecciona año(s) a mostrar:", años_disponibles, default=años_disponibles)
        df_calendario = df_calendario[df_calendario["Año"].isin(años_seleccionados)]

        # Filtro de tipos
        tipos_disponibles = sorted(df_calendario["Type"].dropna().unique())
        tipos_seleccionados = st.multiselect("🏷️ Selecciona Tipo(s):", tipos_disponibles, default=tipos_disponibles)
        df_calendario = df_calendario[df_calendario["Type"].isin(tipos_seleccionados)]

        if df_calendario.empty:
            st.warning("⚠️ No hay datos para los filtros seleccionados.")
            return

        # Agrupar y pivotear
        tabla_pivot = df_calendario.groupby(["Type", "Año", "Mes"]).agg({"Quantity": "sum"}).reset_index()
        tabla_pivot = tabla_pivot.pivot_table(index="Type", columns=["Año", "Mes"], values="Quantity", fill_value=0)

        # Ordenar columnas
        tabla_pivot = tabla_pivot.sort_index(axis=1, level=[0, 1])

        # Calcular fila Total
        fila_total = tabla_pivot.sum(axis=0).to_frame().T
        fila_total.index = ["TOTAL"]

        # Combinar tabla con fila total
        tabla_final = pd.concat([tabla_pivot, fila_total])

        # Mostrar tabla
        st.dataframe(tabla_final.style.format("${:,.2f}"), use_container_width=True)

        # =========================
        # 📈 GRÁFICA DE CANTIDADES POR MES/AÑO/TIPO
        # =========================
        st.markdown("### 📈 Gráfica de Cantidades por Tipo, Mes y Año")

        # Usamos el mismo df_calendario filtrado
        df_grafica = df_calendario.copy()

        # Crear columna MesAño como etiqueta tipo Timestamp (inicio de mes)
        df_grafica["MesAño"] = df_grafica["Wanted On"].dt.to_period("M").dt.to_timestamp()
        df_grafica = df_grafica.sort_values("MesAño")

        # Crear rango completo de meses desde el primer al último mes disponible
        rango_meses = pd.date_range(
            start=df_grafica["MesAño"].min(),
            end=df_grafica["MesAño"].max(),
            freq="MS"  # Month Start
        )

        # Obtener todos los tipos seleccionados
        tipos = df_grafica["Type"].unique()

        # Crear combinaciones de todos los meses con todos los tipos
        index_completo = pd.MultiIndex.from_product([rango_meses, tipos], names=["MesAño", "Type"])

        # Agrupar datos originales
        df_grouped = df_grafica.groupby(["MesAño", "Type"])["Quantity"].sum()

        # Reindexar para asegurar que todos los puntos estén presentes (incluso con 0)
        df_grouped = df_grouped.reindex(index_completo, fill_value=0).reset_index()

        # Crear gráfica
        fig = px.line(
            df_grouped,
            x="MesAño",
            y="Quantity",
            color="Type",
            markers=True,
            title="Evolución Mensual de Compras por Tipo",
            labels={"MesAño": "Mes", "Quantity": "Cantidad", "Type": "Tipo"}
        )

        fig.update_layout(
            hovermode="x unified",
            xaxis=dict(
                tickformat="%b %Y",  # Formato 'Jan 2025'
                tickmode="array",
                tickvals=rango_meses,
                tickangle=-45
            ),
            yaxis_title="Cantidad",
            height=450
        )

        st.plotly_chart(fig, use_container_width=True)

        # Descargar
        st.download_button(
            label="⬇️ Descargar tabla por mes en Excel",
            data=exportar_excel(tabla_final.reset_index()),
            file_name="resumen_tipo_mes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("📥 Por favor, carga un archivo Excel para comenzar el análisis.")

        