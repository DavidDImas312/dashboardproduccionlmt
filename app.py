import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import plotly.express as px
from PIL import Image
from production import produccion_app
from mrp import mrp_app


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
    LOGO_URL_LARGE = "static/LAmteclogo.png"
    img = Image.open(LOGO_URL_LARGE)
    st.set_page_config(page_title='Lamtec Tool', page_icon=img, layout="wide")

    # Inicialización segura de variables en Session State
    for key in ["df_clean", "df_plan", "df_downtime", "df_downtime_procesado"]:
        if key not in st.session_state:
            st.session_state[key] = None

    #st.title("⚙️ Lamtec Tool")
    st.sidebar.title("Aplicaciones Disponibles")
    menu = ["Producción", "MRP"]
    option = st.sidebar.selectbox("Menú:", menu)
    # Pantalla de Inicio
    if option == "Producción":
        st.title("🎯 Eficiencia y Cumplimiento al Plan de Producción")
        produccion_app()
    elif option == "MRP":
        mrp_app()

#Pie de página
        st.markdown("""
        <style>
        .footer {
            position: fixed;
            bottom: 0;
            width: 100%;
            background-color: #ffffff;
            color: gray;
            text-align: center;
            font-size: 12px;
            padding: 10px 0;
            border-top: 1px solid #ddd;
        }
        </style>

        <div class="footer">
            📊 <strong>Lamtec Tool</strong> | Desarrollado por DDIMAS | Versión 1.0 | © 2025 Lamtec México
        </div>
        """, unsafe_allow_html=True)