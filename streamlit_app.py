import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime

# --- 1. CSS & DESIGN SYSTEM ---
st.set_page_config(page_title="Ingood Growth", page_icon="🌱", layout="wide")

st.markdown("""
    <style>
        /* Общий фон */
        .stApp { background-color: #f8fafc; }
        
        /* Сайдбар */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e2e8f0;
        }

        /* КАРТОЧКИ KPI */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #f1f5f9;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        div[data-testid="stMetricLabel"] {
            font-size: 14px; color: #64748b; font-weight: 600; text-transform: uppercase;
        }
        div[data-testid="stMetricValue"] {
            font-size: 32px; color: #10b981; font-weight: 800;
        }

        /* Кнопки */
        div.stButton > button:first-child {
            background-color: #10b981; color: white; border: none;
            border-radius: 8px; font-weight: 600; padding: 0.5rem 1rem;
            box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.4);
        }
        div.stButton > button:first-child:hover {
            background-color: #059669;
        }

        /* Заголовки */
        h1, h2, h3 { color: #0f172a; font-family: 'Inter', sans-serif; }
        
        /* Таблицы */
        div[data-testid="stDataFrame"] {
            background-color: white;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        /* Отступы */
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
    return pd.DataFrame(supabase.table("prospects").select("*").order("last_action_date", desc=True).execute().data)

def get_details(prospect_id, table):
    return pd.DataFrame(supabase.table(table).select("*").eq("prospect_id", prospect_id).order("id", desc=True).execute().data)

# --- 4. UI (Сайдбар) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2921/2921222.png", width=40)
    st.title("Ingood Growth")
    page = st.radio("Navigation", ["Dashboard", "Pipeline", "Contacts"])
    st.divider()
    if st.button("➕ Nouveau Prospect", use_container_width=True):
        res = supabase.table("prospects").insert({"company_name": "NOUVEAU CLIENT"}).execute()
        st.toast("Prospect créé ! Allez dans Pipeline pour l'éditer.")

# --- PAGE: DASHBOARD ---
if page == "Dashboard":
    st.title("Tableau de Bord")
    st.caption("Vue d'ensemble de la performance commerciale")
    
    df = get_data()
    
    if not df.empty:
        # KPI CARDS
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric(label="Total Projets", value=len(df))
        with col2: st.metric(label="Tests R&D En Cours", value=len(df[df['status'] == 'Test R&D']))
        with col3: 
            vol = df['potential_volume'].sum() if 'potential_volume' in df.columns else 0
            st.metric(label="Volume Potentiel", value=f"{vol:.0f} T")
        with col4: st.metric(label="Clients Gagnés", value=len(df[df['status'] == 'Client']))
        
        st.markdown("---")
        
        # ГРАФИКИ
        c_left, c_right = st.columns(2)
        ingood_colors = ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0']
        
        with c_left:
            st.subheader("Répartition par Segment")
            fig_pie = px.pie(df, names='segment', color_discrete_sequence=ingood_colors, hole=0.4)
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with c_right:
            st.subheader("Pipeline par Statut")
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'count']
            fig_bar = px.bar(status_counts, x='status', y='count', color_discrete_sequence=['#10b981'], text='count')
            fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title=None, margin=dict(t=0, b=0, l=0, r=0), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("La base de données est vide.")

# --- PAGE: PIPELINE (ОБНОВЛЕННЫЙ ДИЗАЙН) ---
elif page == "Pipeline":
    st.title("Pipeline Food & Ingrédients")
    st.caption("Suivi des projets R&D et commerciaux.")
    
    df = get_data()
    
    if not df.empty:
        # 1. СТРОКА ПОИСКА (Быстрый поиск)
        search_query = st.text_input("🔍 Rechercher rapide...", placeholder="Nom de société, produit...")
        
        # 2. ФИЛЬТРЫ (В ряд)
        with st.expander("🌪️ Filtres Avancés", expanded=True):
            f1, f2, f3, f4 = st.columns(4)
            
            # Получаем уникальные значения для фильтров
            unique_products = df["product_interest"].unique().tolist()
            unique_status = df["status"].unique().tolist()
            unique_salon = df["last_salon"].unique().tolist() if "last_salon" in df.columns else []
            unique_country = df["country"].unique().tolist() if "country" in df.columns else []
            
            sel_prod = f1.multiselect("Produits", unique_products)
            sel_stat = f2.multiselect("Statuts", unique_status)
            sel_salon = f3.multiselect("Salons", unique_salon)
            sel_country = f4.multiselect("Pays", unique_country)
        
        # 3. ЛОГИКА ФИЛЬТРАЦИИ
        # Поиск
        if search_query:
            mask = df.apply(lambda x: search_query.lower() in str(x.values).lower(), axis=1)
            df = df[mask]
        
        # Фильтры
        if sel_prod: df = df[df["product_interest"].isin(sel_prod)]
        if sel_stat: df = df[df["status"].isin(sel_stat)]
        if sel_salon: df = df[df["last_salon"].isin(sel_salon)]
        if sel_country: df = df[df["country"].isin(sel_country)]

        # 4. ПОДГОТОВКА ДАННЫХ (КРАСОТА)
        # Uppercase для Компании и Продукта
        df['company_name'] = df['company_name'].str.upper()
        df['product_interest'] = df['product_interest'].str.upper()
        
        # Маппинг иконок для Образцов (Sample Status)
        # Если колонки sample_status нет, создаем заглушку
        if 'sample_status' not in df.columns:
            df['sample_status'] = '-'
            
        sample_icons = {
            'Envoyé': '🚀 Envoyé',
            'En test': '🧪 En test', 
            'En cours': '🧪 En test',
            'Reçu': '📥 Reçu',
            'Validé': '✅ Validé',
            'Rejeté': '❌ Rejeté',
            '-': '-'
        }
        # Применяем иконки (безопасно)
        df['sample_display'] = df['sample_status'].map(sample_icons).fillna(df['sample_status'])

        # 5. ОТОБРАЖЕНИЕ ТАБЛИЦЫ
        st.dataframe(
            df,
            column_order=(
                "company_name", 
                "country", 
                "product_interest", 
                "status", 
                "last_action_date", 
                "last_salon", 
                "sample_display", # Наша новая красивая колонка
                "cfia_priority"
            ),
            column_config={
                "company_name": st.column_config.TextColumn("Société", width="medium"),
                "country": st.column_config.TextColumn("Pays", width="small"),
                "product_interest": st.column_config.TextColumn("Produit", width="small"),
                "status": st.column_config.SelectboxColumn(
                    "Statut",
                    width="medium",
                    options=["Prospection", "Qualification", "Test R&D", "Négociation", "Client"],
                    help="Statut du pipeline"
                ),
                "last_action_date": st.column_config.DateColumn("Dernier Contact", format="DD MMM YYYY"),
                "last_salon": st.column_config.TextColumn("Dernier Salon", width="small"),
                "sample_display": st.column_config.TextColumn("Échantillons", width="small"),
                "cfia_priority": st.column_config.CheckboxColumn("CFIA 🚀", width="small"),
            },
            hide_index=True,
            use_container_width=True
        )
        
        # 6. ВЫБОР ДЛЯ РЕДАКТИРОВАНИЯ (Как кнопка Action)
        st.markdown("---")
        c_sel, c_btn = st.columns([3, 1])
        selected_company = c_sel.selectbox("📂 Ouvrir le dossier de :", df["company_name"].unique())
        
        if c_btn.button("Ouvrir Fiche Client >", type="primary"):
            # Находим ID (нужно найти в оригинальном df, так как имена теперь UPPERCASE)
            # Но для простоты предположим, что UPPERCASE совпадает или ищем по индексу
            row = df[df["company_name"] == selected_company].iloc[0]
            st.toast(f"Ouverture de {selected_company} (ID: {row['id']})...")
            # Здесь будет вызов модального окна в следующем шаге
    
    else:
        st.info("Aucun résultat pour ces filtres.")

elif page == "Contacts":
    st.title("Contacts")
    st.info("En construction...")
