import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime

# --- 1. CSS & DESIGN SYSTEM ---
st.markdown("""
    <style>
        /* Общий фон */
        .stApp {
            background-color: #f8fafc; /* Светлый серо-голубой фон (Slate 50) */
        }
        
        /* Сайдбар */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e2e8f0;
        }

        /* СТИЛЬ KPI КАРТОЧЕК (Метрики) */
        div[data-testid="stMetric"] {
            background-color: #ffffff; /* Чисто белый фон */
            border: 1px solid #f1f5f9; /* Едва заметная рамка */
            padding: 24px; /* Больше воздуха внутри */
            border-radius: 16px; /* Сильно скругленные углы */
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); /* Мягкая тень */
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px); /* Эффект парения при наведении */
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        
        /* Текст метрик */
        div[data-testid="stMetricLabel"] {
            font-size: 14px;
            color: #64748b; /* Серый текст заголовка */
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        div[data-testid="stMetricValue"] {
            font-size: 32px;
            color: #10b981; /* Зеленый Emerald для цифр */
            font-weight: 800;
        }

        /* Кнопки */
        div.stButton > button:first-child {
            background-color: #10b981;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.4);
        }
        div.stButton > button:first-child:hover {
            background-color: #059669;
        }

        /* Заголовки */
        h1, h2, h3 {
            color: #0f172a;
            font-family: 'Inter', sans-serif;
        }
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

# --- PAGE: DASHBOARD ---
if menu == "📊 Dashboard": # Убедитесь, что переменная menu совпадает с вашей
    st.title("Tableau de Bord")
    st.caption("Vue d'ensemble de la performance commerciale")
    
    df = load_data() # Или get_prospects(), проверьте название вашей функции
    
    if not df.empty:
        # 1. KPI CARDS (Считаем цифры)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(label="Total Projets", value=len(df))
        
        with col2:
            # Считаем только активные тесты
            active_rd = len(df[df['status'] == 'Test R&D'])
            st.metric(label="Tests R&D En Cours", value=active_rd)
            
        with col3:
            # Считаем сумму, если колонка есть, иначе 0
            vol = df['potential_volume'].sum() if 'potential_volume' in df.columns else 0
            st.metric(label="Volume Potentiel", value=f"{vol:.0f} T")
            
        with col4:
            # Считаем клиентов со статусом "Client" (Won)
            clients_won = len(df[df['status'] == 'Client'])
            st.metric(label="Clients Gagnés", value=clients_won)
        
        st.markdown("---")
        
        # 2. ГРАФИКИ (PLOTLY)
        # Настройка цветов бренда
        ingood_colors = ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5']
        
        c_left, c_right = st.columns(2)
        
        with c_left:
            st.subheader("Répartition par Segment")
            # Donut Chart (Бублик) выглядит современнее Пирога
            fig_pie = px.pie(
                df, 
                names='segment', 
                color_discrete_sequence=ingood_colors,
                hole=0.4 # Делает "дырку" в центре
            )
            # Убираем фон и легенду делаем аккуратной
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", # Прозрачный фон
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                margin=dict(t=0, b=0, l=0, r=0)
            )
            # Добавляем данные внутрь графика
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with c_right:
            st.subheader("Pipeline par Statut")
            # Считаем кол-во проектов по статусам
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'count']
            
            fig_bar = px.bar(
                status_counts, 
                x='status', 
                y='count',
                color_discrete_sequence=['#10b981'], # Один фирменный цвет
                text='count' # Показываем цифру над столбцом
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title=None,
                yaxis_title=None,
                margin=dict(t=0, b=0, l=0, r=0),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9') # Едва заметная сетка
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
    else:
        st.info("La base de données est vide. Ajoutez un prospect pour voir les statistiques.")
    
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
