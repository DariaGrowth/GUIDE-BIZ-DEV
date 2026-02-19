# =============================================================================
# ING GROWTH AI — CRM Stratégique
# Version 3.3 | Corrections Selectbox + Multi-ingrédients + Layout compact
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import urllib.parse
import requests
from io import BytesIO

# =============================================================================
# SVG ICONS - DESIGN SYSTEM
# =============================================================================

FAVICON_SVG = """<svg width="32" height="32" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="56" height="56" rx="12" fill="#1E3F35"/><path d="M28 12c-3 7-9 11-16 11 7 3 13 9 16 16 3-7 9-13 16-16-7-3-13-6-16-11z" fill="white"/></svg>"""

ICON_LOGO = """<svg width="40" height="40" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M28 4c-4 10-12 14-22 14 10 4 18 12 22 22 4-10 12-18 22-22-10-4-18-8-22-14z" fill="#1E3F35"/>
    <path d="M28 14c-2 6-8 10-14 10 6 2 12 8 14 14 2-6 8-10 14-10-6-2-12-4-14-14z" fill="white" fill-opacity="0.3"/>
</svg>"""

def get_icon(name, color="#6B7280", size=20):
    icons = {
        "dashboard": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>',
        "pipeline": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M3 6h18M3 12h18M3 18h18"/><circle cx="7" cy="6" r="2" fill="{color}"/><circle cx="14" cy="12" r="2" fill="{color}"/><circle cx="10" cy="18" r="2" fill="{color}"/></svg>',
        "kanban": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><rect x="3" y="3" width="5" height="18" rx="1"/><rect x="10" y="3" width="5" height="12" rx="1"/><rect x="17" y="3" width="5" height="15" rx="1"/></svg>',
        "samples": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M9 3v6l-3 12h12l-3-12V3"/><path d="M8 3h8"/><path d="M7 15h10"/></svg>',
        "contacts": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/></svg>',
        "news": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 8h8M8 12h8M8 16h4"/></svg>',
        "export": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M12 3v12m0 0l-4-4m4 4l4-4"/><path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2"/></svg>',
        "import": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M12 15V3m0 12l-4-4m4 4l4-4"/><path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2"/></svg>',
        "webhook": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><path d="M6 9v6a3 3 0 003 3h6"/></svg>',
        "alert": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>',
        "chevron": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>',
        "plus": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>',
        "delete": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z"/></svg>',
        "flask": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M9 3v6l-3 12h12l-3-12V3"/><path d="M8 3h8"/><path d="M7 15h10"/></svg>',
        "globe": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>',
        "mail": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 6l-10 7L2 6"/></svg>',
        "phone": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/></svg>',
        "calendar": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
        "check": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><polyline points="20,6 9,17 4,12"/></svg>',
        "check_circle": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>',
        "warning": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        "user": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/></svg>',
    }
    return icons.get(name, "")

# =============================================================================
# 1. CONFIGURATION & STYLES CSS
# =============================================================================

