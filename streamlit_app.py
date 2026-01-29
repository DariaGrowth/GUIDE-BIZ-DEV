import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta
import io
import numpy as np
import time

# --- 1. КОНФИГУРАЦИЯ И СТИЛИ ---
st.set_page_config(page_title="Ingood Growth", page_icon="favicon.png", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* БАЗОВЫЕ НАСТРОЙКИ */
        .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; color: #334155; }
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        div[data-testid="stVerticalBlock"] { gap: 0rem; }
        
        /* ТЕКСТ И ПОЛЯ */
        .stMarkdown label p, .stTextInput label p, .stNumberInput label p, .stSelectbox label p, .stTextArea label p {
            color: #64748b !important; font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.5px;
        }

        /* ГЛАВНАЯ КНОПКА СОЗДАНИЯ */
        [data-testid="stSidebar"] .stButton > button {
            width: 100%; background-color: #047857 !important; color: white !important;
            border: none; border-radius: 6px; padding: 10px 16px; font-weight: 600; font-size: 15px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1); transition: all 0.2s ease;
            display: flex; align-items: center; justify-content: center; gap: 10px;
        }

        /* КНОПКИ В КАРТОЧКАХ */
        button[kind="primary"] {
            background-color: #047857 !important; color: white !important; border-radius: 6px; padding: 8px 16px;
        }
        
        button[kind="secondary"] {
            background-color: white !important; border: 1px solid #fee2e2 !important; color: #ef4444 !important;
        }

        /* --- САЙДБАР (МОНОХРОМНЫЙ СТИЛЬ) --- */
        div[role="radiogroup"] > label > div:first-child { display: none !important; }
        div[role="radiogroup"] label {
            display: flex; align-items: center; width: 100%; padding: 10px 16px;
            margin-bottom: 4px; border-radius: 8px; border: none; cursor: pointer;
            color: #475569; font-weight: 500; font-size: 15px; transition: all 0.2s;
        }
        div[role="radiogroup"] label[data-checked="true"] { 
            background-color: rgba(16, 185, 129, 0.08) !important; 
            color: #047857 !important; font-weight: 600; 
        }

        /* --- ПАЙПЛАЙН --- */
        
        /* ТЕМНО-ЗЕЛЕНОЕ ОКНО ФИЛЬТРОВ (ИСПРАВЛЕНО) */
        /* Находим родительский контейнер, в котором лежит маркер фильтров */
        [data-testid="stVerticalBlockBorderWrapper"]:has(.filter-marker) {
            background-color: #047857 !important; 
            border: none !important;
            border-radius: 10px !important; 
            padding: 15px !important; 
            margin-bottom: 20px !important;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        
        .filter-label-white {
            color: white !important; font-weight: 700; font-size: 14px; padding-top: 8px;
        }

        /* ШАПКА ТАБЛИЦЫ (ЗЕЛЕНАЯ ЛИНИЯ) */
        /* Находим горизонтальный блок, в котором лежит маркер заголовка */
        [data-testid="stHorizontalBlock"]:has(.header-marker) {
            background-color: rgba(4, 120, 87, 0.1) !important;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px 15px !important;
            margin-bottom: 12px !important;
            margin-top: 10px !important;
        }

        .header-text { 
            color: #000000 !important; 
            font-size: 13px !important; 
            font-weight: 800 !important; 
            text-transform: uppercase; 
            letter-spacing: 0.8px;
        }

        /* КАРТОЧКИ КЛИЕНТОВ */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white !important; border: 1px solid #f1f5f9 !important;
            border-radius: 8px !important; padding: 5px 0px !important; margin-bottom: 8px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: #10b981 !important; }

        /* Клик по компании */
        div[data-testid="column"] .stButton > button {
            background-color: transparent !important; border: none !important;
            color: #0f172a !important; font-weight: 700 !important; font-size: 15px !important;
            text-align: left !important; padding: 0px !important; box-shadow: none !important;
        }
        div[data-testid="column"] .stButton > button:hover { color: #047857 !important; }

        .cell-text { color: #64748b; font-size: 14px; font-weight: 500; }
        .cell-prod { color: #047857; font-weight: 700; font-size: 13px; }
        .cell-salon { color: #6366f1; font-weight: 600; font-size: 13px; }

        .badge { padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700; display: inline-block; }
        .bg-yellow { background: #fef9c3; color: #854d0e; }
        .bg-gray { background: #f1f5f9; color: #64748b; }
        .bg-green { background: #dcfce7; color: #166534; }
        .bg-blue { background: #eff6ff; color: #1d4ed8; border: 1px solid #dbeafe; display: flex; align-items: center; gap: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ПОДКЛЮЧЕНИЯ ---
@st.cache_resource
def init_connections():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key), genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except: return None, None

supabase, _ = init_connections()
if not supabase: st.stop()

# --- 3. HELPERS ---
if 'pipeline_key' not in st.session_state: st.session_state['pipeline_key'] = 0

def reset_pipeline(): 
    st.session_state['pipeline_key'] += 1
    st.cache_data.clear()
    safe_del('active_prospect_id')
    safe_del('ai_draft')

def safe_del(key): 
    if key in st.session_state: del st.session_state[key]

# --- 4. РАБОТА С ДАННЫМИ ---
@st.cache_data(ttl=60)
def get_data(): 
    return pd.DataFrame(supabase.table("prospects").select("*").order("last_action_date", desc=True).execute().data)

def get_sub_data(t, pid):
    d = supabase.table(t).select("*").eq("prospect_id", pid).order("id", desc=True).execute().data
    df = pd.DataFrame(d)
    if df.empty:
        if t == "contacts": return pd.DataFrame(columns=["id", "name", "role", "email", "phone"])
        if t == "samples": return pd.DataFrame(columns=["id", "date_sent", "product_name", "reference", "status", "feedback"])
        if t == "activities": return pd.DataFrame(columns=["id", "date", "type", "content"])
    return df

def count_relances():
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    try:
        res = supabase.table("samples").select("id", count="exact").is_("feedback", "null").lte("date_sent", fifteen_days_ago).execute()
        return res.count if res.count else 0
    except: return 0

def add_log(pid, t, c):
    supabase.table("activities").insert({"prospect_id": pid, "type": t, "content": c, "date": datetime.now().isoformat()}).execute()
    supabase.table("prospects").update({"last_action_date": datetime.now().strftime("%Y-%m-%d")}).eq("id", pid).execute()

def ai_mail(ctx):
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model.generate_content(f"Act as professional B2B assistant. Context: {ctx}.").text

# --- 5. КАРТОЧКА КЛИЕНТА ---
@st.dialog(" ", width="large")
def show_prospect_card(pid, data):
    pid = int(pid)
    st.markdown(f"<h2 style='margin-top: -30px; margin-bottom: 25px; font-size: 24px; color: #1e293b; font-weight: 800;'>{data['company_name']}</h2>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 2], gap="large")

    with c_left:
        with st.container(border=True):
            name = st.text_input("Société", value=data['company_name'], key=f"n_{pid}")
            opts = ["Prospection", "Qualification", "Echantillon", "Test R&D", "Essai industriel", "Négociation", "Client signé"]
            curr = data.get("status", "Prospection")
            stat = st.selectbox("Statut", opts, index=next((i for i, s in enumerate(opts) if s in curr), 0))
            
            c1, c2 = st.columns(2)
            with c1: pays = st.text_input("Pays", value=data.get("country", ""))
            with c2: vol = st.number_input("Potentiel (T)", value=float(data.get("potential_volume") or 0))
            salon_input = st.text_input("Source", value=data.get("last_salon", ""))
            
            st.markdown("---")
            if st.button("🪄 Générer l'Email"):
                st.session_state['ai_draft'] = ai_mail(f"Client: {data['company_name']}")
            if 'ai_draft' in st.session_state:
                st.text_area("Brouillon", value=st.session_state['ai_draft'], height=150)

    with c_right:
        t1, t2, t3 = st.tabs(["Contexte", "Эchantillons", "Journal"])
        with t1:
            prod_list, app_list = ["LEN", "PEP", "NEW"], ["Boulangerie", "Sauces", "Confiserie"]
            p_val, a_val = data.get("product_interest"), data.get("segment")
            p_idx = prod_list.index(p_val) if p_val in prod_list else 0
            a_idx = app_list.index(a_val) if a_val in app_list else 0

            c1, c2 = st.columns(2)
            with c1: prod = st.selectbox("Ingrédient", prod_list, index=p_idx)
            with c2: app = st.selectbox("Application", app_list, index=a_idx)
            contacts = st.data_editor(get_sub_data("contacts", pid), column_config={"id": None}, num_rows="dynamic", use_container_width=True, key=f"ed_{pid}")

        with t2:
            for _, r in get_sub_data("samples", pid).iterrows():
                with st.container(border=True):
                    st.markdown(f"**{r['product_name']}** ({r['date_sent'][:10]})")

        with t3:
            n = st.text_area("Note...", key="nn")
            if st.button("Ajouter"): add_log(pid, "Note", n); st.rerun()
            for _, r in get_sub_data("activities", pid).iterrows(): st.caption(f"{r['date'][:10]}"); st.write(r['content'])

    st.markdown("---")
    if st.button("Enregistrer & Fermer", type="primary", use_container_width=True):
        supabase.table("prospects").update({
            "company_name": name, "status": stat, "country": pays, 
            "potential_volume": vol, "last_salon": salon_input, 
            "product_interest": prod, "segment": app
        }).eq("id", pid).execute()
        reset_pipeline(); st.rerun()

# --- 6. SIDEBAR ---
with st.sidebar:
    st.image("favicon.png", width=60)
    st.write("")
    if st.button("⊕ Nouveau Projet"):
        res = supabase.table("prospects").insert({"company_name": "Nouveau Prospect", "status": "Prospection"}).execute()
        st.session_state['open_new_id'] = res.data[0]['id']; st.rerun()
    st.write("")
    
    rc = count_relances()
    nav_opts = {
        "Tableau de Bord": "❒ Tableau de Bord",
        "Pipeline": "☰ Pipeline",
        "Kanban": "▦ Kanban",
        "Эchantillons": "⬒ Эchantillons",
        "À Relancer": "❍ À Relancer"
    }
    
    selection = st.radio("Nav", list(nav_opts.keys()), format_func=lambda x: nav_opts[x], label_visibility="collapsed", index=1)
    
    if rc > 0:
         st.markdown(f"""<style>
            div[role="radiogroup"] label:nth-child(5)::after {{
                content: '{rc}'; background: #fee2e2; color: #ef4444; 
                display: inline-block; font-size: 10px; font-weight: 700; 
                padding: 1px 7px; border-radius: 10px; margin-left: auto;
            }}
         </style>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("👤 Daria Growth")
    pg = selection

# --- 7. РОУТИНГ ---
if 'open_new_id' in st.session_state:
    st.session_state['active_prospect_id'] = st.session_state.pop('open_new_id'); reset_pipeline()
if 'active_prospect_id' in st.session_state:
    try: show_prospect_card(st.session_state['active_prospect_id'], supabase.table("prospects").select("*").eq("id", st.session_state['active_prospect_id']).execute().data[0])
    except: safe_del('active_prospect_id')

# --- 8. СТРАНИЦЫ ---
if pg == "Pipeline":
    df_raw = get_data()
    
    # --- БЛОК ФИЛЬТРОВ (ИСПРАВЛЕННЫЙ ТЕМНО-ЗЕЛЕНЫЙ) ---
    with st.container(border=True):
        # Добавляем маркер, чтобы CSS нашел этот контейнер
        st.markdown('<div class="filter-marker"></div>', unsafe_allow_html=True)
        f_cols = st.columns([0.8, 2, 2, 2, 2])
        with f_cols[0]: st.markdown('<div class="filter-label-white">▽ Filtres:</div>', unsafe_allow_html=True)
        with f_cols[1]: p_f = st.selectbox("Produit", ["Produit: Tous"] + list(df_raw['product_interest'].dropna().unique()), label_visibility="collapsed")
        with f_cols[2]: s_f = st.selectbox("Statut", ["Statut: Tous", "Prospection", "Qualification", "Echantillon", "Test", "Client"], label_visibility="collapsed")
        with f_cols[3]: sl_f = st.selectbox("Salon", ["Salon: Tous"] + list(df_raw['last_salon'].dropna().unique()), label_visibility="collapsed")
        with f_cols[4]: py_f = st.selectbox("Pays", ["Pays: Tous"] + list(df_raw['country'].dropna().unique()), label_visibility="collapsed")

    df = df_raw.copy()
    if p_f != "Produit: Tous": df = df[df['product_interest'] == p_f]
    if s_f != "Statut: Tous": df = df[df['status'].str.contains(s_f, na=False)]
    if sl_f != "Salon: Tous": df = df[df['last_salon'] == sl_f]
    if py_f != "Pays: Tous": df = df[df['country'] == py_f]
    
    st.write("")
    
    # --- ШАПКА ТАБЛИЦЫ (ИСПРАВЛЕННАЯ ЗЕЛЕНАЯ ЛИНИЯ) ---
    weights = [3.5, 1.2, 1.2, 1.8, 1.8, 2.2, 1.8]
    
    with st.container():
        # Добавляем маркер для всей горизонтальной строки
        st.markdown('<div class="header-marker"></div>', unsafe_allow_html=True)
        h = st.columns(weights)
        h[0].markdown('<span class="header-text">SOCIÉTÉ</span>', unsafe_allow_html=True)
        h[1].markdown('<span class="header-text">PAYS</span>', unsafe_allow_html=True)
        h[2].markdown('<span class="header-text">PRODUIT</span>', unsafe_allow_html=True)
        h[3].markdown('<span class="header-text">STATUT</span>', unsafe_allow_html=True)
        h[4].markdown('<span class="header-text">CONTACT</span>', unsafe_allow_html=True)
        h[5].markdown('<span class="header-text">SALON</span>', unsafe_allow_html=True)
        h[6].markdown('<span class="header-text">SAMPLES</span>', unsafe_allow_html=True)

    # ДАННЫЕ
    samples_data = pd.DataFrame(supabase.table("samples").select("prospect_id").execute().data)
    
    for _, row in df.iterrows():
        with st.container(border=True):
            r = st.columns(weights)
            if r[0].button(row['company_name'], key=f"p_{row['id']}"):
                st.session_state['active_prospect_id'] = row['id']; st.rerun()
            r[1].markdown(f"<span class='cell-text'>{row['country'] or '-'}</span>", unsafe_allow_html=True)
            r[2].markdown(f"<span class='cell-prod'>{row['product_interest'] or '-'}</span>", unsafe_allow_html=True)
            stat = row['status'] or "Prospection"
            badge_cls = "bg-green" if "Client" in stat else "bg-yellow" if "Test" in stat else "bg-gray"
            r[3].markdown(f"<span class='badge {badge_cls}'>{stat}</span>", unsafe_allow_html=True)
            d_contact = "-"
            if row['last_action_date']:
                dt = datetime.strptime(row['last_action_date'][:10], "%Y-%m-%d")
                d_contact = dt.strftime("%d %b. %y")
                color = "#ef4444" if (datetime.now() - dt).days > 30 else "#64748b"
                r[4].markdown(f"<span style='color:{color}; font-weight:800; font-size:14px;'>{d_contact}</span>", unsafe_allow_html=True)
            else: r[4].write("-")
            r[5].markdown(f"<span class='cell-salon'>{row.get('last_salon') or '-'}</span>", unsafe_allow_html=True)
            has_s = not samples_data.empty and row['id'] in samples_data['prospect_id'].values
            if has_s: r[6].markdown("<span class='badge bg-blue'>⬒ En test</span>", unsafe_allow_html=True)
            else: r[6].write("-")

elif pg == "Tableau de Bord":
    st.title("Analyses")
    df = get_data()
    if not df.empty:
        m1, m2 = st.columns(2)
        m1.metric("Projets Total", len(df)); m2.plotly_chart(px.pie(df, names='product_interest', hole=.4), use_container_width=True)

elif pg == "Kanban":
    st.title("Board")
    st.info("Vue Kanban в разработке.")

elif pg == "Эchantillons":
    st.title("Gestion des Эchantillons")
    s = pd.DataFrame(supabase.table("samples").select("*").execute().data)
    st.dataframe(s, use_container_width=True)

elif pg == "À Relancer":
    st.title("Relances ❍")
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    s = pd.DataFrame(supabase.table("samples").select("*").is_("feedback", "null").lte("date_sent", fifteen_days_ago).execute().data)
    if not s.empty: st.dataframe(s, use_container_width=True)
    else: st.success("Tout est à jour !")
