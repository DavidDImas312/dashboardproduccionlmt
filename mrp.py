# MRP.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import seaborn as sns
import plotly.express as px
from utils import (
    leer_mrp_excel
)

def mrp_app():
    st.header("📉 Análisis Reportes MRP")
    menumrp = ["Importar Reportes", "Comparativo"]
    option = st.sidebar.selectbox("Acciones:", menumrp)

    if option == "Importar Reportes":
        importar_reportes_mrp()

    elif option == "Comparativo":
        comparativo_mrp()

def importar_reportes_mrp():
    st.subheader("📥 Primer archivo MRP")
    uploaded_file_1 = st.file_uploader("📄 Cargar primer archivo Excel MRP", type=["xlsx"], key="mrp1")

    if uploaded_file_1 is not None and "df_po_1" not in st.session_state:
        with st.spinner("Procesando primer archivo..."):
            try:
                df_po_1, df_sin_req_1 = leer_mrp_excel(uploaded_file_1)
                st.session_state["df_po_1"] = df_po_1
                st.session_state["df_sin_req_1"] = df_sin_req_1
                st.success(f"✅ Primer archivo procesado ({len(df_po_1)} POs y {len(df_sin_req_1)} sin requerimiento)")
            except Exception as e:
                st.error(f"❌ Error procesando primer archivo: {e}")
                return

    if "df_po_1" in st.session_state:
        if st.checkbox("📑 Mostrar datos del primer archivo"):
            st.subheader("Órdenes de Compra (PO) - Primer archivo")
            st.dataframe(st.session_state["df_po_1"])

            st.subheader("Items sin Requerimiento - Primer archivo")
            st.dataframe(st.session_state["df_sin_req_1"])

    # Segundo archivo
    st.subheader("📥 Segundo archivo MRP")
    uploaded_file_2 = st.file_uploader("📄 Cargar segundo archivo Excel MRP", type=["xlsx"], key="mrp2")

    if uploaded_file_2 is not None and "df_po_2" not in st.session_state:
        with st.spinner("Procesando segundo archivo..."):
            try:
                df_po_2, df_sin_req_2 = leer_mrp_excel(uploaded_file_2)
                st.session_state["df_po_2"] = df_po_2
                st.session_state["df_sin_req_2"] = df_sin_req_2
                st.success(f"✅ Segundo archivo procesado ({len(df_po_2)} POs y {len(df_sin_req_2)} sin requerimiento)")
            except Exception as e:
                st.error(f"❌ Error procesando segundo archivo: {e}")
                return

    if "df_po_2" in st.session_state:
        if st.checkbox("📑 Mostrar datos del segundo archivo"):
            st.subheader("Órdenes de Compra (PO) - Segundo archivo")
            st.dataframe(st.session_state["df_po_2"])

            st.subheader("Items sin Requerimiento - Segundo archivo")
            st.dataframe(st.session_state["df_sin_req_2"])

def comparativo_mrp():
    st.subheader("📊 Cantidad de Items por Tipo")

    if "df_po_1" not in st.session_state or "df_po_2" not in st.session_state:
        st.warning("⚠️ Carga primero ambos reportes MRP para comparar.")
        return

    df_po_1 = st.session_state["df_po_1"].copy()
    df_po_2 = st.session_state["df_po_2"].copy()

    df_sin_req_1 = st.session_state["df_sin_req_1"].copy()
    df_sin_req_2 = st.session_state["df_sin_req_2"].copy()

    # Crear columna Vendor Limpio en ambos archivos
    def extraer_vendor(vendor_string):
        if pd.isna(vendor_string):
            return "Sin Vendor"
        vendor_string = str(vendor_string)
        if "Vendor" in vendor_string and "P/O" in vendor_string:
            return vendor_string.split("Vendor")[1].split("P/O")[0].strip(", ").strip()
        elif "Vendor" in vendor_string:
            return vendor_string.split("Vendor")[1].strip(", ").strip()
        else:
            return "Sin Vendor"

    # Crear columna PO_Numero en ambos archivos
    def extraer_po_num(vendor_string):
        if pd.isna(vendor_string):
            return "Sin P/O"
        vendor_string = str(vendor_string)
        if "P/O #" in vendor_string:
            try:
                return vendor_string.split("P/O #")[1].split(",")[0].strip()
            except:
                return "Sin P/O"
        else:
            return "Sin P/O"

    df_po_1["PO_Numero"] = df_po_1["Proveedor_PO"].apply(extraer_po_num)
    df_po_2["PO_Numero"] = df_po_2["Proveedor_PO"].apply(extraer_po_num)

    df_po_1["Vendor Limpio"] = df_po_1["Proveedor_PO"].apply(extraer_vendor)
    df_po_2["Vendor Limpio"] = df_po_2["Proveedor_PO"].apply(extraer_vendor)

    col_a, col_b = st.columns(2)

    with col_a:
        # Resumen Archivo 1
        resumen_1 = df_po_1.groupby("Type")["Item"].nunique().reset_index(name="Cantidad")
        resumen_1_sin_po = df_sin_req_1.groupby("Type")["Item"].nunique().reset_index(name="Cantidad")
        st.markdown("**📄 Pre-ejecición MPR**")
        total_1 = pd.concat([resumen_1, resumen_1_sin_po], ignore_index=True)
        total_1 = total_1.groupby("Type")["Cantidad"].sum().reset_index()

        st.dataframe(total_1, use_container_width=True)
    with col_b:
        # Resumen Archivo 2
        resumen_2 = df_po_2.groupby("Type")["Item"].nunique().reset_index(name="Cantidad")
        resumen_2_sin_po = df_sin_req_2.groupby("Type")["Item"].nunique().reset_index(name="Cantidad")
        st.markdown("**📄 Post-Ejecución MRP**")
        total_2 = pd.concat([resumen_2, resumen_2_sin_po], ignore_index=True)
        total_2 = total_2.groupby("Type")["Cantidad"].sum().reset_index()

        st.dataframe(total_2, use_container_width=True)