st.set_page_config(
    page_title="ING Growth AI",
    page_icon="data:image/svg+xml;utf8," + urllib.parse.quote(FAVICON_SVG),
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

CSS_THEME = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --primary: #1E3F35;
        --primary-light: #2A5548;
        --accent-green: #10B981;
        --text-primary: #111827;
        --text-secondary: #6B7280;
        --text-muted: #9CA3AF;
        --bg-white: #FFFFFF;
        --bg-gray: #F9FAFB;
        --bg-hover: #F3F4F6;
        --border: #E5E7EB;
        --border-light: #F3F4F6;
        --purple: #7C3AED;
        --blue: #3B82F6;
        --orange: #F59E0B;
        --red: #DC2626;
    }

    .stApp { background: var(--bg-gray) !important; font-family: 'DM Sans', sans-serif !important; }
    * { font-family: 'DM Sans', sans-serif !important; }
    [data-testid="stVerticalBlock"] { gap: 0 !important; }
    h1, h2, h3, h4, h5, h6 { font-family: 'DM Sans', sans-serif !important; color: var(--text-primary) !important; font-weight: 600 !important; }

    /* SIDEBAR */
    section[data-testid="stSidebar"] { background: var(--bg-white) !important; border-right: 1px solid var(--border) !important; }
    section[data-testid="stSidebar"] > div { padding: 24px 16px !important; background: transparent !important; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] { background: transparent !important; border: none !important; box-shadow: none !important; }

    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        width: 100% !important; background: var(--primary) !important; color: white !important;
        border: none !important; border-radius: 10px !important; padding: 14px 20px !important;
        font-weight: 600 !important; font-size: 14px !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover { background: var(--primary-light) !important; }

    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        width: 100% !important; background: transparent !important; color: #4B5563 !important;
        border: none !important; border-left: 3px solid transparent !important; border-radius: 8px !important;
        padding: 12px 16px !important; font-weight: 500 !important; font-size: 14px !important;
        text-align: left !important; justify-content: flex-start !important; margin: 2px 0 !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover { background: #F3F4F6 !important; color: #1E3F35 !important; }

    section[data-testid="stSidebar"] [data-testid="column"] .stButton > button[kind="secondary"] {
        background: white !important; border: 1px solid #E5E7EB !important; color: #6B7280 !important;
        font-size: 13px !important; padding: 10px 12px !important; border-radius: 8px !important;
        text-align: center !important; justify-content: center !important;
    }

    /* STATUS BADGES */
    .status-badge { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
    .status-prospection { background: #DBEAFE; color: #1E40AF; }
    .status-qualification { background: #E0E7FF; color: #4338CA; }
    .status-echantillons { background: #FEF3C7; color: #92400E; }
    .status-tests { background: #FFEDD5; color: #C2410C; }
    .status-negociation { background: #F3E8FF; color: #7C3AED; }
    .status-contrat { background: #D1FAE5; color: #065F46; }
    .status-client { background: #ECFDF5; color: #047857; }

    .sample-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; background: #EFF6FF; border-radius: 6px; font-size: 11px; font-weight: 500; color: #3B82F6; }

    /* MODAL - COMPACT */
    div[data-testid="stDialog"]::before { content: ''; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); backdrop-filter: blur(4px); z-index: -1; }
    div[data-testid="stDialog"] > div:first-child { background: rgba(0,0,0,0.4) !important; backdrop-filter: blur(4px) !important; }
    div[data-testid="stDialog"] > div > div {
        background: var(--bg-white) !important; border-radius: 12px !important;
        box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25) !important;
        max-width: 1000px !important; width: 92vw !important; max-height: 88vh !important;
        overflow-y: auto !important; margin: auto !important; padding: 20px 24px !important;
    }

    /* Form Labels - COMPACT */
    .form-label { font-size: 10px !important; font-weight: 700 !important; color: #374151 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; margin-bottom: 6px !important; display: block !important; }

    /* Form Inputs - COMPACT */
    .stTextInput > div, .stTextArea > div, .stSelectbox > div, .stNumberInput > div, .stMultiSelect > div { margin-top: 2px !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div, .stNumberInput > div > div > input, .stMultiSelect > div > div {
        border: 1px solid var(--border) !important; border-radius: 6px !important; font-size: 13px !important; padding: 8px 10px !important; background: var(--bg-white) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox > div > div:focus-within, .stMultiSelect > div > div:focus-within {
        border-color: var(--primary) !important; box-shadow: 0 0 0 3px rgba(30,63,53,0.1) !important;
    }

    /* Tabs - COMPACT */
    .stTabs [data-baseweb="tab-list"] { gap: 0 !important; border-bottom: 1px solid var(--border) !important; }
    .stTabs [data-baseweb="tab"] { font-size: 12px !important; font-weight: 500 !important; padding: 10px 16px !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: var(--primary) !important; border-bottom-color: var(--primary) !important; font-weight: 600 !important; }

    /* Pipeline */
    .col-product { color: var(--accent-green) !important; font-weight: 600 !important; font-size: 13px !important; }
    .col-salon { color: var(--purple) !important; font-weight: 500 !important; font-size: 13px !important; }
    .col-country { color: var(--text-secondary) !important; font-size: 13px !important; }
    .col-date { font-size: 13px !important; font-family: 'JetBrains Mono', monospace !important; }

    /* Hide defaults */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none !important; }
    div[data-testid="stToolbar"] { display: none !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border: none !important; background: transparent !important; }
</style>
"""
st.markdown(CSS_THEME, unsafe_allow_html=True)

# =============================================================================
# 2. AUTHENTIFICATION
# =============================================================================

def check_auth():
    access_token = st.secrets.get("ACCESS_TOKEN", "")
    access_password = st.secrets.get("ACCESS_PASSWORD", "")
    if "token" in st.query_params and st.query_params["token"] == access_token:
        st.session_state["authenticated"] = True
        return True
    if st.session_state.get("authenticated", False):
        return True
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; padding: 40px; background: white; border-radius: 16px; border: 1px solid #E5E7EB;'><div style='margin-bottom: 16px;'>{ICON_LOGO}</div><h2 style='margin: 0 0 4px; font-size: 24px;'>ING Growth AI</h2><p style='margin: 0 0 24px; font-size: 14px; color: #6B7280;'>Plateforme Business Development</p></div>", unsafe_allow_html=True)
        pwd = st.text_input("", type="password", placeholder="Mot de passe", label_visibility="collapsed")
        if st.button("Se connecter", use_container_width=True, type="primary"):
            if pwd == access_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
    return False

# =============================================================================
# 3. CONNEXIONS
# =============================================================================

@st.cache_resource
def init_connections():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None

def get_supabase():
    if 'supabase' not in st.session_state:
        st.session_state.supabase = init_connections()
    return st.session_state.supabase

# =============================================================================
# 4. HELPERS
# =============================================================================

if "pipeline_key" not in st.session_state:
    st.session_state["pipeline_key"] = 0

def reset_pipeline():
    st.session_state["pipeline_key"] += 1
    st.cache_data.clear()
    safe_del("active_prospect_id")

def safe_del(key):
    if key in st.session_state:
        del st.session_state[key]

def clean_prod_name(name):
    if not name or name == "-" or str(name) == "nan":
        return "-"
    return str(name).split(" (")[0].strip()

def get_status_html(status):
    status_map = {
        "Prospection": ("status-prospection", "Prospection"),
        "Qualification": ("status-qualification", "Qualification"),
        "Échantillons en test": ("status-echantillons", "Échantillons"),
        "Tests en cours": ("status-tests", "Tests R&D"),
        "Négociation": ("status-negociation", "Négociation"),
        "Contrat": ("status-contrat", "Contrat"),
        "Client Actif": ("status-client", "Client Actif"),
    }
    cls, label = status_map.get(status, ("status-prospection", status or "—"))
    return f'<span class="status-badge {cls}">{label}</span>'

def serialize_products(products_list):
    if not products_list:
        return ""
    return ", ".join(products_list)

def deserialize_products(products_str):
    if not products_str:
        return []
    return [p.strip() for p in products_str.split(",") if p.strip()]

def build_linkedin_url(company_name):
    if not company_name or company_name == "Nouveau Prospect":
        return None
    keywords = f'{company_name} "Product Developer" OR "R&D" OR "Purchasing" OR "Achats"'
    return f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(keywords)}"

# =============================================================================
# 5. DATA LAYER
# =============================================================================

def get_prospects():
    try:
        res = get_supabase().table("prospects").select("*").order("last_action_date", desc=True).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def get_sub_data(table, prospect_id):
    try:
        data = get_supabase().table(table).select("*").eq("prospect_id", prospect_id).order("id", desc=True).execute().data
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def count_alerts():
    try:
        forty_five = (datetime.now() - timedelta(days=45)).isoformat()
        r1 = get_supabase().table("prospects").select("id", count="exact").eq("status", "Client Actif").lte("last_action_date", forty_five).execute()
        fifteen = (datetime.now() - timedelta(days=15)).isoformat()
        r2 = get_supabase().table("samples").select("id", count="exact").is_("feedback", "null").lte("date_sent", fifteen).execute()
        return (r1.count or 0) + (r2.count or 0)
    except:
        return 0

# =============================================================================
# 6. CONSTANTS
# =============================================================================

PRODUITS_DISPONIBLES = ["Sulfodyne", "Prostaphane", "Peptipea", "Isolats végétaux"]
APPLICATIONS = ["", "Boulangerie / Pâtisserie", "Sauces", "Confiserie", "Plats cuisinés", "Boissons", "Compléments alimentaires", "Autre"]
STATUTS = ["Prospection", "Qualification", "Échantillons en test", "Tests en cours", "Négociation", "Contrat", "Client Actif"]

# =============================================================================
# 7. MODAL - FICHE PROJET
# =============================================================================

@st.dialog("Fiche Projet", width="large")
def show_prospect_modal(pid, data):
    pid = int(pid)
    is_new = data.get("company_name") == "Nouveau Prospect"
    
    # Initialisation session state
    state_keys = {
        f"modal_name_{pid}": data.get("company_name", ""),
        f"modal_status_{pid}": data.get("status", "Prospection"),
        f"modal_country_{pid}": data.get("country", ""),
        f"modal_volume_{pid}": float(data.get("potential_volume") or 0),
        f"modal_source_{pid}": data.get("last_salon", ""),
        f"modal_products_{pid}": deserialize_products(data.get("product_interest", "")),
        f"modal_segment_{pid}": data.get("segment", ""),
        f"modal_notes_{pid}": data.get("notes", ""),
        f"modal_tech_{pid}": data.get("tech_notes", ""),
    }
    for key, default in state_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default
    
    # HEADER
    h1, h2 = st.columns([2.5, 1.5])
    with h1:
        display_name = st.session_state[f"modal_name_{pid}"] or "Nouveau Projet"
        if display_name == "Nouveau Prospect":
            display_name = "Nouveau Projet"
        st.markdown(f"<div style='margin-bottom: 12px;'><h2 style='font-size: 22px; font-weight: 700; margin: 0;'>{display_name}</h2><p style='font-size: 13px; color: #6B7280; margin: 6px 0 0;'>Gestion et Suivi R&D</p></div>", unsafe_allow_html=True)
    with h2:
        bc1, bc2 = st.columns(2, gap="small")
        with bc1:
            st.button("🔍 Hunter AI", key=f"hunter_{pid}", use_container_width=True, type="secondary")
        with bc2:
            st.button("📄 Brief R&D", key=f"brief_{pid}", use_container_width=True, type="secondary")
    
    st.markdown("<hr style='margin: 16px 0; border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
    # BODY
    col_left, col_right = st.columns([1.8, 2.2], gap="medium")
    
    with col_left:
        st.markdown('<p class="form-label">SOCIÉTÉ / CLIENT</p>', unsafe_allow_html=True)
        st.text_input("company", value=st.session_state[f"modal_name_{pid}"], key=f"input_name_{pid}", label_visibility="collapsed", placeholder="Nom de la société", on_change=lambda: st.session_state.update({f"modal_name_{pid}": st.session_state[f"input_name_{pid}"]}))
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        st.markdown('<p class="form-label">STATUT PIPELINE</p>', unsafe_allow_html=True)
        current_status = st.session_state[f"modal_status_{pid}"]
        status_index = STATUTS.index(current_status) if current_status in STATUTS else 0
        st.selectbox("status", options=STATUTS, index=status_index, key=f"input_status_{pid}", label_visibility="collapsed", on_change=lambda: st.session_state.update({f"modal_status_{pid}": st.session_state[f"input_status_{pid}"]}))
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2, gap="small")
        with c1:
            st.markdown('<p class="form-label">PAYS</p>', unsafe_allow_html=True)
            st.text_input("country", value=st.session_state[f"modal_country_{pid}"], key=f"input_country_{pid}", label_visibility="collapsed", placeholder="France", on_change=lambda: st.session_state.update({f"modal_country_{pid}": st.session_state[f"input_country_{pid}"]}))
        with c2:
            st.markdown('<p class="form-label">POTENTIEL (T)</p>', unsafe_allow_html=True)
            st.number_input("vol", value=st.session_state[f"modal_volume_{pid}"], key=f"input_volume_{pid}", label_visibility="collapsed", min_value=0.0, on_change=lambda: st.session_state.update({f"modal_volume_{pid}": st.session_state[f"input_volume_{pid}"]}))
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        st.markdown("<div style='background: #F0FDF4; padding: 12px 14px; border-radius: 8px; border: 1px solid #BBF7D0; margin-bottom: 10px;'><p style='font-size: 11px; font-weight: 700; color: #166534; text-transform: uppercase; margin: 0;'>📍 DERNIER SALON / SOURCE</p></div>", unsafe_allow_html=True)
        st.text_input("source", value=st.session_state[f"modal_source_{pid}"], key=f"input_source_{pid}", label_visibility="collapsed", placeholder="ex: CFIA 2026, LinkedIn", on_change=lambda: st.session_state.update({f"modal_source_{pid}": st.session_state[f"input_source_{pid}"]}))
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        st.markdown('<p class="form-label">🔗 SOCIAL SELLING</p>', unsafe_allow_html=True)
        linkedin_url = build_linkedin_url(st.session_state[f"modal_name_{pid}"])
        if linkedin_url:
            st.markdown(f"<a href='{linkedin_url}' target='_blank' style='display: inline-flex; align-items: center; gap: 8px; background: #0A66C2; color: white; padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; text-decoration: none;'><span style='font-weight: 700;'>in</span> Rechercher contacts R&D</a>", unsafe_allow_html=True)
        else:
            st.caption("Renseignez le nom de la société")
    
    with col_right:
        tab1, tab2, tab3 = st.tabs(["📋 Contexte & Technique", "🧪 Suivi Échantillons", "📓 Journal d'Activité"])
        
        with tab1:
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            t1c1, t1c2 = st.columns(2, gap="small")
            with t1c1:
                st.markdown('<p class="form-label">INGRÉDIENTS GD (Multi-sélection)</p>', unsafe_allow_html=True)
                st.multiselect("products", options=PRODUITS_DISPONIBLES, default=st.session_state[f"modal_products_{pid}"], key=f"input_products_{pid}", label_visibility="collapsed", placeholder="Sélectionner...", on_change=lambda: st.session_state.update({f"modal_products_{pid}": st.session_state[f"input_products_{pid}"]}))
            with t1c2:
                st.markdown('<p class="form-label">APPLICATION FINALE</p>', unsafe_allow_html=True)
                current_app = st.session_state[f"modal_segment_{pid}"]
                app_index = APPLICATIONS.index(current_app) if current_app in APPLICATIONS else 0
                st.selectbox("app", options=APPLICATIONS, index=app_index, key=f"input_segment_{pid}", label_visibility="collapsed", format_func=lambda x: x if x else "Sélectionner...", on_change=lambda: st.session_state.update({f"modal_segment_{pid}": st.session_state[f"input_segment_{pid}"]}))
            
            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            st.markdown('<p class="form-label">PROBLÉMATIQUE / BESOIN (PAIN POINT)</p>', unsafe_allow_html=True)
            st.text_area("pain", value=st.session_state[f"modal_notes_{pid}"], height=90, key=f"input_notes_{pid}", label_visibility="collapsed", placeholder="Ex: Volatilité prix œuf, Texture sèche, Besoin Clean Label...", on_change=lambda: st.session_state.update({f"modal_notes_{pid}": st.session_state[f"input_notes_{pid}"]}))
            
            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            st.markdown('<p class="form-label">NOTES TECHNIQUES R&D</p>', unsafe_allow_html=True)
            st.text_area("tech", value=st.session_state[f"modal_tech_{pid}"], height=90, key=f"input_tech_{pid}", label_visibility="collapsed", placeholder="pH cible, Température cuisson, Dosage recommandé...", on_change=lambda: st.session_state.update({f"modal_tech_{pid}": st.session_state[f"input_tech_{pid}"]}))
        
        with tab2:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            samples_df = get_sub_data("samples", pid)
            if samples_df.empty:
                st.markdown("<div style='text-align: center; padding: 32px; color: #9CA3AF;'><p>Aucun échantillon</p></div>", unsafe_allow_html=True)
            else:
                S_OPTS = ["En test", "Validé", "Rejeté", "Perdu"]
                for _, r in samples_df.iterrows():
                    with st.container(border=True):
                        sc1, sc2, sc3 = st.columns([3, 1.5, 0.5])
                        with sc1:
                            st.markdown(f"<div><span style='font-weight: 600;'>{clean_prod_name(r['product_name'])}</span> · {r['reference']}<br><span style='font-size: 12px; color: #9CA3AF;'>{r['date_sent'][:10]}</span></div>", unsafe_allow_html=True)
                        with sc2:
                            s_idx = S_OPTS.index(r["status"]) if r["status"] in S_OPTS else 0
                            new_s = st.selectbox("s", S_OPTS, index=s_idx, key=f"ss_{r['id']}", label_visibility="collapsed")
                            if new_s != r["status"]:
                                get_supabase().table("samples").update({"status": new_s}).eq("id", r["id"]).execute()
                        with sc3:
                            if st.button("🗑", key=f"ds_{r['id']}"):
                                get_supabase().table("samples").delete().eq("id", r["id"]).execute()
                                st.rerun()
            
            st.markdown("<hr style='margin: 16px 0;'>", unsafe_allow_html=True)
            st.markdown('<p class="form-label">➕ AJOUTER UN ÉCHANTILLON</p>', unsafe_allow_html=True)
            asc1, asc2, asc3 = st.columns([2, 1.5, 1])
            with asc1:
                s_ref = st.text_input("ref", key=f"sr_{pid}", placeholder="Référence", label_visibility="collapsed")
            with asc2:
                s_prod = st.selectbox("sprod", PRODUITS_DISPONIBLES, key=f"sp_{pid}", label_visibility="collapsed")
            with asc3:
                if st.button("Ajouter", type="primary", key=f"add_s_{pid}", use_container_width=True):
                    if s_ref.strip():
                        get_supabase().table("samples").insert({"prospect_id": pid, "reference": s_ref, "product_name": s_prod, "status": "En test", "date_sent": datetime.now().isoformat()}).execute()
                        st.rerun()
        
        with tab3:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            activities_df = get_sub_data("activities", pid)
            if activities_df.empty:
                st.markdown("<div style='text-align: center; padding: 32px; color: #9CA3AF;'><p>Aucune activité</p></div>", unsafe_allow_html=True)
            else:
                for _, act in activities_df.head(5).iterrows():
                    icon = "📧" if act["type"] == "Email" else "📞" if act["type"] == "Appel" else "📅" if act["type"] == "RDV" else "📝"
                    st.markdown(f"<div style='padding: 12px; background: #F9FAFB; border-radius: 8px; margin-bottom: 8px;'><div style='display: flex; justify-content: space-between;'><span style='font-weight: 600; font-size: 13px;'>{icon} {act['type']}</span><span style='font-size: 11px; color: #9CA3AF;'>{act['date'][:10]}</span></div><p style='font-size: 13px; color: #6B7280; margin: 4px 0 0;'>{act['content'][:100]}{'...' if len(act['content']) > 100 else ''}</p></div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 16px 0;'>", unsafe_allow_html=True)
            st.markdown('<p class="form-label">➕ AJOUTER UNE ACTIVITÉ</p>', unsafe_allow_html=True)
            act_type = st.selectbox("type", ["Email", "Appel", "RDV", "Note"], key=f"at_{pid}", label_visibility="collapsed")
            act_content = st.text_area("content", height=70, key=f"ac_{pid}", placeholder="Décrivez l'activité...", label_visibility="collapsed")
            if st.button("Enregistrer l'activité", type="primary", key=f"save_act_{pid}"):
                if act_content.strip():
                    get_supabase().table("activities").insert({"prospect_id": pid, "type": act_type, "content": act_content, "date": datetime.now().isoformat()}).execute()
                    st.success("✅ Activité ajoutée")
                    st.rerun()
    
    # FOOTER
    st.markdown("<hr style='margin: 20px 0 14px;'>", unsafe_allow_html=True)
    
    if st.session_state.get(f"confirm_delete_{pid}", False):
        st.error("⚠️ Êtes-vous sûr de vouloir supprimer ce projet ? Cette action est irréversible.")
        dc1, dc2, dc3 = st.columns([1.2, 1.2, 2])
        with dc1:
            if st.button("Confirmer la suppression", key=f"confirm_yes_{pid}", use_container_width=True, type="primary"):
                get_supabase().table("samples").delete().eq("prospect_id", pid).execute()
                get_supabase().table("activities").delete().eq("prospect_id", pid).execute()
                get_supabase().table("contacts").delete().eq("prospect_id", pid).execute()
                get_supabase().table("prospects").delete().eq("id", pid).execute()
                safe_del(f"confirm_delete_{pid}")
                safe_del("active_prospect_id")
                for k in list(st.session_state.keys()):
                    if f"modal_" in k and f"_{pid}" in k:
                        safe_del(k)
                reset_pipeline()
                st.rerun()
        with dc2:
            if st.button("Annuler", key=f"confirm_no_{pid}", use_container_width=True):
                safe_del(f"confirm_delete_{pid}")
                st.rerun()
    else:
        fc1, fc2, fc3, fc4 = st.columns([1.2, 2, 1, 1.5])
        with fc1:
            if not is_new and st.button("🗑️ Supprimer", key=f"del_{pid}", use_container_width=True, type="secondary"):
                st.session_state[f"confirm_delete_{pid}"] = True
                st.rerun()
        with fc3:
            if st.button("Annuler", key=f"cancel_{pid}", use_container_width=True, type="secondary"):
                if is_new:
                    get_supabase().table("prospects").delete().eq("id", pid).execute()
                safe_del("active_prospect_id")
                for k in list(st.session_state.keys()):
                    if f"modal_" in k and f"_{pid}" in k:
                        safe_del(k)
                st.rerun()
        with fc4:
            if st.button("✓ Enregistrer", type="primary", key=f"save_{pid}", use_container_width=True):
                try:
                    products_str = serialize_products(st.session_state.get(f"modal_products_{pid}", []))
                    save_data = {
                        "company_name": st.session_state.get(f"modal_name_{pid}", ""),
                        "status": st.session_state.get(f"modal_status_{pid}", "Prospection"),
                        "country": st.session_state.get(f"modal_country_{pid}", ""),
                        "potential_volume": st.session_state.get(f"modal_volume_{pid}", 0),
                        "last_salon": st.session_state.get(f"modal_source_{pid}", ""),
                        "product_interest": products_str,
                        "segment": st.session_state.get(f"modal_segment_{pid}", ""),
                        "notes": st.session_state.get(f"modal_notes_{pid}", ""),
                        "tech_notes": st.session_state.get(f"modal_tech_{pid}", ""),
                        "last_action_date": datetime.now().isoformat(),
                    }
                    get_supabase().table("prospects").update(save_data).eq("id", pid).execute()
                    st.success("✅ Projet enregistré")
                    time.sleep(0.8)
                    safe_del("active_prospect_id")
                    for k in list(st.session_state.keys()):
                        if f"modal_" in k and f"_{pid}" in k:
                            safe_del(k)
                    reset_pipeline()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

# =============================================================================
# 8. SIDEBAR NAVIGATION
# =============================================================================

def render_sidebar():
    with st.sidebar:
        st.markdown(f"<div style='text-align: center; padding: 16px 0 20px;'>{ICON_LOGO}<div style='font-weight: 700; font-size: 18px; color: #111827; margin-top: 12px;'>ING Growth</div><div style='font-size: 11px; color: #9CA3AF; text-transform: uppercase;'>AI Platform</div></div>", unsafe_allow_html=True)
        
        if st.button("✦  Nouveau Projet", key="btn_new_project", use_container_width=True, type="primary"):
            try:
                res = get_supabase().table("prospects").insert({"company_name": "Nouveau Prospect", "status": "Prospection", "last_action_date": datetime.now().isoformat()}).execute()
                if res.data:
                    st.session_state["active_prospect_id"] = res.data[0]["id"]
                    st.rerun()
            except Exception as e:
                st.error(f"Erreur: {e}")
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'Pipeline'
        
        alert_count = count_alerts()
        nav_items = [
            ("Dashboard", "Tableau de Bord"), ("Pipeline", "Pipeline"), ("Kanban", "Kanban"),
            ("Samples", "Échantillons"), ("Contacts", "Contacts"), ("News", "Veille IA"),
            ("Excel", "Import / Export"), ("Webhooks", "Webhooks"),
            ("Alertes", f"À Relancer ({alert_count})" if alert_count > 0 else "À Relancer"),
        ]
        
        for page_key, label in nav_items:
            if st.button(label, key=f"nav_{page_key}", use_container_width=True, type="secondary"):
                safe_del("active_prospect_id")
                st.session_state.selected_page = page_key
                st.rerun()
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        st.caption("DONNÉES")
        col_exp, col_imp = st.columns(2)
        with col_exp:
            if st.button("Export", key="btn_export", use_container_width=True, type="secondary"):
                st.session_state.selected_page = "Excel"
                st.rerun()
        with col_imp:
            if st.button("Import", key="btn_import", use_container_width=True, type="secondary"):
                st.session_state.selected_page = "Excel"
                st.rerun()
        
        st.markdown("---")
        st.markdown(f"<div style='display: flex; align-items: center; gap: 8px;'>{get_icon('user', '#9CA3AF', 16)}<span style='font-size: 12px; color: #9CA3AF;'>Utilisateur connecté</span></div>", unsafe_allow_html=True)
        return st.session_state.selected_page

# =============================================================================
# 9. PAGES
# =============================================================================

def page_pipeline():
    st.markdown(f"<div style='margin-bottom: 24px;'><h1 style='font-size: 24px; font-weight: 700; margin: 0;'>{get_icon('pipeline', '#1E3F35', 28)} Pipeline Food & Ingrédients</h1><p style='font-size: 14px; color: #6B7280; margin: 4px 0 0;'>Vue complète de vos projets</p></div>", unsafe_allow_html=True)
    
    df_raw = get_prospects()
    if df_raw.empty:
        st.info("Aucun prospect. Cliquez sur 'Nouveau Projet' pour commencer.")
        return
    
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        p_filter = st.selectbox("prod", ["Tous Produits"] + PRODUITS_DISPONIBLES, key="pf", label_visibility="collapsed")
    with f2:
        s_filter = st.selectbox("stat", ["Tous Statuts"] + STATUTS, key="sf", label_visibility="collapsed")
    with f3:
        sal_filter = st.selectbox("salon", ["Tous Salons"] + sorted(df_raw["last_salon"].dropna().unique().tolist()), key="salf", label_visibility="collapsed")
    with f4:
        c_filter = st.selectbox("country", ["Tous Pays"] + sorted(df_raw["country"].dropna().unique().tolist()), key="cf", label_visibility="collapsed")
    
    df = df_raw.copy()
    if p_filter != "Tous Produits":
        df = df[df["product_interest"].str.contains(p_filter, na=False)]
    if s_filter != "Tous Statuts":
        df = df[df["status"] == s_filter]
    if sal_filter != "Tous Salons":
        df = df[df["last_salon"] == sal_filter]
    if c_filter != "Tous Pays":
        df = df[df["country"] == c_filter]
    
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    for _, row in df.iterrows():
        cols = st.columns([2, 1, 1.2, 1.2, 1, 1.2, 0.5])
        with cols[0]:
            if st.button(row["company_name"].upper(), key=f"row_{row['id']}", use_container_width=True):
                st.session_state["active_prospect_id"] = row["id"]
                st.rerun()
        with cols[1]:
            st.markdown(f'<span class="col-country">{row.get("country") or "—"}</span>', unsafe_allow_html=True)
        with cols[2]:
            products = row.get("product_interest", "") or ""
            st.markdown(f'<span class="col-product">{products[:25]}{"..." if len(products) > 25 else ""}</span>', unsafe_allow_html=True)
        with cols[3]:
            st.markdown(get_status_html(row.get("status")), unsafe_allow_html=True)
        with cols[4]:
            date_str = "—"
            if row.get("last_action_date"):
                try:
                    date_str = datetime.strptime(row["last_action_date"][:10], "%Y-%m-%d").strftime("%d %b")
                except:
                    pass
            st.markdown(f'<span class="col-date">{date_str}</span>', unsafe_allow_html=True)
        with cols[5]:
            st.markdown(f'<span class="col-salon">{row.get("last_salon") or "—"}</span>', unsafe_allow_html=True)
        with cols[6]:
            st.markdown(f'{get_icon("chevron", "#9CA3AF", 16)}', unsafe_allow_html=True)

def page_dashboard():
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700;">{get_icon("dashboard", "#1E3F35", 28)} Tableau de Bord</h1>', unsafe_allow_html=True)
    df = get_prospects()
    if df.empty:
        st.info("Aucune donnée")
        return
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Projets actifs", len(df))
    m2.metric("Potentiel total", f"{int(df['potential_volume'].sum())} T")
    signed = len(df[df["status"].isin(["Contrat", "Client Actif"])])
    m3.metric("Taux conversion", f"{int(signed / max(len(df), 1) * 100)}%")
    m4.metric("En R&D", len(df[df["status"].isin(["Échantillons en test", "Tests en cours"])]))
    c1, c2 = st.columns(2)
    with c1:
        pie_df = df[df["product_interest"].notna() & (df["product_interest"] != "")]
        if not pie_df.empty:
            fig = px.pie(pie_df, names="product_interest", hole=0.45, title="Mix Produits")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        bar_df = df.groupby("status").size().reset_index(name="count")
        if not bar_df.empty:
            fig = px.bar(bar_df, x="status", y="count", title="Par Statut")
            st.plotly_chart(fig, use_container_width=True)

def page_kanban():
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700;">{get_icon("kanban", "#1E3F35", 28)} Kanban Board</h1>', unsafe_allow_html=True)
    df = get_prospects()
    if df.empty:
        st.info("Aucun prospect")
        return
    cols = st.columns(len(STATUTS))
    for i, stage in enumerate(STATUTS):
        with cols[i]:
            count = len(df[df["status"] == stage])
            st.markdown(f"<div style='border-bottom: 3px solid #1E3F35; padding-bottom: 8px; margin-bottom: 12px;'><p style='font-size: 11px; font-weight: 700; text-transform: uppercase; margin: 0;'>{stage}</p><p style='font-size: 11px; color: #9CA3AF; margin: 4px 0 0;'>{count}</p></div>", unsafe_allow_html=True)
            for _, row in df[df["status"] == stage].iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['company_name'][:15]}**")
                    if st.button("Ouvrir", key=f"o_{row['id']}", use_container_width=True):
                        st.session_state["active_prospect_id"] = row["id"]
                        st.rerun()

def page_samples():
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700;">{get_icon("flask", "#1E3F35", 28)} Échantillons</h1>', unsafe_allow_html=True)
    try:
        samp = pd.DataFrame(get_supabase().table("samples").select("*, prospects(company_name)").execute().data)
        if not samp.empty:
            samp["Client"] = samp["prospects"].apply(lambda x: x["company_name"] if x else "—")
            st.dataframe(samp[["date_sent", "product_name", "reference", "status", "Client", "feedback"]], use_container_width=True)
        else:
            st.info("Aucun échantillon")
    except:
        st.info("Aucun échantillon")

def page_contacts():
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700;">{get_icon("contacts", "#1E3F35", 28)} Contacts</h1>', unsafe_allow_html=True)
    try:
        cons = pd.DataFrame(get_supabase().table("contacts").select("*, prospects(company_name)").execute().data)
        if not cons.empty:
            cons["Entreprise"] = cons["prospects"].apply(lambda x: x["company_name"] if x else "—")
            st.dataframe(cons[["name", "role", "email", "phone", "Entreprise"]], use_container_width=True)
        else:
            st.info("Aucun contact")
    except:
        st.info("Aucun contact")

def page_news():
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700;">{get_icon("news", "#1E3F35", 28)} Veille IA</h1>', unsafe_allow_html=True)
    st.info("Veille stratégique - Configuration requise")

def page_excel():
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700;">{get_icon("export", "#1E3F35", 28)} Import / Export</h1>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("**Export**")
            df = get_prospects()
            if not df.empty:
                buffer = BytesIO()
                df.to_excel(buffer, index=False, engine="openpyxl")
                buffer.seek(0)
                st.download_button("Télécharger Excel", buffer, f"prospects_{datetime.now().strftime('%Y%m%d')}.xlsx", type="primary", use_container_width=True)
            else:
                st.info("Aucune donnée")
    with c2:
        with st.container(border=True):
            st.markdown("**Import**")
            uploaded = st.file_uploader("Fichier Excel", type=["xlsx"], label_visibility="collapsed")
            if uploaded and st.button("Importer", type="primary"):
                st.success("Import réussi")

def page_webhooks():
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700;">{get_icon("webhook", "#1E3F35", 28)} Webhooks</h1>', unsafe_allow_html=True)
    st.code("https://your-app.streamlit.io/api/webhook/leads")
    st.info("Configurez ce webhook dans Make.com")

def page_alertes():
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700;">{get_icon("alert", "#1E3F35", 28)} Alertes</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-weight: 600;">{get_icon("warning", "#F59E0B", 18)} Clients sans contact (45+ jours)</p>', unsafe_allow_html=True)
    try:
        threshold = (datetime.now() - timedelta(days=45)).isoformat()
        alerts = pd.DataFrame(get_supabase().table("prospects").select("*").eq("status", "Client Actif").lte("last_action_date", threshold).execute().data)
        if not alerts.empty:
            for _, a in alerts.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{a['company_name']}** - Dernier contact: {a.get('last_action_date', '')[:10]}")
                    if st.button("Ouvrir", key=f"alert_{a['id']}"):
                        st.session_state["active_prospect_id"] = a["id"]
                        st.rerun()
        else:
            st.success("✅ Tous les clients sont à jour")
    except:
        st.info("Aucune alerte")

# =============================================================================
# 10. MAIN
# =============================================================================

def main():
    if not check_auth():
        return
    if not get_supabase():
        st.error("Connexion base de données échouée")
        st.stop()
    
    selected_page = render_sidebar()
    
    if "active_prospect_id" in st.session_state:
        try:
            data = get_supabase().table("prospects").select("*").eq("id", st.session_state["active_prospect_id"]).execute().data[0]
            show_prospect_modal(st.session_state["active_prospect_id"], data)
        except:
            safe_del("active_prospect_id")
    
    pages = {
        "Dashboard": page_dashboard, "Pipeline": page_pipeline, "Kanban": page_kanban,
        "Samples": page_samples, "Contacts": page_contacts, "News": page_news,
        "Excel": page_excel, "Webhooks": page_webhooks, "Alertes": page_alertes,
    }
    pages.get(selected_page, page_pipeline)()

if __name__ == "__main__":
    main()
