# MRP.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from utils import (
    cargar_datos_columnas_requeridas,
    required_columns,
    required_columns_plan,
    cargar_downtime,
    extraer_downtime,
    catalogo_downtime,
    filtrar_downtime
)

def mrp_app():
    st.header("🚧 Estamos construyendo este apartado...")