#    # Resumen Total Combinado (para referencia)
#    resumen_1["Archivo"] = "Archivo 1"
#    resumen_2["Archivo"] = "Archivo 2"
#   resumen_total = pd.concat([resumen_1, resumen_2])

#    st.markdown("**📑 Resumen combinado**")
#    st.dataframe(resumen_total, use_container_width=True)

    # 📋 Comparativa de Items con PO entre archivos
    st.subheader("📌 Cambios en Reuqerimiento")

    # Items con PO en cada archivo
    items_po_1 = set(df_sin_req_1["Item"].unique())
    items_po_2 = set(df_sin_req_2["Item"].unique())

    # Items que tenían PO en archivo 1 pero ya no en archivo 2
    items_po_solo_en_1 = sorted(items_po_2 - items_po_1)

    # Items que tienen PO en archivo 2 pero no en archivo 1
    items_po_solo_en_2 = sorted(items_po_1 - items_po_2)

    # Convertir a DataFrames
    df_items_po_solo_1 = pd.DataFrame(items_po_solo_en_1, columns=["Item"])
    df_items_po_solo_2 = pd.DataFrame(items_po_solo_en_2, columns=["Item"])

    # Mostrar en columnas
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📄 Items con Requerimiento Antes de MRP y Después ya no**")
        st.dataframe(df_items_po_solo_1, use_container_width=True)
        #st.metric("Total", len(df_items_po_solo_1))

    with col2:
        st.markdown("**📄 Items con Requerimiento Después de MRP y Antes no**")
        st.dataframe(df_items_po_solo_2, use_container_width=True)
        #st.metric("Total", len(df_items_po_solo_2))

    # 📌 Calcular días de atraso en Archivo 2
    hoy = pd.to_datetime(datetime.date.today())
    df_po_2["Fecha Llegada"] = pd.to_datetime(df_po_2["Fecha Llegada"], errors='coerce')
    df_po_2["Días de Atraso"] = (hoy - df_po_2["Fecha Llegada"]).dt.days

    # Filtrar items con P/O y más de 30 días de atraso
    items_mas_30_dias = df_po_2[
        (df_po_2["PO_Numero"] != "Sin P/O") & (df_po_2["Días de Atraso"] > 30)
        ]

    # Mostrar resumen
    st.subheader("📛 Items con Requerimiento y Más de 30 Días de Atraso")

    if not items_mas_30_dias.empty:
        st.markdown(f"Se encontraron **{items_mas_30_dias['Item'].nunique()} items** con más de 30 días de atraso.")
        st.dataframe(
            items_mas_30_dias[["Item", "PO_Numero", "Vendor Limpio", "Fecha Llegada", "Días de Atraso", "Cantidad"]]
        )
    else:
        st.success("✅ No hay items con P/O atrasados más de 30 días.")

    # 📦 Items sin requerimiento por archivo
    #if st.checkbox("Mostrar Tablas de Items sin Requerimiento"):
    st.subheader("📦 Items sin requerimiento por archivo")

    col3, col4 = st.columns(2)

    with col3:
        if "df_sin_req_1" in st.session_state:
            total_items_1 = st.session_state["df_sin_req_1"]["Item"].nunique()
            st.markdown(f"**📄 Antes — Total de items sin requerimiento: `{total_items_1}`**")
            st.dataframe(
                st.session_state["df_sin_req_1"][["Item", "Vendor"]],
                use_container_width=True
            )
        else:
            st.info("No se ha cargado el Archivo 1.")

    with col4:
        if "df_sin_req_2" in st.session_state:
            total_items_2 = st.session_state["df_sin_req_2"]["Item"].nunique()
            st.markdown(f"**📄 Después — Total de items sin requerimiento: `{total_items_2}`**")
            st.dataframe(
                st.session_state["df_sin_req_2"][["Item", "Vendor"]],
                use_container_width=True
            )
        else:
            st.info("No se ha cargado el Archivo 2.")

    st.subheader("📈 Gráfica: Items sin Requerimiento por Vendor")

    # Validar que existan datos en ambos dataframes
    if "df_sin_req_1" in st.session_state and "df_sin_req_2" in st.session_state:
        df_sin_req_1 = st.session_state["df_sin_req_1"].copy()
        df_sin_req_2 = st.session_state["df_sin_req_2"].copy()

        # Agrupar por Vendor
        df_vendor_1 = df_sin_req_1.groupby("Vendor")["Item"].nunique().reset_index(name="Total")
        df_vendor_1["Archivo"] = "Antes"

        df_vendor_2 = df_sin_req_2.groupby("Vendor")["Item"].nunique().reset_index(name="Total")
        df_vendor_2["Archivo"] = "Después"

        df_vendor_total = pd.concat([df_vendor_1, df_vendor_2])

        if not df_vendor_total.empty:
            fig = px.bar(
                df_vendor_total,
                x="Vendor",
                y="Total",
                color="Archivo",
                barmode="group",
                title="Items sin Requerimiento por Vendor",
                height=500
            )
            fig.update_layout(xaxis_title="Vendor", yaxis_title="Total de Items")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de Items sin Requerimiento para graficar.")
    else:
        st.warning("⚠️ Carga ambos archivos para visualizar esta gráfica.")

    # 📌 Filtros en sidebar
    st.sidebar.subheader("🔍 Filtros para comparativo")

    # Filtro de Type
    tipos_disponibles = sorted(set(df_po_1["Type"].unique()).union(df_po_2["Type"].unique()))
    tipo_seleccionado = st.sidebar.selectbox("Selecciona Type:", options=["Todos"] + tipos_disponibles)

    # Vendor dinámico según Type seleccionado
    if tipo_seleccionado != "Todos":
        vendors_disponibles = sorted(
            set(df_po_1[df_po_1["Type"] == tipo_seleccionado]["Vendor Limpio"].unique()).union(
                df_po_2[df_po_2["Type"] == tipo_seleccionado]["Vendor Limpio"].unique()
            )
        )
    else:
        vendors_disponibles = sorted(
            set(df_po_1["Vendor Limpio"].unique()).union(df_po_2["Vendor Limpio"].unique())
        )

    vendor_seleccionado = st.sidebar.selectbox("Selecciona Vendor:", options=["Todos"] + vendors_disponibles)

    # Validación de filtros obligatorios
    if tipo_seleccionado == "Todos" or vendor_seleccionado == "Todos":
        st.warning(
            "⚠️ Selecciona un **Type** y un **Vendor** en los filtros del sidebar para habilitar el comparativo.")
        return

    # Filtrar datos según Type y Vendor
    df_po_1_filtrado = df_po_1[
        (df_po_1["Type"] == tipo_seleccionado) & (df_po_1["Vendor Limpio"] == vendor_seleccionado)
    ]
    df_po_2_filtrado = df_po_2[
        (df_po_2["Type"] == tipo_seleccionado) & (df_po_2["Vendor Limpio"] == vendor_seleccionado)
    ]

    # Filtro dinámico de P/O según Vendor y Type seleccionado
    po_disponibles = sorted(set(df_po_1_filtrado["PO_Numero"].unique()).union(df_po_2_filtrado["PO_Numero"].unique()))

    po_seleccionado = st.sidebar.selectbox("Selecciona P/O #:", options=["Todos"] + po_disponibles)

    # Solo aplicar filtro si se selecciona una P/O específica
    if po_seleccionado != "Todos":
        df_po_1_filtrado = df_po_1_filtrado[df_po_1_filtrado["PO_Numero"] == po_seleccionado]
        df_po_2_filtrado = df_po_2_filtrado[df_po_2_filtrado["PO_Numero"] == po_seleccionado]

    # Filtro dinámico de Items según Vendor seleccionado
    items_disponibles = sorted(set(df_po_1_filtrado["Item"].unique()).union(df_po_2_filtrado["Item"].unique()))

    items_seleccionados = st.sidebar.multiselect(
        "Selecciona Items:", options=items_disponibles, default=items_disponibles
    )

    fechas_1 = pd.to_datetime(df_po_1["Fecha Llegada"], errors='coerce')
    fechas_2 = pd.to_datetime(df_po_2["Fecha Llegada"], errors='coerce')

    fecha_min = min(fechas_1.min(), fechas_2.min())
    fecha_max = max(fechas_1.max(), fechas_2.max())

    rango_fechas = st.sidebar.date_input(
        "Rango de Fechas:",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    # Comparativa agrupada
    comparativo_df_1 = df_po_1_filtrado.groupby(["Item", "Fecha Llegada"])["Cantidad"].sum().reset_index()
    comparativo_df_1.rename(columns={"Cantidad": "Cantidad Antes"}, inplace=True)

    comparativo_df_2 = df_po_2_filtrado.groupby(["Item", "Fecha Llegada"])["Cantidad"].sum().reset_index()
    comparativo_df_2.rename(columns={"Cantidad": "Cantidad Después"}, inplace=True)

    comparativo_final = pd.merge(
        comparativo_df_1, comparativo_df_2,
        on=["Item", "Fecha Llegada"], how="outer"
    ).fillna(0)

    comparativo_final["Fecha Llegada"] = pd.to_datetime(comparativo_final["Fecha Llegada"], errors='coerce')
    comparativo_final["Diferencia"] = comparativo_final["Cantidad Después"] - comparativo_final["Cantidad Antes"]

    # Aplicar filtros de Item
    comparativo_final = comparativo_final[comparativo_final["Item"].isin(items_seleccionados)]

    # Validar que el usuario haya seleccionado ambas fechas antes de filtrar por rango
    if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = pd.to_datetime(rango_fechas[0]), pd.to_datetime(rango_fechas[1])
        comparativo_final = comparativo_final[
            (comparativo_final["Fecha Llegada"] >= fecha_inicio) & (comparativo_final["Fecha Llegada"] <= fecha_fin)
            ]
    else:
        st.info("Selecciona ambas fechas para aplicar el filtro de rango.")

    if comparativo_final.empty:
        st.info("No hay datos para mostrar con los filtros seleccionados.")
    else:
        num_items = comparativo_final["Item"].nunique()

        # Si hay demasiados items, evitar graficar
        if num_items > 20:  # aquí tú defines el límite razonable (20, 30, etc)
            st.warning(
                "Selecciona otro rango o menos items — la información es muy grande y no es posible presentarla en la gráfica.")
        else:
            st.subheader("📈 Gráfica de Requerimientos")
            fig = px.bar(
                comparativo_final.melt(id_vars=["Item", "Fecha Llegada"],
                                       value_vars=["Cantidad Antes", "Cantidad Después"]),
                x="Fecha Llegada",
                y="value",
                color="variable",
                barmode="group",
                facet_col="Item",
                labels={"value": "Cantidad", "variable": "Archivo"},
                title=f"Comparativo {tipo_seleccionado} - {vendor_seleccionado}",
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

    if st.checkbox("Mostrar Tabla Comparativa"):
        st.subheader("📑 Tabla Comparativa de Requerimientos Filtrada")
        st.dataframe(comparativo_final)

    # Obtener fecha actual
    hoy = pd.to_datetime(datetime.date.today())

    # Calcular días restantes y días de atraso sobre el archivo 2 filtrado
    df_po_2_filtrado["Fecha Llegada"] = pd.to_datetime(df_po_2_filtrado["Fecha Llegada"], errors='coerce')
    df_po_2_filtrado["Días Restantes"] = (df_po_2_filtrado["Fecha Llegada"] - hoy).dt.days

    # Filtrar items próximos a entregar en 7 días
    proximos_7_dias = df_po_2_filtrado[
        (df_po_2_filtrado["Días Restantes"] >= 0) & (df_po_2_filtrado["Días Restantes"] <= 7)
        ]

    # Filtrar items atrasados
    atrasados = df_po_2_filtrado[df_po_2_filtrado["Días Restantes"] < 0].copy()
    atrasados["Días de Atraso"] = atrasados["Días Restantes"].abs()

    # 📊 Mostrar resumen de alertas
    st.subheader("🚨 Alertas de Entregas")

    # Métricas resumen
    col1, col2 = st.columns(2)
    col1.metric("Próximos a entregar (7 días)", len(proximos_7_dias))
    col2.metric("Items Atrasados", len(atrasados))

    # Mostrar tabla de próximos
    if not proximos_7_dias.empty:
        st.markdown("### 📅 Próximas entregas (7 días)")
        st.dataframe(
            proximos_7_dias[["Item", "Fecha Llegada", "Días Restantes", "Cantidad"]]
        )
    else:
        st.info("✅ No hay entregas programadas en los próximos 7 días.")

    # Mostrar tabla de atrasados
    if not atrasados.empty:
        st.markdown("### ⚠️ Entregas Atrasadas")
        st.dataframe(
            atrasados[["Item", "Fecha Llegada", "Días de Atraso", "Cantidad"]]
        )
    else:
        st.success("✅ No hay entregas atrasadas.")