import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from utils import cargar_reporte_produccion, cargar_programacion, required_columns, required_columns_plan, exportar_varias_hojas_excel

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
        col1, col2, col3 = st.columns(3)
        col1.metric("Horas trabajadas", f'{df_filtrado["Hours"].sum():,.2f}')
        col2.metric("OEE Promedio", f'{df_filtrado["OEE"].mean():.2f}%')
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
                df_wc.groupby("W/C")["Downtime"]
                .sum()
                .reset_index()
                .sort_values(by="Downtime", ascending=False)
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

            fig, ax = plt.subplots(figsize=(8, 5))

            sns.barplot(
                data=efficiency_wc,
                x="W/C",
                y="Efficiency",
                ax=ax,
                palette="coolwarm"
            )

            ax.set_xlabel("Centro de Trabajo (W/C)", fontsize=13)
            ax.set_ylabel("Eficiencia (%)", fontsize=13)
            ax.set_title("Promedio de Eficiencia", fontsize=15, weight='bold')
            ax.set_ylim(0, 100)
            ax.grid(axis="y", linestyle="--", alpha=0.6)
            ax.set_axisbelow(True)

            max_value = 100

            # Etiquetas sobre o fuera de las barras
            for bar in ax.patches:
                height = bar.get_height()

                if height > max_value * 0.15:
                    # Si la barra es suficientemente alta: etiqueta dentro, color blanco
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height - (height * 0.05),
                        f'{height:.1f}%',
                        ha='center',
                        va='center',
                        fontsize=11,
                        color='white',
                        fontweight='bold'
                    )
                else:
                    # Si la barra es pequeña: etiqueta arriba, color negro
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height + 1,  # un poco arriba de la barra
                        f'{height:.1f}%',
                        ha='center',
                        va='bottom',
                        fontsize=11,
                        color='black',
                        fontweight='bold'
                    )

            plt.xticks(rotation=35, ha='right', fontsize=11)
            plt.yticks(fontsize=11)

            plt.tight_layout()  # <-- Ajusta todo para evitar que se empalmen

            st.pyplot(fig)

        # Gráfica 2: Partes Producidas por W/C
        with col_b:
            quantity_wc = (
                df_wc.groupby("W/C")["Quantity"]
                .sum()
                .reset_index()
                .sort_values(by="Quantity", ascending=True)
            )

            fig, ax = plt.subplots(figsize=(7, 5))

            bars = sns.barplot(
                data=quantity_wc,
                y="W/C",
                x="Quantity",
                ax=ax,
                palette="crest"
            )

            max_value = quantity_wc["Quantity"].max()

            # Etiquetas dentro de las barras
            max_value = quantity_wc["Quantity"].max()

            for p in bars.patches:
                width = p.get_width()

                if width > max_value * 0.15:
                    # Si la barra es suficientemente grande: etiqueta dentro, color blanco
                    ax.text(
                        width - (width * 0.02),
                        p.get_y() + p.get_height() / 2,
                        f'{int(width):,}',
                        ha='right', va='center',
                        fontsize=10,
                        color='white',
                        fontweight='bold'
                    )
                else:
                    # Si la barra es pequeña: etiqueta afuera, color negro
                    ax.text(
                        width + (max_value * 0.01),
                        p.get_y() + p.get_height() / 2,
                        f'{int(width):,}',
                        ha='left', va='center',
                        fontsize=10,
                        color='black',
                        fontweight='bold'
                    )

            ax.set_xlabel("Partes Producidas")
            ax.set_ylabel("Centro de Trabajo (W/C)")
            ax.set_title("Producción por W/C")
            ax.grid(axis='x', linestyle='--', alpha=0.6)
            ax.set_axisbelow(True)

            st.pyplot(fig)


        # Segunda fila de gráficas
        col_c, col_d = st.columns(2)

        # Gráfica 3: Empleados por Turno
        with col_c:
            empleados_turno = (
                df_wc.groupby("Shift")["Employee"]
                .nunique()
                .reset_index()
                .sort_values(by="Employee", ascending=True)
            )

            fig, ax = plt.subplots(figsize=(6, 4))

            sns.barplot(
                data=empleados_turno,
                x="Shift",
                y="Employee",
                ax=ax,
                palette="flare"
            )

            max_value = empleados_turno["Employee"].max()

            # Etiquetas sobre o fuera de las barras
            for bar in ax.patches:
                height = bar.get_height()

                if height > max_value * 0.15:
                    # Si la barra es suficientemente alta: etiqueta dentro, color blanco
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height - (height * 0.1),
                        f'{int(height)}',
                        ha='center',
                        va='center',
                        fontsize=11,
                        color='white',
                        fontweight='bold'
                    )
                else:
                    # Si la barra es pequeña: etiqueta arriba, color negro
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height + 0.3,
                        f'{int(height)}',
                        ha='center',
                        va='bottom',
                        fontsize=11,
                        color='#333333',
                        fontweight='bold'
                    )

            ax.set_xlabel("Turno", fontsize=13)
            ax.set_ylabel("Empleados únicos", fontsize=13)
            ax.set_title("Empleados por Turno", fontsize=15, weight='bold')
            ax.grid(axis='y', linestyle='--', alpha=0.6)
            ax.set_axisbelow(True)

            plt.xticks(fontsize=11)
            plt.yticks(fontsize=11)

            plt.tight_layout()

            st.pyplot(fig)

        # Gráfica 4: Downtime por W/C
        with col_d:
            downtime_wc = (
                df_wc.groupby("W/C")["Downtime"]
                .sum()
                .reset_index()
                .sort_values(by="Downtime", ascending=False)
            )

            fig, ax = plt.subplots(figsize=(6, 4))

            sns.barplot(
                data=downtime_wc,
                y="W/C",
                x="Downtime",
                ax=ax,
                palette="rocket"
            )

            max_value = downtime_wc["Downtime"].max()

            # Etiquetas sobre o fuera de las barras
            for bar in ax.patches:
                width = bar.get_width()

                if width > max_value * 0.15:
                    # Si la barra es suficientemente larga: etiqueta dentro
                    ax.text(
                        width - (width * 0.02),
                        bar.get_y() + bar.get_height() / 2,
                        f'{width:.2f}',
                        ha='right',
                        va='center',
                        fontsize=11,
                        color='white',
                        fontweight='bold'
                    )
                else:
                    # Si la barra es corta: etiqueta afuera
                    ax.text(
                        width + 0.1,
                        bar.get_y() + bar.get_height() / 2,
                        f'{width:.2f}',
                        ha='left',
                        va='center',
                        fontsize=11,
                        color='#333333',
                        fontweight='bold'
                    )

            ax.set_xlabel("Downtime (hrs)", fontsize=13)
            ax.set_ylabel("Centro de Trabajo (W/C)", fontsize=13)
            ax.set_title("Downtime Total por W/C", fontsize=15, weight='bold')
            ax.grid(axis='x', linestyle='--', alpha=0.6)
            ax.set_axisbelow(True)

            plt.xticks(fontsize=11)
            plt.yticks(fontsize=11)

            plt.tight_layout()

            st.pyplot(fig)

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

            fig, ax = plt.subplots(figsize=(6, 4))

            sns.barplot(
                data=eficiencia_empleado,
                y="Employee",
                x="Efficiency",
                ax=ax,
                palette="rocket"
            )

            max_value = 100  # Porque la escala ya está limitada a 100%

            # Etiquetas sobre o fuera de las barras
            for bar in ax.patches:
                width = bar.get_width()

                if width > max_value * 0.15:
                    # Si la barra es suficientemente larga: etiqueta dentro
                    ax.text(
                        width - (width * 0.02),
                        bar.get_y() + bar.get_height() / 2,
                        f'{width:.1f}%',
                        ha='right',
                        va='center',
                        fontsize=11,
                        color='white',
                        fontweight='bold'
                    )
                else:
                    # Si la barra es corta: etiqueta afuera
                    ax.text(
                        width + 0.5,
                        bar.get_y() + bar.get_height() / 2,
                        f'{width:.1f}%',
                        ha='left',
                        va='center',
                        fontsize=11,
                        color='#333333',
                        fontweight='bold'
                    )

            ax.set_xlabel("Eficiencia (%)", fontsize=13)
            ax.set_ylabel("Empleado", fontsize=13)
            ax.set_title("Eficiencia Promedio por Empleado", fontsize=15, weight='bold')
            ax.set_xlim(0, 100)
            ax.grid(axis='x', linestyle='--', alpha=0.6)
            ax.set_axisbelow(True)

            plt.xticks(fontsize=11)
            plt.yticks(fontsize=11)

            plt.tight_layout()

            st.pyplot(fig)

        # Gráfica 6: Cantidad de Work Orders por Turno
        with col_f:
            wo_por_turno = (
                df_wc.groupby("Shift")["Job #"]
                .nunique()
                .reset_index()
                .sort_values(by="Job #", ascending=True)
            )

            fig, ax = plt.subplots(figsize=(5, 3.5))

            sns.barplot(
                data=wo_por_turno,
                x="Shift",
                y="Job #",
                ax=ax,
                palette="pastel"
            )

            max_value = wo_por_turno["Job #"].max()

            # Etiquetas sobre o fuera de las barras
            for bar in ax.patches:
                height = bar.get_height()

                if height > max_value * 0.15:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height - (height * 0.5),
                        f'{height:.0f}',
                        ha='center',
                        va='bottom',
                        fontsize=11,
                        color='white',
                        fontweight='bold'
                    )
                else:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height + 0.3,
                        f'{height:.0f}',
                        ha='center',
                        va='bottom',
                        fontsize=11,
                        color='#333333',
                        fontweight='bold'
                    )

            ax.set_xlabel("Turno", fontsize=13)
            ax.set_ylabel("Cantidad de Work Orders", fontsize=13)
            ax.set_title("Work Orders por Turno", fontsize=15, weight='bold')
            ax.grid(axis='y', linestyle='--', alpha=0.6)
            ax.set_axisbelow(True)

            plt.xticks(fontsize=11)
            plt.yticks(fontsize=11)

            plt.tight_layout()

            st.pyplot(fig)

        col_g, col_h = st.columns(2)

        with col_g:
            horas_wc = (
                df_wc.groupby("W/C")["Hours"]
                .sum()
                .reset_index()
                .sort_values(by="Hours", ascending=False)
            )

            fig, ax = plt.subplots(figsize=(6, 4))

            sns.barplot(
                data=horas_wc,
                y="W/C",
                x="Hours",
                ax=ax,
                palette="crest"
            )

            max_value = horas_wc["Hours"].max()

            # Etiquetas sobre o fuera de las barras
            for bar in ax.patches:
                width = bar.get_width()

                if width > max_value * 0.15:
                    ax.text(
                        width - (width * 0.01),
                        bar.get_y() + bar.get_height() / 2,
                        f'{width:.2f}',
                        va='center',
                        ha='right',
                        fontsize=11,
                        color='white',
                        fontweight='bold'
                    )
                else:
                    ax.text(
                        width + 0.1,
                        bar.get_y() + bar.get_height() / 2,
                        f'{width:.2f}',
                        va='center',
                        ha='left',
                        fontsize=11,
                        color='#333333',
                        fontweight='bold'
                    )

            ax.set_xlabel("Total de Horas", fontsize=13)
            ax.set_ylabel("Centro de Trabajo (W/C)", fontsize=13)
            ax.set_title("Total de Horas por W/C", fontsize=15, weight='bold')
            ax.grid(axis='x', linestyle='--', alpha=0.6)
            ax.set_axisbelow(True)

            plt.xticks(fontsize=11)
            plt.yticks(fontsize=11)

            plt.tight_layout()

            st.pyplot(fig)

        # Gráfica 8: Cantidad de Scrap por W/C
        with col_h:
            scrap_wc = (
                df_wc.groupby("W/C")["Scrap"]
                .sum()
                .reset_index()
                .sort_values(by="Scrap", ascending=False)
            )

            fig, ax = plt.subplots(figsize=(6, 4))

            sns.barplot(
                data=scrap_wc,
                y="W/C",
                x="Scrap",
                ax=ax,
                palette="rocket"
            )

            max_value = scrap_wc["Scrap"].max()

            # Etiquetas sobre o fuera de las barras
            for bar in ax.patches:
                width = bar.get_width()

                if width > max_value * 0.15:
                    ax.text(
                        width - (width * 0.01),
                        bar.get_y() + bar.get_height() / 2,
                        f'{width:.0f}',
                        va='center',
                        ha='right',
                        fontsize=11,
                        color='white',
                        fontweight='bold'
                    )
                else:
                    ax.text(
                        width + 0.1,
                        bar.get_y() + bar.get_height() / 2,
                        f'{width:.0f}',
                        va='center',
                        ha='left',
                        fontsize=11,
                        color='#333333',
                        fontweight='bold'
                    )

            ax.set_xlabel("Scrap (Pzas)", fontsize=13)
            ax.set_ylabel("Centro de Trabajo (W/C)", fontsize=13)
            ax.set_title("Scrap por W/C", fontsize=15, weight='bold')
            ax.grid(axis='x', linestyle='--', alpha=0.6)
            ax.set_axisbelow(True)

            plt.xticks(fontsize=11)
            plt.yticks(fontsize=11)

            plt.tight_layout()

            st.pyplot(fig)

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

            fig, ax = plt.subplots(figsize=(6, 4))

            sns.barplot(
                data=oee_wc,
                x="OEE",
                y="W/C",
                ax=ax,
                palette="mako"
            )

            max_value = oee_wc["OEE"].max()

            # Etiquetas sobre o fuera de las barras
            for bar in ax.patches:
                width = bar.get_width()

                if width > max_value * 0.15:
                    ax.text(
                        width - (width * 0.01),
                        bar.get_y() + bar.get_height() / 2,
                        f'{width:.2f}%',
                        va='center',
                        ha='right',
                        fontsize=11,
                        color='white',
                        fontweight='bold'
                    )
                else:
                    ax.text(
                        width + 0.3,
                        bar.get_y() + bar.get_height() / 2,
                        f'{width:.2f}%',
                        va='center',
                        ha='left',
                        fontsize=11,
                        color='#333333',
                        fontweight='bold'
                    )

            ax.set_xlabel("OEE Promedio (%)", fontsize=13)
            ax.set_ylabel("Centro de Trabajo (W/C)", fontsize=13)
            ax.set_title("OEE Promedio por W/C", fontsize=15, weight='bold')
            ax.set_xlim(0, 100)
            ax.grid(axis='x', linestyle='--', alpha=0.6)
            ax.set_axisbelow(True)

            plt.xticks(fontsize=11)
            plt.yticks(fontsize=11)

            plt.tight_layout()

            st.pyplot(fig)

        # Gráfica 10: Expected vs Actual Run Rate /hr por W/C
        with col_j:
            # Filtrar df_wc por turno si se seleccionó al menos uno
            df_wc_filtrado = df_wc.copy()

            if turnos_seleccionados:
                df_wc_filtrado = df_wc_filtrado[df_wc_filtrado["Shift"].isin(turnos_seleccionados)]

            df_wc_filtrado["Expected Run Rate /hr"] = pd.to_numeric(df_wc_filtrado["Expected Run Rate /hr"], errors="coerce")
            df_wc_filtrado["Actual Run Rate /hr"] = pd.to_numeric(df_wc_filtrado["Actual Run Rate /hr"], errors="coerce")

            # Agrupar por W/C
            runrate_wc = df_wc_filtrado.groupby("W/C")[["Expected Run Rate /hr", "Actual Run Rate /hr"]].mean().reset_index()
            runrate_wc = runrate_wc.sort_values(by="Expected Run Rate /hr", ascending=False)

            # Eliminar NaN para evitar shape mismatch
            runrate_wc.dropna(subset=["Expected Run Rate /hr", "Actual Run Rate /hr"], inplace=True)

            # Transformar a formato largo para seaborn
            runrate_wc_melted = runrate_wc.melt(
                id_vars="W/C", 
                value_vars=["Expected Run Rate /hr", "Actual Run Rate /hr"],
                var_name="Tipo", 
                value_name="Run Rate"
            )

            # Gráfica
            fig, ax = plt.subplots(figsize=(7, 5))

            custom_palette = {
                "Expected Run Rate /hr": "#1f77b4",
                "Actual Run Rate /hr": "#ff7f0e"
            }

            sns.barplot(
                data=runrate_wc_melted,
                y="W/C",
                x="Run Rate",
                hue="Tipo",
                palette=custom_palette,
                ax=ax
            )

            max_value = runrate_wc_melted["Run Rate"].max()

            # Etiquetas de valor
            for p in ax.patches:
                width = p.get_width()
                if not pd.isna(width):
                    if width > max_value * 0.15:
                        ax.text(
                            width - (width * 0.01),
                            p.get_y() + p.get_height() / 2,
                            f'{width:.2f}',
                            va='center',
                            ha='right',
                            fontsize=10,
                            color='white',
                            fontweight='bold'
                        )
                    else:
                        ax.text(
                            width + 0.3,
                            p.get_y() + p.get_height() / 2,
                            f'{width:.2f}',
                            va='center',
                            ha='left',
                            fontsize=10,
                            color='#333333',
                            fontweight='bold'
                        )

            # Detalles de estilo
            ax.set_xlabel("Run Rate (unidades/hr)", fontsize=13)
            ax.set_ylabel("Centro de Trabajo (W/C)", fontsize=13)
            ax.set_title("Expected vs Actual Run Rate por W/C", fontsize=15, weight='bold')
            ax.grid(axis='x', linestyle='--', alpha=0.6)
            ax.set_axisbelow(True)
            ax.legend(title="", loc="lower right")

            plt.xticks(fontsize=11)
            plt.yticks(fontsize=11)

            plt.tight_layout()

            st.pyplot(fig)

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

            # Obtener W/C Type únicos
            wc_types_local = df_filtrado["W/C Type"].unique().tolist()

            # Crear contenedor para filtros y botón de reset
            with st.container():
                col_reset, col_filters = st.columns([1, 5])

                with col_filters:
                    selected_wc_type_local = st.selectbox(
                        "Selecciona W/C Type para Cumplimiento al Plan:",
                        options=wc_types_local,
                        key="wc_type_local"
                    )

                    # Filtrar datos según W/C Type seleccionado
                    df_plan_filtrado = df_plan[df_plan["W/C Type"] == selected_wc_type_local]

                    # Subfiltro de W/C
                    wc_local = df_plan_filtrado["W/C"].unique().tolist()

                    selected_wc_local = st.multiselect(
                        "Selecciona W/C (puedes elegir varios o dejar vacío para todos):",
                        options=wc_local,
                        key="wc_local"
                    )

            #    with col_reset:
            #        if st.button("🔄 Resetear Filtros"):
            #            st.session_state["wc_type_local"] = wc_types_local[0]  # o ""
            #            st.session_state["wc_local"] = []

            # Aplicar subfiltro de W/C si hay selección
            if selected_wc_local:
                df_plan_filtrado = df_plan_filtrado[df_plan_filtrado["W/C"].isin(selected_wc_local)]

            # Agrupar datos
            cumplimiento_plan = df_plan_filtrado.groupby("W/C")[["To Make", "Produced"]].sum().reset_index()

            # Calcular % de cumplimiento
            cumplimiento_plan["Cumplimiento (%)"] = (
                (cumplimiento_plan["Produced"] / cumplimiento_plan["To Make"]) * 100
            ).round(2)
            cumplimiento_plan["Cumplimiento (%)"].fillna(0, inplace=True)

            # Ordenar de mayor a menor cumplimiento
            cumplimiento_plan = cumplimiento_plan.sort_values(by="Cumplimiento (%)", ascending=True)

            # Gráfica ordenada
            fig, ax = plt.subplots(figsize=(7, 5))
            sns.barplot(
                data=cumplimiento_plan,
                x="W/C",
                y="Cumplimiento (%)",
                palette="light:#5A9",
                order=cumplimiento_plan["W/C"]  # <--- Aquí el orden definido
            )

            # Textos sobre barras
            for bar, row in zip(ax.patches, cumplimiento_plan.itertuples(index=False)):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + 1,
                    f'{row._3:.1f}%',  # _3 si Cumplimiento es la 3a columna
                    ha='center',
                    fontsize=8
                )


            ax.set_title(f'Cumplimiento al Plan ({selected_wc_type_local})')
            ax.set_ylabel("Cumplimiento (%)")
            ax.set_xlabel("Centro de Trabajo (W/C)")
            ax.set_ylim(0, 120)
            ax.grid(axis='y', linestyle='--', alpha=0.5)
            plt.xticks(rotation=45)

            st.pyplot(fig)

            # Mostrar tablas
            st.subheader("📄 Datos Filtrados para Cumplimiento al Plan")
            st.dataframe(df_plan_filtrado[["W/C Type", "W/C", "Job #", "Item", "To Make", "Produced"]])

            st.subheader("📊 Cumplimiento Agrupado por W/C")
            st.dataframe(cumplimiento_plan)

        else:
            st.info("Carga primero el archivo de Scheduled Jobs para mostrar esta gráfica.")

    else:
        st.warning("No hay datos para los W/C seleccionados en este rango.")