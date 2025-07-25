import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import cargar_datos_columnas_requeridas, convertir_columnas_fecha


def ventas_app():
    menuventas = ["Importar Reportes", "Comparativa"]
    option = st.sidebar.selectbox("Acciones:", menuventas)

    if option == "Importar Reportes":
        importar_ventas()

    elif option == "Comparativa":
        comparativa_grafica()

def importar_ventas():
    st.subheader("📥 Cargar Archivos")

    columnas_orders = ["Ship On", "Customer", "Item", "Amount"]
    columnas_sales = ["Invoice Date", "Customer", "Item", "Amount"]

    uploaded_orders = st.file_uploader("📄 Archivo de Orders", type=["xlsx"], key="orders")
    uploaded_sales = st.file_uploader("📄 Archivo de Ventas", type=["xlsx"], key="sales")

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

    # 📌 Validar que se hayan cargado previamente los archivos
    if "df_orders" not in st.session_state or "df_sales" not in st.session_state:
        st.warning("⚠️ Primero carga ambos archivos en la pestaña 'Importar Reportes'.")
        st.stop()

    # 📌 Obtener los dataframes de sesión
    df_orders = st.session_state.df_orders.copy()
    df_sales = st.session_state.df_sales.copy()

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