# escalera.py

import streamlit as st
from utils import cargar_archivos_estilo_escalera, graficar_evolucion_item, exportar_excel

def escalera_app():
    #st.set_page_config(page_title="Análisis Escalera", layout="wide")

    st.title("📊 Análisis con Escalera de Ítems por Fecha")

    # 🧾 Instrucciones de uso
    with st.expander("ℹ️ Instrucciones para cargar los archivos", expanded=True):
        st.markdown("""
        **Formato requerido para el análisis:**

        - Los archivos deben estar en formato **Excel (.xlsx)**.
        - La **columna A** debe contener la lista de ítems o datos a comparar (por ejemplo, números de parte).
        - Las **columnas B en adelante** deben contener **fechas en formato `dd/mm/yyyy`** como encabezados.
        - Las celdas deben contener las **cantidades por ítem y fecha**.

        **Ejemplo de formato válido:**

        | Item        | 01/07/2025 | 08/07/2025 | 15/07/2025 |
        |-------------|------------|------------|------------|
        | G09115-103  | 3200       | 3000       | 2800       |
        | G09115-104  | 1000       | 1100       | 1200       |

        ⚠️ Asegúrate de que las fechas estén bien escritas y que no haya celdas vacías en los encabezados.
        """)


    # 📥 Cargar archivos
    archivos = st.file_uploader("📂 Cargar archivos Excel (en orden)", type=["xlsx"], accept_multiple_files=True)

    if archivos:
        # 🚀 Cargar datos estilo escalera
        df_escalera, versiones = cargar_archivos_estilo_escalera(archivos)

        if df_escalera is not None:
            # 📋 Mostrar tabla escalera
            st.subheader("📋 Tabla Estilo Escalera")
            st.dataframe(df_escalera, use_container_width=True)

            # 📈 Gráfico por ítem
            st.subheader("📈 Evolución por Ítem")
            item_sel = st.selectbox("Selecciona un ítem", sorted(df_escalera["Item"].unique()))
            graficar_evolucion_item(df_escalera, item_sel)

            # 💾 Exportar a Excel
            st.subheader("⬇️ Exportar a Excel")
            excel_data = exportar_excel(df_escalera)
            st.download_button(
                label="📥 Descargar archivo Excel",
                data=excel_data,
                file_name="analisis_escalera.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("Por favor, sube al menos dos archivos Excel para comenzar el análisis.")
