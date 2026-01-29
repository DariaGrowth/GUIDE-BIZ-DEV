import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta
import io
import numpy as np
import time

# --- 1. CONFIGURATION & STYLES ---
st.set_page_config(page_title="Ingood Growth", page_icon="favicon.png", layout="wide")

# Профессиональный CSS: фиксируем цвета и компактность таблицы
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* 1. ГЛОБАЛЬНЫЙ БЕЛЫЙ ФОН */
        .stApp { 
            background-color: #ffffff !important; 
            font-family: 'Inter', sans-serif; 
        }
        
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }

        /* 2. УДАЛЕНИЕ РАССТОЯНИЙ (GAP) МЕЖДУ СТРОКАМИ */
        [data-testid="stVerticalBlock"] { 
            gap: 0rem !important; 
        }
        
        /* 3. ЗЕЛЕНАЯ КНОПКА "НОВЫЙ ПРОЕКТ" */
        [data-testid="stSidebar"] .stButton > button {
            width: 100%; 
            background-color: #047857 !important; 
            color: white !important;
            border: none; 
            border-radius: 6px; 
            padding: 10px 16px; 
            font-weight: 600;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }

        /* 4. ТЕМНО-ЗЕЛЕНЫЙ БЛОК ФИЛЬТРОВ */
        div[data-testid="stVerticalBlock"] > div:nth-child(1) > div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #047857 !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 20px !important;
            margin-bottom: 15px !important;
        }
        
        .filter-label-white { 
            color: #ffffff !important; 
            font-weight: 700; 
            font-size: 14px; 
        }

        /* 5. ШАПКА ТАБЛИЦЫ (БЕЗ ЛИНИИ, КРУПНЫЙ ЗЕЛЕНЫЙ ТЕКСТ) */
        .pipeline-header-row {
            background-color: transparent !important;
            border: none !important;
            padding: 12px 15px 8px 15px;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
        }
        .header-text-style { 
            color: #047857 !important; 
            font-size: 14px !important; 
            font-weight: 800 !important; 
            text-transform: uppercase; 
            letter-spacing: 0.5px;
        }

        /* 6. СВЕРХКОМПАКТНЫЕ БЕЛЫЕ СТРОКИ */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important;
            border: none !important;
            border-bottom: 1px solid #f1f5f9 !important;
            border-radius: 0px !important;
            padding: 2px 15px !important;
            margin-bottom: 0px !important;
        }
        
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            background-color: #fcfdfd !important;
        }

        /* 7. НАЗВАНИЕ КОМПАНИИ: КЛИКАТЕЛЬНЫЙ ТЕКСТ (СТИЛЬ ССЫЛКИ) */
        div[data-testid="column"]:first-child .stButton > button {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            color: #047857 !important;
            font-weight: 800 !important;
            font-size: 15px !important;
            text-align: left !important;
            box-shadow: none !important;
            min-height: 0px !important;
            height: 32px !important;
            line-height: 32px !important;
            display: inline-block !important;
            width: auto !important;
            transition: all 0.2s ease;
        }
        div[data-testid="column"]:first-child .stButton > button:hover {
            text-decoration: underline !important;
            background: transparent !important;
            color: #065f46 !important;
        }

        /* 8. САЙДБАР И УВЕДОМЛЕНИЯ */
        div[role="radiogroup"] label {
            display: flex; align-items: center; padding: 8px 16px;
            color: #475569; font-size: 14px; border-radius: 6px;
        }
        div[role="radiogroup"] label[data-checked="true"] { 
            background-color: rgba(16, 185, 129, 0.08) !important; 
            color: #047857 !important; font-weight: 600; 
        }

        /* КРАСНЫЙ КРУЖОК УВЕДОМЛЕНИЙ */
        .notif-badge {
            background: #fee2e2; color: #ef4444; font-size: 10px; font-weight: 700;
            padding: 1px 7px; border-radius: 10px; margin-left: auto;
        }

        .text-small-muted { color: #64748b; font-size: 13px; font-weight: 500; }
        .badge-ui { padding: 2px 10px; border-radius: 10px; font-size: 10px; font-weight: 700; display: inline-block; }
        .bg-yellow { background: #fef9c3; color: #854d0e; }
        .bg-gray { background: #f1f5f9; color: #64748b; }
        .bg-green { background: #dcfce7; color: #166534; }
        .bg-blue { background: #eff6ff; color: #1d4ed8; border: 1px solid #dbeafe; }

        /* Компактный стиль для кнопок-иконок (корзина) */
        .icon-btn button {
            padding: 0 !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            color: #94a3b8 !important;
        }
        .icon-btn button:hover {
            color: #ef4444 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNECTIONS ---
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

# --- 4. DATA ---
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

# --- 5. FICHE PROSPECT (MODAL) ---
@st.dialog(" ", width="large")
def show_prospect_card(pid, data):
    pid = int(pid)
    st.markdown(f"<h2 style='margin-top: -30px; margin-bottom: 25px; font-size: 22px; color: #1e293b; font-weight: 800;'>{data['company_name']}</h2>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 2], gap="large")

    with c_left:
        with st.container(border=True):
            name = st.text_input("SOCIÉTÉ / CLIENT", value=data['company_name'], key=f"n_{pid}")
            opts = ["Prospection", "Qualification", "Echantillon", "Test R&D", "Essai industriel", "Négociation", "Client signé"]
            curr = data.get("status", "Prospection")
            stat = st.selectbox("STATUT PIPELINE", opts, index=next((i for i, s in enumerate(opts) if s in curr), 0))
            
            c1, c2 = st.columns(2)
            with c1: pays = st.text_input("PAYS", value=data.get("country", ""))
            with c2: vol = st.number_input("POTENTIEL (T)", value=float(data.get("potential_volume") or 0))
            
            # Замена Dernier Salon на Dernier Contact
            last_contact_val = data.get("last_action_date", datetime.now().strftime("%Y-%m-%d"))
            if not last_contact_val: last_contact_val = datetime.now().strftime("%Y-%m-%d")
            last_contact_date = st.date_input("DERNIER CONTACT", value=datetime.strptime(last_contact_val[:10], "%Y-%m-%d"))
            
            st.markdown("---")
            if st.button("🪄 Générer Email"):
                model = genai.GenerativeModel("gemini-1.5-flash")
                res = model.generate_content(f"Ecrire un court email professionnel pour {data['company_name']}").text
                st.session_state['ai_draft'] = res
            if 'ai_draft' in st.session_state:
                st.text_area("Brouillon AI", value=st.session_state['ai_draft'], height=150)

    with c_right:
        # Вкладки как на скриншоте
        t1, t2, t3 = st.tabs(["Contexte & Technique", "Suivi Échantillons", "Journal d'Activité"])
        
        with t1:
            prod_list = ["LENGOOD® (Substitut Œuf)", "PEPTIPEA® (Protéine)", "NEWGOOD® (Nouveauté)"]
            p_val = data.get("product_interest", "LENGOOD® (Substitut Œuf)")
            p_idx = prod_list.index(p_val) if p_val in prod_list else 0
            
            app_list = ["Boulangerie / Pâtisserie", "Sauces / Mayonnaise", "Confiserie", "Plats cuisinés"]
            a_val = data.get("segment", "Boulangerie / Pâtisserie")
            a_idx = app_list.index(a_val) if a_val in app_list else 0

            c1, c2 = st.columns(2)
            with c1: prod = st.selectbox("INGRÉDIENT INGOOD", prod_list, index=p_idx)
            with c2: app = st.selectbox("APPLICATION FINALE", app_list, index=a_idx)
            
            pain_point = st.text_area("PROBLÉMATIQUE / BESOIN (PAIN POINT)", value=data.get("notes", ""), height=100)
            tech_notes = st.text_area("NOTES TECHNIQUES", value=data.get("tech_notes", ""), height=100)
            
            st.markdown("##### CONTACTS")
            contacts = st.data_editor(get_sub_data("contacts", pid), column_config={"id": None}, num_rows="dynamic", use_container_width=True, key=f"ed_{pid}")

        with t2:
            st.markdown("##### AJOUTER UN ÉCHANTILLON")
            cs1, cs2, cs3 = st.columns([2, 1.2, 0.8])
            with cs1: ref_input = st.text_input("Ref", key="new_ref", label_visibility="collapsed", placeholder="Ref (ex: Lot A12)")
            with cs2: prod_input = st.selectbox("Produit", prod_list, key="new_prod_sample", label_visibility="collapsed")
            with cs3: 
                if st.button("Ajouter", type="primary", use_container_width=True):
                    supabase.table("samples").insert({
                        "prospect_id": pid, 
                        "reference": ref_input, 
                        "product_name": prod_input, 
                        "status": "En test", 
                        "date_sent": datetime.now().isoformat()
                    }).execute()
                    st.rerun()

            st.markdown("---")
            st.markdown("##### HISTORIQUE DES ENVOIS")
            samples_df = get_sub_data("samples", pid)
            for _, r in samples_df.iterrows():
                with st.container(border=True):
                    # Исправленная сетка колонок: [Название, Статус, Удалить]
                    # Используем веса [3.5, 1.5, 0.4] для лучшего баланса
                    ch1, ch2, ch3 = st.columns([3.5, 1.5, 0.4])
                    
                    with ch1:
                        st.markdown(f"**{r['product_name']}** {r['reference']} <span style='color:#94a3b8; font-size:12px;'>({r['date_sent'][:10] if r['date_sent'] else ''})</span>", unsafe_allow_html=True)
                    
                    with ch2:
                        s_opts = ["En test", "Validé", "Rejeté", "En attente"]
                        s_idx = s_opts.index(r['status']) if r['status'] in s_opts else 0
                        new_s = st.selectbox("Status", s_opts, index=s_idx, key=f"s_stat_{r['id']}", label_visibility="collapsed")
                        if new_s != r['status']:
                            supabase.table("samples").update({"status": new_s}).eq("id", r['id']).execute()
                    
                    with ch3:
                        # Контейнер для выравнивания кнопки удаления
                        st.markdown('<div class="icon-btn">', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_s_{r['id']}", help="Supprimer", use_container_width=True):
                            supabase.table("samples").delete().eq("id", r['id']).execute()
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Поле фидбека
                    new_f = st.text_area("Feedback R&D client...", value=r.get("feedback", ""), key=f"s_feed_{r['id']}", height=80, placeholder="Feedback R&D client...", label_visibility="collapsed")
                    if new_f != r.get("feedback", ""):
                        supabase.table("samples").update({"feedback": new_f}).eq("id", r['id']).execute()

        with t3:
            st.markdown("##### JOURNAL DES ACTIONS")
            n = st.text_area("Ajouter une note...", key="nn")
            if st.button("Ajouter à l'activité"):
                supabase.table("activities").insert({"prospect_id": pid, "type": "Note", "content": n, "date": datetime.now().isoformat()}).execute()
                st.rerun()
            for _, r in get_sub_data("activities", pid).iterrows(): st.caption(f"{r['date'][:10]}"); st.write(r['content'])

    st.markdown("---")
    if st.button("Enregistrer & Fermer", type="primary", use_container_width=True):
        supabase.table("prospects").update({
            "company_name": name, 
            "status": stat, 
            "country": pays, 
            "potential_volume": vol, 
            "last_action_date": last_contact_date.isoformat(),
            "product_interest": prod, 
            "segment": app,
            "notes": pain_point,
            "tech_notes": tech_notes
        }).eq("id", pid).execute()
        
        # Сохранение контактов
        if not contacts.empty:
            current_ids = contacts['id'].dropna().astype(int).tolist() if 'id' in contacts.columns else []
            old_contacts = get_sub_data("contacts", pid)
            if not old_contacts.empty:
                to_delete = [oid for oid in old_contacts['id'].tolist() if oid not in current_ids]
                if to_delete: supabase.table("contacts").delete().in_("id", to_delete).execute()
            for r in contacts.to_dict('records'):
                if str(r.get("name")).strip():
                    d = {"prospect_id": pid, "name": r["name"], "role": r.get("role",""), "email": r.get("email",""), "phone": r.get("phone","")}
                    if r.get("id") and not pd.isna(r.get("id")): supabase.table("contacts").upsert({**d, "id": int(r["id"])}).execute()
                    else: supabase.table("contacts").insert(d).execute()
                    
        reset_pipeline(); st.rerun()

# --- 6. SIDEBAR ---
with st.sidebar:
    st.image("favicon.png", width=50)
    st.write("")
    if st.button("⊕ Nouveau Projet"):
        res = supabase.table("prospects").insert({"company_name": "Nouveau Prospect", "status": "Prospection"}).execute()
        st.session_state['open_new_id'] = res.data[0]['id']; st.rerun()
    st.write("")
    
    rc = count_relances()
    nav_opts = {
        "Tableau de Bord": "❒ Dashboard",
        "Pipeline": "☰ Pipeline",
        "Kanban": "▦ Kanban",
        "Échantillons": "🧪 Samples",
        "À Relancer": "🔔 Alerts"
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

# --- 7. ROUTING ---
if 'open_new_id' in st.session_state:
    st.session_state['active_prospect_id'] = st.session_state.pop('open_new_id'); reset_pipeline()
if 'active_prospect_id' in st.session_state:
    try: 
        row_v = supabase.table("prospects").select("*").eq("id", st.session_state['active_prospect_id']).execute().data[0]
        show_prospect_card(st.session_state['active_prospect_id'], row_v)
    except: safe_del('active_prospect_id')

# --- 8. PAGES ---
if pg == "Pipeline":
    df_raw = get_data()
    
    # --- БЛОК ФИЛЬТРОВ (ТЕМНО-ЗЕЛЕНЫЙ) ---
    with st.container(border=True):
        f_cols = st.columns([0.8, 2, 2, 2, 2])
        with f_cols[0]: st.markdown('<div class="filter-label-white">▽ Filtres:</div>', unsafe_allow_html=True)
        
        with f_cols[1]: 
            p_list = ["Produit: Tous"] + sorted(list(df_raw['product_interest'].dropna().unique()))
            p_f = st.selectbox("Produit", p_list, label_visibility="collapsed")
            
        with f_cols[2]: 
            s_list = ["Statut: Tous", "Prospection", "Qualification", "Echantillon", "Test R&D", "Essai industriel", "Négociation", "Client signé"]
            s_f = st.selectbox("Statut", s_list, label_visibility="collapsed")
            
        with f_cols[3]: 
            sl_list = ["Source: Tous"] + sorted(list(df_raw['last_salon'].dropna().unique()))
            sl_f = st.selectbox("Salon", sl_list, label_visibility="collapsed")
            
        with f_cols[4]: 
            py_list = ["Pays: Tous"] + sorted(list(df_raw['country'].dropna().unique()))
            py_f = st.selectbox("Pays", py_list, label_visibility="collapsed")

    df = df_raw.copy()
    if p_f != "Produit: Tous": df = df[df['product_interest'] == p_f]
    if s_f != "Statut: Tous": df = df[df['status'].str.contains(s_f, na=False)]
    if py_f != "Pays: Tous": df = df[df['country'] == py_f]
    
    st.write("")
    
    # --- ШАПКА ТАБЛИЦЫ (ЗЕЛЕНЫЙ ШРИФТ) ---
    weights = [3.5, 1.2, 1.2, 1.8, 1.8, 2.2, 1.8]
    st.markdown('<div class="pipeline-header-row">', unsafe_allow_html=True)
    h = st.columns(weights)
    h[0].markdown('<span class="header-text-style">SOCIÉTÉ</span>', unsafe_allow_html=True)
    h[1].markdown('<span class="header-text-style">PAYS</span>', unsafe_allow_html=True)
    h[2].markdown('<span class="header-text-style">PRODUIT</span>', unsafe_allow_html=True)
    h[3].markdown('<span class="header-text-style">STATUT</span>', unsafe_allow_html=True)
    h[4].markdown('<span class="header-text-style">CONTACT</span>', unsafe_allow_html=True)
    h[5].markdown('<span class="header-text-style">SALON</span>', unsafe_allow_html=True)
    h[6].markdown('<span class="header-text-style">SAMPLES</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    samples_db = pd.DataFrame(supabase.table("samples").select("prospect_id").execute().data)
    
    for _, row in df.iterrows():
        with st.container(border=True):
            r = st.columns(weights)
            # Название компании: Стиль гиперссылки
            if r[0].button(row['company_name'], key=f"p_{row['id']}"):
                st.session_state['active_prospect_id'] = row['id']; st.rerun()
            
            r[1].markdown(f"<span class='text-small-muted'>{row['country'] or '-'}</span>", unsafe_allow_html=True)
            r[2].markdown(f"<span style='color:#047857; font-weight:700; font-size:13px;'>{row['product_interest'] or '-'}</span>", unsafe_allow_html=True)
            
            stat = row['status'] or "Prospection"
            badge_cls = "bg-green" if "Client" in stat else "bg-yellow" if "Test" in stat else "bg-gray"
            r[3].markdown(f"<span class='badge-ui {badge_cls}'>{stat}</span>", unsafe_allow_html=True)
            
            last_c = "-"
            if row['last_action_date']:
                dt = datetime.strptime(row['last_action_date'][:10], "%Y-%m-%d")
                d_contact = dt.strftime("%d %b %y")
                color = "#ef4444" if (datetime.now() - dt).days > 30 else "#64748b"
                r[4].markdown(f"<span style='color:{color}; font-weight:700; font-size:13px;'>{d_contact}</span>", unsafe_allow_html=True)
            else: r[4].write("-")
            
            r[5].markdown(f"<span class='text-small-muted'>{row.get('last_salon') or '-'}</span>", unsafe_allow_html=True)
            
            has_s = not samples_db.empty and row['id'] in samples_db['prospect_id'].values
            if has_s: r[6].markdown("<span class='badge-ui bg-blue'>🧪 En test</span>", unsafe_allow_html=True)
            else: r[6].write("-")

else:
    st.title(pg)
    st.info("Coming soon.")
