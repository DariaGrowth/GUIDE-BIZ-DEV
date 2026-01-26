import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime

# --- 1. НАСТРОЙКИ И ДИЗАЙН (CSS INJECTION) ---
st.set_page_config(page_title="Ingood Growth", page_icon="🌱", layout="wide")

# Усиленный CSS для имитации вашего HTML-дизайна
st.markdown("""
    <style>
        /* Имитация Tailwind CSS Slate-50 */
        .stApp {
            background-color: #f8fafc;
        }
        
        /* Сайдбар - белый и чистый */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e2e8f0;
            box-shadow: 2px 0 5px rgba(0,0,0,0.02);
        }
        
        /* Кнопки - Emerald Green с тенью */
        div.stButton > button:first-child {
            background-color: #10b981;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.4);
            transition: all 0.2s;
        }
        div.stButton > button:first-child:hover {
            background-color: #059669;
            box-shadow: 0 6px 8px -1px rgba(16, 185, 129, 0.6);
            transform: translateY(-1px);
        }

        /* Карточки метрик (KPI) - как в HTML */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            color: #0f172a;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 14px;
            color: #64748b; /* Slate-500 */
            font-weight: 500;
        }
        div[data-testid="stMetricValue"] {
            font-size: 28px;
            color: #0f172a; /* Slate-900 */
            font-weight: 700;
        }
        
        /* Заголовки */
        h1, h2, h3 {
            color: #0f172a;
            font-family: 'Inter', sans-serif;
        }
        
        /* Убираем лишние отступы сверху */
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ПОДКЛЮЧЕНИЕ ---
@st.cache_resource
def init_connections():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key), genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except:
        return None, None

supabase, _ = init_connections()
if not supabase: st.stop()

# --- 3. ФУНКЦИИ ---
def get_data():
    return pd.DataFrame(supabase.table("prospects").select("*").execute().data)

# --- 4. UI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2921/2921222.png", width=40)
    st.title("Ingood Growth")
    page = st.radio("Navigation", ["Dashboard", "Pipeline", "Contacts"])
    st.divider()
    if st.button("➕ Nouveau Prospect", use_container_width=True):
        st.toast("Fonction Nouveau Prospect")

if page == "Dashboard":
    st.title("Tableau de Bord")
    df = get_data()
    
    if not df.empty:
        # KPI CARDS
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Projets", len(df))
        c2.metric("Tests R&D", len(df[df['status']=='Test R&D']), delta="Actifs")
        vol = df['potential_volume'].sum() if 'potential_volume' in df.columns else 0
        c3.metric("Potentiel (T)", f"{vol:.0f} T")
        
        st.markdown("---")
        
        # CHARTS (Светлая тема)
        c_left, c_right = st.columns(2)
        
        # График 1
        fig_pie = px.pie(df, names='segment', title='Répartition par Segment', 
                         color_discrete_sequence=['#10b981', '#34d399', '#6ee7b7', '#a7f3d0'])
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        c_left.plotly_chart(fig_pie, use_container_width=True)
        
        # График 2
        fig_bar = px.bar(df, x='status', title='Pipeline par Statut', 
                         color_discrete_sequence=['#10b981'])
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        c_right.plotly_chart(fig_bar, use_container_width=True)

elif page == "Pipeline":
    st.title("Pipeline Commercial")
    df = get_data()
    if not df.empty:
        st.dataframe(
            df, 
            column_config={
                "status": st.column_config.SelectboxColumn("Statut", options=["Prospection", "Client"]),
                "cfia_priority": st.column_config.CheckboxColumn("CFIA")
            },
            use_container_width=True, hide_index=True
        )
