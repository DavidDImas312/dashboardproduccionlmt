import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import plotly.express as px


PASSWORD = ")ufIuabDoyH"

def check_password():
    """Función para verificar contraseña."""
    def password_entered():
        if st.session_state["password"] == PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Introduce la contraseña", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Introduce la contraseña", type="password", on_change=password_entered, key="password")
        st.error("Contraseña incorrecta")
        return False
    else:
        return True

if check_password():

    from utils import cargar_reporte_produccion, cargar_programacion, required_columns, required_columns_plan, exportar_varias_hojas_excel, catalogo_downtime

    st.set_page_config(page_title="Análisis de Reportes de Producción", layout="wide")

    if 'df_clean' not in st.session_state:
        st.session_state.df_clean = None
    if 'df_plan' not in st.session_state:
        st.session_state.df_plan = None

    st.title("📊 Dashboard de Producción")

    st.sidebar.title("Navegación")
    option = st.sidebar.radio("Ir a:", ["Inicio", "Dashboard"])

    # Pantalla de Inicio
    if option == "Inicio":
        st.header("📥 Importar Reporte Production Efficiency")
        uploaded_file = st.file_uploader("Selecciona el archivo Excel del reporte", type=["xlsx"])

        if uploaded_file is not None:
            df, error_cols = cargar_reporte_produccion(uploaded_file)
            if df is None:
                st.error("❌ Las columnas no coinciden.")
                st.write("Se esperaban:")
                st.write(required_columns)
                st.write("Se encontraron:")
                st.write(error_cols)
                st.stop()

            st.session_state.df_clean = df
            st.success("✅ Archivo cargado y validado.")
            if st.checkbox("Mostrar datos cargados"):
                st.dataframe(df)

        st.header("📥 Importar Reporte Scheduled Jobs")
        uploaded_plan = st.file_uploader("Selecciona el archivo Excel de la programación", type=["xlsx"], key="plan")

        if uploaded_plan is not None:
            df_plan, error_cols = cargar_programacion(uploaded_plan)
            if df_plan is None:
                st.error("❌ Las columnas del archivo de programación no coinciden.")
                st.write("Se esperaban:")
                st.write(required_columns_plan)
                st.write("Se encontraron:")
                st.write(error_cols)
                st.stop()

            st.session_state.df_plan = df_plan
            st.success("✅ Archivo de programación cargado.")
            if st.checkbox("Mostrar datos de programación"):
                st.dataframe(df_plan)

    # Pantalla de Dashboard
    elif option == "Dashboard":
        # st.header("📊 Dashboard de Producción")

        if st.session_state.df_clean is not None:
            df = st.session_state.df_clean

            # Filtros por Fecha
            fechas = st.sidebar.date_input(
                "Selecciona rango de fechas",
                [df["Completed On"].min(), df["Completed On"].max()]
            )

            df_filtrado = df[
                (df["Completed On"] >= pd.to_datetime(fechas[0])) &
                (df["Completed On"] <= pd.to_datetime(fechas[1]))
            ]

            # Filtro por turno (global para todas las gráficas)
            turnos_disponibles = df_filtrado["Shift"].unique()
            turnos_seleccionados = st.sidebar.multiselect(
                "Selecciona Turno(s)",
                options=turnos_disponibles,
                default=turnos_disponibles
            )

            # Aplicar filtro de turnos
            df_filtrado = df_filtrado[df_filtrado["Shift"].isin(turnos_seleccionados)]

            # Filtro por W/C Type
            wc_types_disponibles = df_filtrado["W/C Type"].unique()
            wc_types_seleccionados = st.sidebar.multiselect(
                "Selecciona Tipo(s) de Centro de Trabajo",
                options=wc_types_disponibles,
                default=wc_types_disponibles
            )

            df_filtrado = df_filtrado[df_filtrado["W/C Type"].isin(wc_types_seleccionados)]
            
            # KPIs resumen
            st.subheader("🔍 Resumen General")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Eficiencia Promedio", f'{df_filtrado["Efficiency"].mean():.2f}%')
            col2.metric("OEE Promedio", f'{df_filtrado["OEE"].mean():.2f}%')
            col4.metric("Horas No-Producción", f'{df_filtrado["Non-production Downtime Hours"].sum():,.2f}')        
            col3.metric("Cantidad Producida", f'{df_filtrado["Quantity"].sum():,.0f}')

            
            # Obtener lista única de W/C disponibles
            wc_options = df_filtrado["W/C"].unique().tolist()
            wc_options = sorted(df_filtrado["W/C"].unique().tolist())

            # Filtro multiselección
            selected_wc = st.multiselect(
                "Selecciona Centro(s) de Trabajo:",
                options=wc_options,
                default=wc_options  # por defecto selecciona todos
            )

            # Filtrar según selección
            df_wc = df_filtrado[df_filtrado["W/C"].isin(selected_wc)]

            # Sección: Top 5 Centros de Trabajo Críticos
            st.subheader("📉 Centros de Trabajo con Indicadores Críticos")

            col_x, col_y, col_z = st.columns(3)

            # Top 5 con menor eficiencia
            with col_x:
                st.markdown("**Menor Eficiencia (Top 5)**")
                top5_low_eff = (
                    df_wc.groupby("W/C")["Efficiency"]
                    .mean()
                    .reset_index()
                    .sort_values(by="Efficiency", ascending=True)
                    .head(5)
                )
                st.dataframe(top5_low_eff, use_container_width=True)

            # Top 5 con más downtime
            with col_y:
                st.markdown("**Más Tiempo de Downtime (Top 5)**")
                top5_downtime = (
                    df_wc.groupby("W/C")["Production Downtime Hours"]
                    .sum()
                    .reset_index()
                    .sort_values(by="Production Downtime Hours", ascending=False)
                    .head(5)
                )
                st.dataframe(top5_downtime, use_container_width=True)

            # Top 5 con más scrap
            with col_z:
                st.markdown("**Más Scrap (Top 5)**")
                top5_scrap = (
                    df_wc.groupby("W/C")["Scrap"]
                    .sum()
                    .reset_index()
                    .sort_values(by="Scrap", ascending=False)
                    .head(5)
                )
                st.dataframe(top5_scrap, use_container_width=True)

            # Gráfica de Eficiencia por Centro de Trabajo con filtro
            st.subheader("⚙️ Eficiencia por Centro de Trabajo")

            # Vista en cuadricula de 3 columnas
            col_a, col_b = st.columns(2)

            # Agrupar y calcular promedio de eficiencia por W/C
            # efficiency_wc = df_wc.groupby("W/C")["Efficiency"].mean().reset_index()

            # Tema profesional para todas las gráficas
            sns.set_theme(
                style="whitegrid", 
                context="talk",  # para dashboards es ideal, usa "notebook" o "paper" para reportes
                palette="colorblind"
            )

            # Ajustes generales de Matplotlib
            plt.rcParams.update({
                "axes.facecolor": "white",
                "axes.edgecolor": "#333333",
                "axes.grid": True,
                "grid.color": "#DDDDDD",
                "grid.linestyle": "--",
                "axes.titleweight": "bold",
                "axes.titlesize": 16,
                "axes.labelsize": 14,
                "xtick.labelsize": 12,
                "ytick.labelsize": 12,
                "legend.fontsize": 12,
                "figure.autolayout": True,  # evita recortes
                "figure.dpi": 120  # resolución adecuada para Streamlit
            })

            # Gráfica 1: Eficiencia por W/C
            with col_a:
                efficiency_wc = (
                    df_wc.groupby("W/C")["Efficiency"]
                    .mean()
                    .reset_index()
                    .sort_values(by="Efficiency", ascending=True)
                )

                # Gráfico interactivo con Plotly Express
                fig = px.bar(
                    efficiency_wc,
                    x="W/C",
                    y="Efficiency",
                    text="Efficiency",
                    color="Efficiency",
                    color_continuous_scale="RdBu",
                    title="Promedio de Eficiencia",
                    labels={
                        "W/C": "Centro de Trabajo (W/C)",
                        "Efficiency": "Eficiencia (%)"
                    },
                    height=500
                )

                # Personalización de texto y layout
                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='inside',
                    insidetextanchor='middle'
                )

                fig.update_layout(
                    yaxis_title="Eficiencia (%)",
                    xaxis_title="Centro de Trabajo (W/C)",
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(showgrid=True, gridcolor='lightgrey', range=[0, 100]),
                    xaxis=dict(showgrid=False),
                    title_font=dict(size=18, color='white', family="Arial"),
                    font=dict(size=12),
                    margin=dict(t=50, l=50, r=30, b=80)
                )

                # Rotar etiquetas del eje X
                fig.update_xaxes(tickangle=35)

                # Mostrar gráfico en Streamlit
                st.plotly_chart(fig, use_container_width=True)

          # Gráfica 2: Partes Producidas por W/C
            with col_b:
                quantity_wc = (
                    df_wc.groupby("W/C")["Quantity"]
                    .sum()
                    .reset_index()
                    .sort_values(by="Quantity", ascending=True)
                )

                # Gráfico interactivo con Plotly Express
                fig = px.bar(
                    quantity_wc,
                    x="Quantity",
                    y="W/C",
                    text="Quantity",
                    color="Quantity",
                    color_continuous_scale="PuRd",
                    title="Producción por W/C",
                    labels={
                        "Quantity": "Partes Producidas",
                        "W/C": "Centro de Trabajo (W/C)"
                    },
                    height=500
                )

                # Personalización de texto y layout
                fig.update_traces(
                    texttemplate='%{text:,}',  # separador de miles
                    textposition='inside',
                    insidetextanchor='middle'
                )

                fig.update_layout(
                    xaxis_title="Partes Producidas",
                    yaxis_title="Centro de Trabajo (W/C)",
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=True, gridcolor='lightgrey'),
                    yaxis=dict(showgrid=False),
                    title_font=dict(size=18, color='white', family="Arial"),
                    font=dict(size=12),
                    margin=dict(t=50, l=50, r=30, b=50)
                )

                # Mostrar gráfico en Streamlit
                st.plotly_chart(fig, use_container_width=True)



            # Segunda fila de gráficas
            col_c, col_d = st.columns(2)

            # Gráfica 3: Downtime por W/C
            with col_c:
                downtime_wc = (
                    df_wc.groupby("W/C")["Production Downtime Hours"]
                    .sum()
                    .reset_index()
                    .sort_values(by="Production Downtime Hours", ascending=False)
                )

                if downtime_wc.empty:
                    st.info("No hay datos de downtime en el rango de fechas y filtros seleccionados.")
                else:
                    # Gráfico con Plotly Express
                    fig = px.bar(
                        downtime_wc,
                        y="W/C",
                        x="Production Downtime Hours",
                        orientation='h',
                        text="Production Downtime Hours",
                        color="Production Downtime Hours",
                        color_continuous_scale="OrRd",
                        labels={
                            "W/C": "Centro de Trabajo (W/C)",
                            "Production Downtime Hours": "Downtime (hrs)"
                        },
                        title="Downtime Total por W/C"
                    )

                    # Personalización de texto y layout
                    fig.update_traces(
                        texttemplate='%{text:.2f}',
                        textposition='inside',
                        insidetextanchor='middle'
                    )

                    fig.update_layout(
                        height=600,
                        xaxis_title="Downtime (hrs)",
                        yaxis_title="Centro de Trabajo (W/C)",
                        coloraxis_showscale=False,
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showgrid=True, gridcolor='lightgrey'),
                        yaxis=dict(showgrid=False),
                        title_font=dict(size=18, color='white', family="Arial"),
                        font=dict(size=12)
                    )

                    st.plotly_chart(fig, use_container_width=True)

            #Gráfica 4: Razones de Downtime
            with col_d:
                if "Production Downtime Reasons" in df_wc.columns:
                    # Agrupar por W/C y Reason ID, sumando Downtime
                    downtime_por_wc = df_wc.groupby(["W/C", "Production Downtime Reasons"])["Production Downtime Hours"].sum().reset_index()

                    # Unir con catálogo para obtener la descripción
                    downtime_por_wc = downtime_por_wc.merge(
                        catalogo_downtime, 
                        left_on="Production Downtime Reasons", 
                        right_on="Reason ID",
                        how="left"
                    )

                    if downtime_por_wc.empty:
                        st.info("No hay datos de downtime en el rango de fechas y filtros seleccionados.")
                    else:
                        # Gráfico interactivo con Plotly Express
                        fig = px.bar(
                            downtime_por_wc,
                            x="Production Downtime Hours",
                            y="W/C",
                            color="Description",
                            text="Production Downtime Hours",
                            orientation="h",
                            title="Downtime por Razón y Centro de Trabajo",
                            labels={
                                "Production Downtime Hours": "Downtime (hrs)",
                                "W/C": "Centro de Trabajo (W/C)",
                                "Description": "Razón de Downtime"
                            },
                            color_continuous_scale="Set2",
                            height=600
                        )

                        # Personalización de texto y layout
                        fig.update_traces(
                            texttemplate='%{text:.2f}',
                            textposition='inside',
                            insidetextanchor='middle'
                        )

                        fig.update_layout(
                            barmode="group",  # si quieres que se apilen, o 'group' para separadas
                            xaxis_title="Downtime (hrs)",
                            yaxis_title="Centro de Trabajo (W/C)",
                            plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=True, gridcolor='lightgrey'),
                            yaxis=dict(showgrid=False),
                            title_font=dict(size=18, color='white', family="Arial"),
                            font=dict(size=12),
                            legend_title_text="Razón de Downtime"
                        )

                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("La columna 'Production Downtime Reasons' no está presente en el reporte de eficiencia cargado.")

            # Tercer fila de gráficas
            col_e, col_f = st.columns(2)

            # Gráfica 5: Eficiencia promedio por Empleado
            with col_e:
                eficiencia_empleado = (
                    df_wc.groupby("Employee")["Efficiency"]
                    .mean()
                    .reset_index()
                    .sort_values(by="Efficiency", ascending=False)
                )

                # Gráfico interactivo con Plotly Express
                fig = px.bar(
                    eficiencia_empleado,
                    x="Efficiency",
                    y="Employee",
                    text=eficiencia_empleado["Efficiency"].round(1).astype(str) + '%',
                    color="Efficiency",
                    color_continuous_scale="RdPu",
                    title="Eficiencia Promedio por Empleado",
                    labels={
                        "Efficiency": "Eficiencia (%)",
                        "Employee": "Empleado"
                    },
                    height=600
                )

                # Personalización de layout y etiquetas
                fig.update_traces(
                    textposition='inside',
                    insidetextanchor='middle'
                )

                fig.update_layout(
                    xaxis_title="Eficiencia (%)",
                    yaxis_title="Empleado",
                    xaxis=dict(range=[0, 100], showgrid=True, gridcolor='lightgrey'),
                    yaxis=dict(showgrid=False),
                    plot_bgcolor='rgba(0,0,0,0)',
                    title_font=dict(size=18, color='white', family="Arial"),
                    font=dict(size=12),
                    margin=dict(t=50, l=50, r=30, b=50)
                )

                # Mostrar gráfico en Streamlit
                st.plotly_chart(fig, use_container_width=True)


            # Gráfica 6: Cantidad de Empleados por Turno
            with col_f:
                empleados_turno = (
                    df_wc.groupby("Shift")["Employee"]
                    .nunique()
                    .reset_index()
                    .sort_values(by="Employee", ascending=True)
                )

                # Gráfico interactivo con Plotly Express
                fig = px.bar(
                    empleados_turno,
                    x="Shift",
                    y="Employee",
                    text=empleados_turno["Employee"].astype(str),
                    color="Employee",
                    color_continuous_scale="Agsunset",
                    title="Empleados por Turno",
                    labels={
                        "Shift": "Turno",
                        "Employee": "Empleados únicos"
                    },
                    height=500
                )

                # Personalización de layout y etiquetas
                fig.update_traces(
                    textposition='inside',
                    insidetextanchor='middle'
                )

                fig.update_layout(
                    xaxis_title="Turno",
                    yaxis_title="Empleados únicos",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='lightgrey'),
                    plot_bgcolor='rgba(0,0,0,0)',
                    title_font=dict(size=18, color='white', family="Arial"),
                    font=dict(size=12),
                    margin=dict(t=50, l=50, r=30, b=50)
                )

                # Mostrar gráfico en Streamlit
                st.plotly_chart(fig, use_container_width=True)

            col_g, col_h = st.columns(2)

            # Gráfica 7: horas por W/C
            with col_g:
                horas_wc = (
                    df_wc.groupby("W/C")["Hours"]
                    .sum()
                    .reset_index()
                    .sort_values(by="Hours", ascending=False)
                )

                max_value = horas_wc["Hours"].max()

                # Definir posición de los textos
                horas_wc["TextPosition"] = horas_wc["Hours"].apply(
                    lambda x: 'inside' if x > max_value * 0.15 else 'outside'
                )

                # Gráfico interactivo con Plotly Express
                fig = px.bar(
                    horas_wc,
                    y="W/C",
                    x="Hours",
                    text=horas_wc["Hours"].round(2).astype(str),
                    color="Hours",
                    color_continuous_scale="Peach",
                    title="Total de Horas por W/C",
                    labels={
                        "Hours": "Total de Horas",
                        "W/C": "Centro de Trabajo (W/C)"
                    },
                    height=500
                )

                # Personalización de layout y etiquetas
                fig.update_traces(
                    textposition=horas_wc["TextPosition"],
                    insidetextanchor='middle'
                )

                fig.update_layout(
                    xaxis_title="Total de Horas",
                    yaxis_title="Centro de Trabajo (W/C)",
                    xaxis=dict(showgrid=True, gridcolor='lightgrey'),
                    yaxis=dict(showgrid=False),
                    plot_bgcolor='rgba(0,0,0,0)',
                    title_font=dict(size=18, color='white', family="Arial"),
                    font=dict(size=12),
                    margin=dict(t=50, l=50, r=30, b=50)
                )

                # Mostrar gráfico en Streamlit
                st.plotly_chart(fig, use_container_width=True)

            # Gráfica 8: Cantidad de Scrap por W/C
            with col_h:
                scrap_wc = (
                    df_wc.groupby("W/C")["Scrap"]
                    .sum()
                    .reset_index()
                    .sort_values(by="Scrap", ascending=False)
                )

                max_value = scrap_wc["Scrap"].max()

                # Definir posición de las etiquetas según tamaño
                scrap_wc["TextPosition"] = scrap_wc["Scrap"].apply(
                    lambda x: 'inside' if x > max_value * 0.15 else 'outside'
                )

                # Crear gráfico con Plotly Express
                fig = px.bar(
                    scrap_wc,
                    y="W/C",
                    x="Scrap",
                    text=scrap_wc["Scrap"].astype(int).astype(str),
                    color="Scrap",
                    color_continuous_scale="Inferno",
                    title="Scrap por W/C",
                    labels={
                        "Scrap": "Scrap (Pzas)",
                        "W/C": "Centro de Trabajo (W/C)"
                    },
                    height=500
                )

                # Personalizar etiquetas y layout
                fig.update_traces(
                    textposition=scrap_wc["TextPosition"],
                    insidetextanchor='middle'
                )

                fig.update_layout(
                    xaxis_title="Scrap (Pzas)",
                    yaxis_title="Centro de Trabajo (W/C)",
                    xaxis=dict(showgrid=True, gridcolor='lightgrey'),
                    yaxis=dict(showgrid=False),
                    plot_bgcolor='rgba(0,0,0,0)',
                    title_font=dict(size=18, color='white', family="Arial"),
                    font=dict(size=12),
                    margin=dict(t=50, l=50, r=30, b=50)
                )

                # Mostrar gráfico en Streamlit
                st.plotly_chart(fig, use_container_width=True)


            # Cuarta fila de gráficas
            col_i, col_j  = st.columns(2)

            # Gráfica 9: OEE promedio por W/C
            with col_i:
                oee_wc = (
                    df_wc.groupby("W/C")["OEE"]
                    .mean()
                    .reset_index()
                    .sort_values(by="OEE", ascending=False)
                )

                max_value = oee_wc["OEE"].max()

                # Definir posición de las etiquetas según tamaño
                oee_wc["TextPosition"] = oee_wc["OEE"].apply(
                    lambda x: 'inside' if x > max_value * 0.15 else 'outside'
                )

                # Crear gráfico con Plotly Express
                fig = px.bar(
                    oee_wc,
                    y="W/C",
                    x="OEE",
                    text=oee_wc["OEE"].apply(lambda x: f'{x:.2f}%'),
                    color="OEE",
                    color_continuous_scale="Magma",
                    title="OEE Promedio por W/C",
                    labels={
                        "OEE": "OEE Promedio (%)",
                        "W/C": "Centro de Trabajo (W/C)"
                    },
                    height=500
                )

                # Personalizar etiquetas y layout
                fig.update_traces(
                    textposition=oee_wc["TextPosition"],
                    insidetextanchor='middle'
                )

                fig.update_layout(
                    xaxis_title="OEE Promedio (%)",
                    yaxis_title="Centro de Trabajo (W/C)",
                    xaxis=dict(showgrid=True, gridcolor='lightgrey', range=[0, 100]),
                    yaxis=dict(showgrid=False),
                    plot_bgcolor='rgba(0,0,0,0)',
                    title_font=dict(size=18, color='white', family="Arial"),
                    font=dict(size=12),
                    margin=dict(t=50, l=50, r=30, b=50)
                )

                # Mostrar gráfico en Streamlit
                st.plotly_chart(fig, use_container_width=True)

            # Gráfica 10: Expected vs Actual Run Rate /hr por W/C
            with col_j:
                # Filtrar df_wc por turno si se seleccionó alguno
                df_wc_filtrado = df_wc.copy()

                if turnos_seleccionados:
                    df_wc_filtrado = df_wc_filtrado[df_wc_filtrado["Shift"].isin(turnos_seleccionados)]

                # Asegurarnos que son numéricos
                df_wc_filtrado["Expected Run Rate /hr"] = pd.to_numeric(df_wc_filtrado["Expected Run Rate /hr"], errors="coerce")
                df_wc_filtrado["Actual Run Rate /hr"] = pd.to_numeric(df_wc_filtrado["Actual Run Rate /hr"], errors="coerce")

                # Agrupar por W/C y calcular promedios
                runrate_wc = df_wc_filtrado.groupby("W/C")[["Expected Run Rate /hr", "Actual Run Rate /hr"]].mean().reset_index()
                runrate_wc = runrate_wc.sort_values(by="Expected Run Rate /hr", ascending=False)

                runrate_wc.dropna(subset=["Expected Run Rate /hr", "Actual Run Rate /hr"], inplace=True)

                # Transformar a formato largo
                runrate_wc_melted = runrate_wc.melt(
                    id_vars="W/C",
                    value_vars=["Expected Run Rate /hr", "Actual Run Rate /hr"],
                    var_name="Tipo",
                    value_name="Run Rate"
                )

                max_value = runrate_wc_melted["Run Rate"].max()

                # Posiciones dinámicas de etiquetas
                runrate_wc_melted["TextPosition"] = runrate_wc_melted["Run Rate"].apply(
                    lambda x: 'inside' if x > max_value * 0.15 else 'outside'
                )

                # Gráfica con Plotly
                fig = px.bar(
                    runrate_wc_melted,
                    y="W/C",
                    x="Run Rate",
                    color="Tipo",
                    text=runrate_wc_melted["Run Rate"].apply(lambda x: f'{x:.2f}'),
                    barmode="group",
                    color_discrete_map={
                        "Expected Run Rate /hr": "#1f77b4",
                        "Actual Run Rate /hr": "#ff7f0e"
                    },
                    labels={
                        "Run Rate": "Run Rate (unidades/hr)",
                        "W/C": "Centro de Trabajo (W/C)"
                    },
                    title="Expected vs Actual Run Rate por W/C",
                    height=550
                )

                # Personalizar etiquetas y estilo
                fig.update_traces(
                    textposition=runrate_wc_melted["TextPosition"],
                    insidetextanchor='middle'
                )

                fig.update_layout(
                    xaxis_title="Run Rate (unidades/hr)",
                    yaxis_title="Centro de Trabajo (W/C)",
                    xaxis=dict(showgrid=True, gridcolor='lightgrey'),
                    yaxis=dict(showgrid=False),
                    plot_bgcolor='rgba(0,0,0,0)',
                    title_font=dict(size=18, color='white', family="Arial"),
                    font=dict(size=12),
                    margin=dict(t=50, l=50, r=30, b=50),
                    legend_title_text=""
                )

                st.plotly_chart(fig, use_container_width=True)


            #Siguiente fila
            col_k, col_l = st.columns(2)

            #Gráfica 12: WorkOrderd por turno
            with col_k:
                # Agrupar por turno y contar WO únicos
                wo_por_turno = (
                    df_wc.groupby("Shift")["Job #"]
                    .nunique()
                    .reset_index()
                    .sort_values(by="Job #", ascending=True)
                )

                max_value = wo_por_turno["Job #"].max()

                # Posiciones dinámicas de etiquetas
                wo_por_turno["TextPosition"] = wo_por_turno["Job #"].apply(
                    lambda x: 'inside' if x > max_value * 0.15 else 'outside'
                )

                # Gráfica con Plotly
                fig = px.bar(
                    wo_por_turno,
                    x="Shift",
                    y="Job #",
                    text=wo_por_turno["Job #"].apply(lambda x: f'{x:.0f}'),
                    color="Job #",
                    color_continuous_scale="Magenta",
                    labels={"Job #": "Cantidad de Work Orders", "Shift": "Turno"},
                    title="Work Orders por Turno",
                    height=400
                )

                # Personalizar etiquetas y estilo
                fig.update_traces(
                    textposition=wo_por_turno["TextPosition"],
                    insidetextanchor='middle'
                )

                fig.update_layout(
                    xaxis_title="Turno",
                    yaxis_title="Cantidad de Work Orders",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='lightgrey'),
                    plot_bgcolor='rgba(0,0,0,0)',
                    title_font=dict(size=18, color='White', family="Arial"),
                    font=dict(size=12),
                    margin=dict(t=50, l=50, r=30, b=50),
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)

            with col_l: 
                if not df_wc.empty:
                    diccionario_dfs = {
                        "Downtime por W_C": downtime_wc,
                        "Eficiencia por Empleado": eficiencia_empleado,
                        "WorkOrders por Turno": wo_por_turno,
                        "Horas por W_C": horas_wc,
                        "Scrap por W_C": scrap_wc,
                        "OEE por W_C": oee_wc,
                        "RunRate por W_C": runrate_wc
                    }

                exportar_varias_hojas_excel(diccionario_dfs)

            # Gráfica 11: Cumplimiento al Plan de Producción (solo este bloque usa su propio filtro)
            st.subheader("📈 Cumplimiento al Plan de Producción por W/C")

            if st.session_state.df_plan is not None:
                df_plan = st.session_state.df_plan

                wc_types_local = df_filtrado["W/C Type"].unique().tolist()

                with st.container():
                    col_reset, col_filters = st.columns([1, 5])

                    with col_filters:
                        selected_wc_type_local = st.selectbox(
                            "Selecciona W/C Type para Cumplimiento al Plan:",
                            options=wc_types_local,
                            key="wc_type_local"
                        )

                        df_plan_filtrado = df_plan[df_plan["W/C Type"] == selected_wc_type_local]

                        wc_local = df_plan_filtrado["W/C"].unique().tolist()

                        selected_wc_local = st.multiselect(
                            "Selecciona W/C (puedes elegir varios o dejar vacío para todos):",
                            options=wc_local,
                            key="wc_local"
                        )

                if selected_wc_local:
                    df_plan_filtrado = df_plan_filtrado[df_plan_filtrado["W/C"].isin(selected_wc_local)]

                cumplimiento_plan = df_plan_filtrado.groupby("W/C")[["To Make", "Produced"]].sum().reset_index()

                cumplimiento_plan["Cumplimiento (%)"] = (
                    (cumplimiento_plan["Produced"] / cumplimiento_plan["To Make"]) * 100
                ).round(2)
                cumplimiento_plan["Cumplimiento (%)"].fillna(0, inplace=True)

                cumplimiento_plan = cumplimiento_plan.sort_values(by="Cumplimiento (%)", ascending=True)

                # Gráfica con Plotly
                fig = px.bar(
                    cumplimiento_plan,
                    x="W/C",
                    y="Cumplimiento (%)",
                    text=cumplimiento_plan["Cumplimiento (%)"].apply(lambda x: f'{x:.1f}%'),
                    color="Cumplimiento (%)",
                    color_continuous_scale="teal",
                    title=f'Cumplimiento al Plan ({selected_wc_type_local})',
                    labels={"Cumplimiento (%)": "Cumplimiento (%)", "W/C": "Centro de Trabajo"},
                    height=450
                )

                fig.update_traces(
                    textposition='outside'
                )

                fig.update_layout(
                    yaxis=dict(range=[0, 120], showgrid=True, gridcolor='lightgrey'),
                    xaxis=dict(showgrid=False),
                    plot_bgcolor='rgba(0,0,0,0)',
                    title_font=dict(size=18),
                    font=dict(size=12),
                    margin=dict(t=50, l=50, r=30, b=50),
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)

                # Mostrar tablas
                st.subheader("📄 Datos Filtrados para Cumplimiento al Plan")
                st.dataframe(df_plan_filtrado[["W/C Type", "W/C", "Job #", "Item", "To Make", "Produced"]])

                st.subheader("📊 Cumplimiento Agrupado por W/C")
                st.dataframe(cumplimiento_plan)
            else:
                st.info("Carga primero el archivo de Scheduled Jobs para mostrar esta gráfica.")

        else:
            st.warning("No hay datos para los W/C seleccionados en este rango.")
