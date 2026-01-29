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

# Professional CSS Injection to force layout and colors
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* 1. APP BACKGROUND */
        .stApp { 
            background-color: #f1f5f9 !important; 
            font-family: 'Inter', sans-serif; 
        }
        
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        
        /* 2. INGOOD DARK GREEN FILTERS PANEL */
        /* Targets the first border wrapper container on the page */
        div[data-testid="stVerticalBlock"] > div:nth-child(1) > div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #047857 !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 15px 20px !important;
            margin-bottom: 20px !important;
        }
        
        .filter-header-white { 
            color: #ffffff !important; 
            font-weight: 700 !important; 
            font-size: 14px !important; 
            margin-top: 8px !important;
        }

        /* 3. TABLE HEADER STYLE (LIGHT GREEN LINE) */
        .custom-header-bar {
            background-color: rgba(4, 120, 87, 0.1) !important;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px 15px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
        }
        .header-label { 
            color: #000000 !important; 
            font-size: 12px !important; 
            font-weight: 800 !important; 
            text-transform: uppercase; 
            letter-spacing: 0.5px;
        }

        /* 4. PROSPECT ROWS (WHITE CARDS) - FIXED HEIGHT */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            padding: 2px 15px !important; /* Reduced padding to make it compact */
            margin-bottom: 8px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
        }
        
        /* Ensure filter block keeps its padding */
        div[data-testid="stVerticalBlock"] > div:nth-child(1) > div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 15px 20px !important;
        }

        /* 5. COMPANY NAME: PLAIN GREEN BOLD TEXT LINK */
        div[data-testid="column"]:first-child button {
            background: none !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            color: #047857 !important;
            font-weight: 800 !important;
            font-size: 15px !important;
            text-align: left !important;
            box-shadow: none !important;
            cursor: pointer !important;
        }
        div[data-testid="column"]:first-child button:hover {
            color: #065f46 !important;
            text-decoration: underline !important;
        }

        /* 6. SIDEBAR STYLING (MONOCHROME) */
        div[role="radiogroup"] label {
            display: flex; align-items: center; padding: 10px 16px;
            color: #475569; font-size: 14px; border-radius: 8px;
        }
        div[role="radiogroup"] label[data-checked="true"] { 
            background-color: rgba(16, 185, 129, 0.08) !important; 
            color: #047857 !important; font-weight: 600; 
        }

        /* BADGES */
        .badge-base { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; display: inline-block; }
        .bg-yellow { background: #fef9c3; color: #854d0e; }
        .bg-gray { background: #f1f5f9; color: #64748b; }
        .bg-green { background: #dcfce7; color: #166534; }
        .bg-blue { background: #eff6ff; color: #1d4ed8; border: 1px solid #dbeafe; }
        
        .cell-text-gray { color: #64748b; font-size: 13px; font-weight: 500; }
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

# --- 5. FICHE PROSPECT (MODAL) ---
@st.dialog(" ", width="large")
def show_prospect_card(pid, data):
    pid = int(pid)
    st.markdown(f"<h2 style='margin-top: -30px; margin-bottom: 25px; font-size: 22px; color: #1e293b; font-weight: 800;'>{data['company_name']}</h2>", unsafe_allow_html=True)
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
                model = genai.GenerativeModel("gemini-1.5-flash")
                st.session_state['ai_draft'] = model.generate_content(f"Write a short professional B2B email for {data['company_name']} in French.").text
            if 'ai_draft' in st.session_state:
                st.text_area("AI Draft", value=st.session_state['ai_draft'], height=150)

    with c_right:
        t1, t2, t3 = st.tabs(["Contexte", "Échantillons", "Journal"])
        with t1:
            prod_list = ["LEN", "PEP", "NEW"]
            p_val = data.get("product_interest")
            p_idx = prod_list.index(p_val) if p_val in prod_list else 0

            c1, c2 = st.columns(2)
            with c1: prod = st.selectbox("Ingrédient", prod_list, index=p_idx)
            with c2: app = st.selectbox("Application", ["Boulangerie", "Sauces", "Confiserie"], index=0)
            contacts = st.data_editor(get_sub_data("contacts", pid), column_config={"id": None}, num_rows="dynamic", use_container_width=True, key=f"ed_{pid}")

        with t2:
            for _, r in get_sub_data("samples", pid).iterrows():
                with st.container(border=True): st.markdown(f"**{r['product_name']}** ({r['date_sent'][:10]})")

        with t3:
            n = st.text_area("Note...", key="nn")
            if st.button("Ajouter"):
                supabase.table("activities").insert({"prospect_id": pid, "type": "Note", "content": n, "date": datetime.now().isoformat()}).execute()
                st.rerun()
            for _, r in get_sub_data("activities", pid).iterrows(): st.caption(f"{r['date'][:10]}"); st.write(r['content'])

    st.markdown("---")
    if st.button("Enregistrer & Fermer", type="primary", use_container_width=True):
        supabase.table("prospects").update({
            "company_name": name, "status": stat, "country": pays, 
            "potential_volume": vol, "last_salon": salon_input, 
            "product_interest": prod
        }).eq("id", pid).execute()
        reset_pipeline(); st.rerun()

# --- 6. SIDEBAR ---
with st.sidebar:
    st.image("favicon.png", width=55)
    st.write("")
    if st.button("⊕ Nouveau Projet"):
        res = supabase.table("prospects").insert({"company_name": "Nouveau Prospect", "status": "Prospection"}).execute()
        st.session_state['open_new_id'] = res.data[0]['id']; st.rerun()
    st.write("")
    
    nav_opts = {
        "Tableau de Bord": "❒ Dashboard",
        "Pipeline": "☰ Pipeline",
        "Kanban": "▦ Kanban",
        "Échantillons": "🧪 Samples",
        "À Relancer": "🔔 Alerts"
    }
    
    selection = st.radio("Nav", list(nav_opts.keys()), format_func=lambda x: nav_opts[x], label_visibility="collapsed", index=1)
    st.markdown("---")
    st.caption("👤 Daria Growth")
    pg = selection

# --- 7. ROUTING ---
if 'open_new_id' in st.session_state:
    st.session_state['active_prospect_id'] = st.session_state.pop('open_new_id'); reset_pipeline()
if 'active_prospect_id' in st.session_state:
    try: 
        row_data = supabase.table("prospects").select("*").eq("id", st.session_state['active_prospect_id']).execute().data[0]
        show_prospect_card(st.session_state['active_prospect_id'], row_data)
    except: safe_del('active_prospect_id')

# --- 8. PAGES ---
if pg == "Pipeline":
    df_raw = get_data()
    
    # --- FILTERS PANEL (DARK GREEN) ---
    with st.container(border=True):
        f_cols = st.columns([0.8, 2, 2, 2, 2])
        with f_cols[0]: st.markdown('<div class="filter-header-white">▽ Filtres:</div>', unsafe_allow_html=True)
        with f_cols[1]: p_f = st.selectbox("Produit", ["Produit: Tous"] + list(df_raw['product_interest'].dropna().unique()), label_visibility="collapsed")
        with f_cols[2]: s_f = st.selectbox("Statut", ["Statut: Tous", "Prospection", "Qualification", "Echantillon", "Test", "Client"], label_visibility="collapsed")
        with f_cols[3]: sl_f = st.selectbox("Salon", ["Salon: Tous"] + list(df_raw['last_salon'].dropna().unique()), label_visibility="collapsed")
        with f_cols[4]: py_f = st.selectbox("Pays", ["Pays: Tous"] + list(df_raw['country'].dropna().unique()), label_visibility="collapsed")

    df = df_raw.copy()
    if p_f != "Produit: Tous": df = df[df['product_interest'] == p_f]
    if s_f != "Statut: Tous": df = df[df['status'].str.contains(s_f, na=False)]
    
    st.write("")
    
    # --- TABLE HEADER ---
    weights = [3.5, 1.2, 1.2, 1.8, 1.8, 2.2, 1.8]
    st.markdown('<div class="custom-header-bar">', unsafe_allow_html=True)
    h = st.columns(weights)
    h[0].markdown('<span class="header-label">SOCIÉTÉ</span>', unsafe_allow_html=True)
    h[1].markdown('<span class="header-label">PAYS</span>', unsafe_allow_html=True)
    h[2].markdown('<span class="header-label">PRODUIT</span>', unsafe_allow_html=True)
    h[3].markdown('<span class="header-label">STATUT</span>', unsafe_allow_html=True)
    h[4].markdown('<span class="header-label">CONTACT</span>', unsafe_allow_html=True)
    h[5].markdown('<span class="header-label">SALON</span>', unsafe_allow_html=True)
    h[6].markdown('<span class="header-label">SAMPLES</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    samples_list = pd.DataFrame(supabase.table("samples").select("prospect_id").execute().data)
    
    for _, row in df.iterrows():
        # DATA ROW (WHITE CARD)
        with st.container(border=True):
            r = st.columns(weights)
            # Company Name: Bold Dark Green Text
            if r[0].button(row['company_name'], key=f"p_{row['id']}"):
                st.session_state['active_prospect_id'] = row['id']; st.rerun()
            
            r[1].markdown(f"<span class='cell-text-gray'>{row['country'] or '-'}</span>", unsafe_allow_html=True)
            r[2].markdown(f"<span style='color:#047857; font-weight:700; font-size:13px;'>{row['product_interest'] or '-'}</span>", unsafe_allow_html=True)
            
            status = row['status'] or "Prospection"
            cls = "bg-green" if "Client" in status else "bg-yellow" if "Test" in status else "bg-gray"
            r[3].markdown(f"<span class='badge-base {cls}'>{status}</span>", unsafe_allow_html=True)
            
            last_c = "-"
            if row['last_action_date']:
                dt = datetime.strptime(row['last_action_date'][:10], "%Y-%m-%d")
                last_c = dt.strftime("%d %b. %y")
                color = "#ef4444" if (datetime.now() - dt).days > 30 else "#64748b"
                r[4].markdown(f"<span style='color:{color}; font-weight:700; font-size:14px;'>{last_c}</span>", unsafe_allow_html=True)
            else: r[4].write("-")
            
            r[5].markdown(f"<span class='cell-text-gray'>{row.get('last_salon') or '-'}</span>", unsafe_allow_html=True)
            
            has_s = not samples_list.empty and row['id'] in samples_list['prospect_id'].values
            if has_s: r[6].markdown("<span class='badge-base bg-blue'>🧪 En test</span>", unsafe_allow_html=True)
            else: r[6].write("-")

else:
    st.title(pg)
    st.info("Coming soon.")
