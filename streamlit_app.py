# =============================================================================
# ING GROWTH AI — CRM Stratégique
# Version 3.0 | UI/UX Optimisée | Pixel Perfect Design
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

ICON_LOGO = """<svg width="40" height="40" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M28 4c-4 10-12 14-22 14 10 4 18 12 22 22 4-10 12-18 22-22-10-4-18-8-22-14z" fill="#1E3F35"/>
    <path d="M28 14c-2 6-8 10-14 10 6 2 12 8 14 14 2-6 8-10 14-10-6-2-12-4-14-14z" fill="white" fill-opacity="0.3"/>
</svg>"""

# Navigation Icons (20x20, stroke-based)
def get_icon(name, color="#6B7280"):
    icons = {
        "dashboard": f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>',
        "pipeline": f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M3 6h18M3 12h18M3 18h18"/><circle cx="7" cy="6" r="2" fill="{color}"/><circle cx="14" cy="12" r="2" fill="{color}"/><circle cx="10" cy="18" r="2" fill="{color}"/></svg>',
        "kanban": f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><rect x="3" y="3" width="5" height="18" rx="1"/><rect x="10" y="3" width="5" height="12" rx="1"/><rect x="17" y="3" width="5" height="15" rx="1"/></svg>',
        "samples": f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M9 3v6l-3 12h12l-3-12V3"/><path d="M8 3h8"/><path d="M7 15h10"/></svg>',
        "contacts": f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/></svg>',
        "news": f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M4 4h16v16H4z"/><path d="M8 8h8M8 12h8M8 16h4"/></svg>',
        "export": f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M12 3v12m0 0l-4-4m4 4l4-4"/><path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2"/></svg>',
        "webhook": f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><path d="M6 9v6a3 3 0 003 3h6"/></svg>',
        "alert": f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M12 3v1m0 16v1m-8-9H3m18 0h-1m-2.5-6.5l-.7.7m-10.6 10.6l-.7.7m0-12l.7.7m10.6 10.6l.7.7"/><circle cx="12" cy="12" r="4"/></svg>',
        "chevron": f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>',
        "flask": f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="1.5"><path d="M9 3v6l-4 10a1 1 0 001 1h12a1 1 0 001-1l-4-10V3"/><path d="M8 3h8"/></svg>',
        "plus": f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>',
        "delete": f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="1.5"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z"/></svg>',
    }
    return icons.get(name, "")

# =============================================================================
# 1. CONFIGURATION & STYLES CSS
# =============================================================================

st.set_page_config(
    page_title="ING Growth AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

# CSS OPTIMISÉ - PIXEL PERFECT
CSS_THEME = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --primary: #1E3F35;
        --primary-light: #2A5548;
        --accent-green: #10B981;
        --accent-neon: #00FF41;
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

    /* ══════════════════════════════════════════════════════════
       BASE RESET
    ══════════════════════════════════════════════════════════ */
    .stApp {
        background: var(--bg-gray) !important;
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    * { font-family: 'DM Sans', sans-serif !important; }
    
    [data-testid="stVerticalBlock"] { gap: 0 !important; }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'DM Sans', sans-serif !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    /* ══════════════════════════════════════════════════════════
       SIDEBAR - CLEAN FLOATING DESIGN
    ══════════════════════════════════════════════════════════ */
    section[data-testid="stSidebar"] {
        background: var(--bg-white) !important;
        border-right: 1px solid var(--border) !important;
        padding: 0 !important;
    }
    
    section[data-testid="stSidebar"] > div {
        padding: 24px 16px !important;
        background: transparent !important;
    }

    /* Remove ALL green backgrounds and borders from sidebar */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"],
    section[data-testid="stSidebar"] .stButton,
    section[data-testid="stSidebar"] [data-testid="column"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* ── NOUVEAU PROJET BUTTON ── */
    .new-project-btn button {
        width: 100% !important;
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 20px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    .new-project-btn button:hover {
        background: var(--primary-light) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(30,63,53,0.15) !important;
    }

    /* ── NAV ITEMS - FLOATING STYLE ── */
    .nav-item {
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        padding: 10px 12px !important;
        margin: 2px 0 !important;
        border-radius: 8px !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        background: transparent !important;
        border: none !important;
        position: relative !important;
    }
    
    .nav-item:hover {
        background: var(--bg-hover) !important;
    }
    
    .nav-item:hover .nav-icon svg,
    .nav-item:hover .nav-text {
        color: var(--primary) !important;
        stroke: var(--primary) !important;
    }
    
    .nav-item.active {
        background: #ECFDF5 !important;
    }
    
    .nav-item.active::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 20px;
        background: var(--accent-green);
        border-radius: 0 2px 2px 0;
    }
    
    .nav-item.active .nav-icon svg,
    .nav-item.active .nav-text {
        color: var(--primary) !important;
        stroke: var(--primary) !important;
    }
    
    .nav-text {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        transition: color 0.15s ease !important;
    }
    
    .nav-icon {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 20px !important;
        height: 20px !important;
    }

    /* Sidebar section titles */
    .sidebar-section-title {
        font-size: 11px !important;
        font-weight: 600 !important;
        color: var(--text-muted) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding: 16px 12px 8px !important;
        margin: 0 !important;
    }

    /* Sidebar buttons (Export/Import) */
    .sidebar-action-btn button {
        background: var(--bg-white) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 8px 12px !important;
        transition: all 0.15s ease !important;
    }
    
    .sidebar-action-btn button:hover {
        background: var(--bg-hover) !important;
        border-color: var(--primary) !important;
        color: var(--primary) !important;
    }

    /* ══════════════════════════════════════════════════════════
       PIPELINE - TABLE DESIGN
    ══════════════════════════════════════════════════════════ */
    .pipeline-container {
        background: var(--bg-white);
        border-radius: 12px;
        border: 1px solid var(--border);
        overflow: hidden;
    }

    .pipeline-header {
        padding: 20px 24px;
        border-bottom: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .pipeline-title {
        font-size: 20px !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        margin: 0 !important;
    }

    .filter-bar {
        display: flex;
        gap: 12px;
        padding: 16px 24px;
        background: var(--bg-gray);
        border-bottom: 1px solid var(--border);
    }

    .filter-select {
        background: var(--bg-white) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        font-size: 13px !important;
        color: var(--text-secondary) !important;
    }

    /* Table Headers */
    .table-header {
        display: grid;
        grid-template-columns: 2fr 1fr 1.2fr 1.2fr 1fr 1.2fr 0.8fr 50px;
        padding: 12px 24px;
        background: var(--bg-gray);
        border-bottom: 1px solid var(--border);
    }

    .table-header-cell {
        font-size: 11px !important;
        font-weight: 600 !important;
        color: var(--text-muted) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* Table Rows */
    .table-row {
        display: grid;
        grid-template-columns: 2fr 1fr 1.2fr 1.2fr 1fr 1.2fr 0.8fr 50px;
        padding: 16px 24px;
        border-bottom: 1px solid var(--border-light);
        align-items: center;
        transition: background 0.15s ease;
    }

    .table-row:hover {
        background: var(--bg-hover);
    }

    .table-row:last-child {
        border-bottom: none;
    }

    /* Company name - UPPERCASE BOLD */
    .company-name {
        font-weight: 700 !important;
        font-size: 14px !important;
        color: var(--text-primary) !important;
        text-transform: uppercase !important;
        cursor: pointer;
        transition: color 0.15s ease;
    }

    .company-name:hover {
        color: var(--primary) !important;
    }

    /* Column colors */
    .col-product {
        color: var(--accent-green) !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }

    .col-salon {
        color: var(--purple) !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }

    .col-country {
        color: var(--text-secondary) !important;
        font-size: 13px !important;
    }

    .col-date {
        font-size: 13px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Chevron */
    .row-chevron {
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        opacity: 0.4;
        transition: opacity 0.15s ease;
    }

    .table-row:hover .row-chevron {
        opacity: 1;
    }

    /* ══════════════════════════════════════════════════════════
       STATUS BADGES - PASTEL PILLS
    ══════════════════════════════════════════════════════════ */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        white-space: nowrap;
    }

    .status-prospection {
        background: #DBEAFE;
        color: #1E40AF;
    }

    .status-qualification {
        background: #E0E7FF;
        color: #4338CA;
    }

    .status-echantillons {
        background: #FEF3C7;
        color: #92400E;
    }

    .status-tests {
        background: #FFEDD5;
        color: #C2410C;
    }

    .status-negociation {
        background: #F3E8FF;
        color: #7C3AED;
    }

    .status-contrat {
        background: #D1FAE5;
        color: #065F46;
    }

    .status-client {
        background: #ECFDF5;
        color: #047857;
    }

    /* Sample badge */
    .sample-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 8px;
        background: #EFF6FF;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
        color: #3B82F6;
    }

    /* ══════════════════════════════════════════════════════════
       MODAL - FICHE PROJET
    ══════════════════════════════════════════════════════════ */
    div[data-testid="stDialog"] {
        background: var(--bg-white) !important;
    }

    div[data-testid="stDialog"] > div {
        padding: 0 !important;
        max-width: 1000px !important;
    }

    .modal-header {
        padding: 24px 32px;
        border-bottom: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }

    .modal-title {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        margin: 0 0 4px 0 !important;
    }

    .modal-subtitle {
        font-size: 14px !important;
        color: var(--text-secondary) !important;
        margin: 0 !important;
    }

    .modal-actions {
        display: flex;
        gap: 8px;
    }

    .modal-body {
        padding: 24px 32px;
        display: grid;
        grid-template-columns: 1fr 1.5fr;
        gap: 32px;
    }

    .modal-footer {
        padding: 16px 32px;
        border-top: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: var(--bg-gray);
    }

    /* Form Labels */
    .form-label {
        font-size: 11px !important;
        font-weight: 600 !important;
        color: var(--text-muted) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.3px !important;
        margin-bottom: 6px !important;
        display: block !important;
    }

    /* Form Inputs */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox > div > div {
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        padding: 10px 12px !important;
        background: var(--bg-white) !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(30,63,53,0.1) !important;
        outline: none !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important;
        border-bottom: 1px solid var(--border) !important;
        background: transparent !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 13px !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        padding: 12px 20px !important;
        border-bottom: 2px solid transparent !important;
        background: transparent !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--primary) !important;
        border-bottom-color: var(--primary) !important;
        font-weight: 600 !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
        background: var(--bg-hover) !important;
    }

    /* ══════════════════════════════════════════════════════════
       BUTTONS
    ══════════════════════════════════════════════════════════ */
    .btn-primary {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.15s ease !important;
    }

    .btn-primary:hover {
        background: var(--primary-light) !important;
        transform: translateY(-1px) !important;
    }

    .btn-secondary {
        background: var(--bg-white) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.15s ease !important;
    }

    .btn-secondary:hover {
        background: var(--bg-hover) !important;
        border-color: var(--text-muted) !important;
    }

    .btn-danger {
        background: #FEF2F2 !important;
        color: var(--red) !important;
        border: 1px solid #FECACA !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.15s ease !important;
    }

    .btn-danger:hover {
        background: #FEE2E2 !important;
        border-color: var(--red) !important;
    }

    .btn-action {
        background: #F0FDF4 !important;
        color: var(--accent-green) !important;
        border: 1px solid #BBF7D0 !important;
        border-radius: 6px !important;
        padding: 6px 12px !important;
        font-weight: 500 !important;
        font-size: 12px !important;
    }

    /* ══════════════════════════════════════════════════════════
       METRICS & CARDS
    ══════════════════════════════════════════════════════════ */
    [data-testid="stMetric"] {
        background: var(--bg-white) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 12px !important;
        font-weight: 600 !important;
        color: var(--text-muted) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* Cards */
    .card {
        background: var(--bg-white);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
    }

    .card-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 12px;
    }

    /* ══════════════════════════════════════════════════════════
       HIDE STREAMLIT DEFAULTS
    ══════════════════════════════════════════════════════════ */
    #MainMenu, footer, header { visibility: hidden; }
    
    .stDeployButton { display: none !important; }
    
    div[data-testid="stToolbar"] { display: none !important; }

    /* Remove default button outlines */
    button:focus, button:focus-visible {
        outline: none !important;
        box-shadow: none !important;
    }

    /* Streamlit container borders - remove */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
</style>
"""

st.markdown(CSS_THEME, unsafe_allow_html=True)

# =============================================================================
# 2. AUTHENTIFICATION
# =============================================================================

def check_auth():
    access_token = st.secrets.get("ACCESS_TOKEN", "")
    access_password = st.secrets.get("ACCESS_PASSWORD", "")

    if "token" in st.query_params:
        if st.query_params["token"] == access_token:
            st.session_state["authenticated"] = True
            return True

    if st.session_state.get("authenticated", False):
        return True

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='text-align: center; padding: 40px; background: white; border-radius: 16px; border: 1px solid #E5E7EB;'>"
            f"<div style='margin-bottom: 16px;'>{ICON_LOGO}</div>"
            f"<h2 style='margin: 0 0 4px; font-size: 24px; font-weight: 700; color: #111827;'>ING Growth AI</h2>"
            f"<p style='margin: 0 0 24px; font-size: 14px; color: #6B7280;'>Plateforme Business Development</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        pwd = st.text_input("", type="password", placeholder="Entrez votre mot de passe", label_visibility="collapsed")
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
    """Retourne le HTML du badge de statut avec couleurs pastel"""
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

# =============================================================================
# 5. DATA LAYER
# =============================================================================

def get_prospects():
    try:
        res = get_supabase().table("prospects").select("*").order("last_action_date", desc=True).execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

def get_sub_data(table, prospect_id):
    try:
        data = get_supabase().table(table).select("*").eq("prospect_id", prospect_id).order("id", desc=True).execute().data
        return pd.DataFrame(data)
    except Exception:
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
# 6. MODAL - FICHE PROJET (PIXEL PERFECT)
# =============================================================================

@st.dialog("Fiche Projet", width="large")
def show_prospect_modal(pid, data):
    """Modal de fiche projet avec design pixel perfect"""
    pid = int(pid)
    is_new = data.get("company_name") == "Nouveau Prospect"
    
    # Constants
    PRODUITS = ["LENGOOD® (Substitut Œuf)", "PEPTIPEA® (Protéine)", "NEWGOOD® (Nouveauté)"]
    APPLICATIONS = ["Boulangerie / Pâtisserie", "Sauces", "Confiserie", "Plats cuisinés", "Boissons", "Autre"]
    STATUTS = ["Prospection", "Qualification", "Échantillons en test", "Tests en cours", "Négociation", "Contrat", "Client Actif"]
    
    # ══════════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════════
    h1, h2 = st.columns([3, 1])
    with h1:
        st.markdown(f"""
            <div style="margin-bottom: 8px;">
                <h2 style="font-size: 22px; font-weight: 700; color: #111827; margin: 0;">
                    {"Nouveau Projet" if is_new else data.get("company_name", "")}
                </h2>
                <p style="font-size: 14px; color: #6B7280; margin: 4px 0 0;">
                    Gestion et Suivi R&D
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with h2:
        # Action buttons (Hunter AI, Brief R&D)
        bc1, bc2 = st.columns(2)
        with bc1:
            st.button("🎯 Hunter AI", key=f"hunter_{pid}", use_container_width=True)
        with bc2:
            st.button("📋 Brief R&D", key=f"brief_{pid}", use_container_width=True)
    
    st.markdown("<hr style='margin: 16px 0; border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════
    # BODY - TWO COLUMNS
    # ══════════════════════════════════════════════════════════
    col_left, col_right = st.columns([2, 3], gap="large")
    
    # ─────────────────────────────────────────────────────────
    # LEFT COLUMN - FORM FIELDS
    # ─────────────────────────────────────────────────────────
    with col_left:
        # Société
        st.markdown('<p class="form-label">SOCIÉTÉ / CLIENT</p>', unsafe_allow_html=True)
        name = st.text_input("company", value=data.get("company_name", ""), key=f"name_{pid}", label_visibility="collapsed", placeholder="Nom de la société")
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # Statut
        st.markdown('<p class="form-label">STATUT PIPELINE</p>', unsafe_allow_html=True)
        current_status = data.get("status", "Prospection")
        stat_idx = STATUTS.index(current_status) if current_status in STATUTS else 0
        stat = st.selectbox("status", STATUTS, index=stat_idx, key=f"stat_{pid}", label_visibility="collapsed")
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # Pays / Potentiel
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<p class="form-label">PAYS</p>', unsafe_allow_html=True)
            pays = st.text_input("country", value=data.get("country", ""), key=f"pays_{pid}", label_visibility="collapsed", placeholder="France")
        with c2:
            st.markdown('<p class="form-label">POTENTIEL (T)</p>', unsafe_allow_html=True)
            vol = st.number_input("vol", value=float(data.get("potential_volume") or 0), key=f"vol_{pid}", label_visibility="collapsed", min_value=0.0)
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # Dernier Salon / Source
        st.markdown("""
            <div style="background: #F9FAFB; padding: 16px; border-radius: 8px; margin-bottom: 8px;">
                <p class="form-label" style="margin: 0 0 8px;">📍 DERNIER SALON / SOURCE</p>
            </div>
        """, unsafe_allow_html=True)
        source = st.text_input("source", value=data.get("last_salon", ""), key=f"source_{pid}", label_visibility="collapsed", placeholder="ex: CFIA 2026, LinkedIn, Prospection directe")
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        # LinkedIn Button
        st.markdown('<p class="form-label">🔗 SOCIAL SELLING</p>', unsafe_allow_html=True)
        company_name = data.get("company_name", "")
        if company_name and company_name != "Nouveau Prospect":
            linkedin_query = urllib.parse.quote(f'{company_name} "R&D" OR "Purchasing" OR "Achats"')
            linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={linkedin_query}"
            st.markdown(f"""
                <a href="{linkedin_url}" target="_blank" style="
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    background: #0A66C2;
                    color: white;
                    padding: 10px 16px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 600;
                    text-decoration: none;
                    transition: background 0.15s ease;
                ">
                    <span style="font-weight: 700;">in</span> Rechercher contacts R&D
                </a>
            """, unsafe_allow_html=True)
    
    # ─────────────────────────────────────────────────────────
    # RIGHT COLUMN - TABS
    # ─────────────────────────────────────────────────────────
    with col_right:
        tab1, tab2, tab3 = st.tabs(["📋 Contexte & Technique", "🧪 Suivi Échantillons", "📓 Journal d'Activité"])
        
        # ── TAB 1: Contexte & Technique ──
        with tab1:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
            t1c1, t1c2 = st.columns(2)
            with t1c1:
                st.markdown('<p class="form-label">INGRÉDIENT INGOOD</p>', unsafe_allow_html=True)
                prod_idx = PRODUITS.index(data.get("product_interest")) if data.get("product_interest") in PRODUITS else 0
                prod = st.selectbox("prod", PRODUITS, index=prod_idx, key=f"prod_{pid}", label_visibility="collapsed")
            with t1c2:
                st.markdown('<p class="form-label">APPLICATION FINALE</p>', unsafe_allow_html=True)
                app_idx = APPLICATIONS.index(data.get("segment")) if data.get("segment") in APPLICATIONS else 0
                app = st.selectbox("app", APPLICATIONS, index=app_idx, key=f"app_{pid}", label_visibility="collapsed")
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            st.markdown('<p class="form-label">PROBLÉMATIQUE / BESOIN (PAIN POINT)</p>', unsafe_allow_html=True)
            pain = st.text_area("pain", value=data.get("notes", ""), height=90, key=f"pain_{pid}", label_visibility="collapsed", placeholder="Ex: Volatilité prix œuf, Texture sèche, Besoin Clean Label...")
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            st.markdown('<p class="form-label">NOTES TECHNIQUES R&D</p>', unsafe_allow_html=True)
            tech = st.text_area("tech", value=data.get("tech_notes", ""), height=90, key=f"tech_{pid}", label_visibility="collapsed", placeholder="pH cible, Température cuisson, Dosage recommandé...")
        
        # ── TAB 2: Suivi Échantillons ──
        with tab2:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
            samples_df = get_sub_data("samples", pid)
            
            if samples_df.empty:
                st.markdown("""
                    <div style="text-align: center; padding: 40px 20px; color: #9CA3AF;">
                        <p style="font-size: 14px; margin: 0;">Aucun échantillon envoyé</p>
                        <p style="font-size: 12px; margin: 8px 0 0;">Ajoutez un échantillon ci-dessous</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                S_OPTS = ["En test", "Validé", "Rejeté", "Perdu"]
                for _, r in samples_df.iterrows():
                    with st.container(border=True):
                        sc1, sc2, sc3 = st.columns([3, 1.5, 0.5])
                        with sc1:
                            st.markdown(f"""
                                <div>
                                    <span style="font-weight: 600; color: #111827;">{clean_prod_name(r['product_name'])}</span>
                                    <span style="color: #6B7280; font-size: 13px;"> · {r['reference']}</span>
                                    <br>
                                    <span style="font-size: 12px; color: #9CA3AF;">{r['date_sent'][:10]}</span>
                                </div>
                            """, unsafe_allow_html=True)
                        with sc2:
                            s_idx = S_OPTS.index(r["status"]) if r["status"] in S_OPTS else 0
                            new_s = st.selectbox("s", S_OPTS, index=s_idx, key=f"ss_{r['id']}", label_visibility="collapsed")
                            if new_s != r["status"]:
                                get_supabase().table("samples").update({"status": new_s}).eq("id", r["id"]).execute()
                        with sc3:
                            if st.button("🗑", key=f"ds_{r['id']}"):
                                get_supabase().table("samples").delete().eq("id", r["id"]).execute()
                                st.rerun()
                        
                        new_fb = st.text_input("Feedback", value=r.get("feedback") or "", key=f"fb_{r['id']}", placeholder="Retour technique...", label_visibility="collapsed")
                        if new_fb != (r.get("feedback") or ""):
                            get_supabase().table("samples").update({"feedback": new_fb}).eq("id", r["id"]).execute()
            
            st.markdown("<hr style='margin: 20px 0; border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
            
            st.markdown('<p class="form-label">➕ AJOUTER UN ÉCHANTILLON</p>', unsafe_allow_html=True)
            asc1, asc2, asc3 = st.columns([2, 1.5, 0.8])
            with asc1:
                s_ref = st.text_input("ref", key=f"sr_{pid}", placeholder="Référence / Lot", label_visibility="collapsed")
            with asc2:
                s_prod = st.selectbox("sprod", PRODUITS, key=f"sp_{pid}", label_visibility="collapsed")
            with asc3:
                if st.button("Ajouter", type="primary", key=f"add_s_{pid}", use_container_width=True):
                    if s_ref.strip():
                        get_supabase().table("samples").insert({
                            "prospect_id": pid,
                            "reference": s_ref,
                            "product_name": s_prod,
                            "status": "En test",
                            "date_sent": datetime.now().isoformat(),
                        }).execute()
                        st.rerun()
        
        # ── TAB 3: Journal d'Activité ──
        with tab3:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
            activities_df = get_sub_data("activities", pid)
            
            if activities_df.empty:
                st.markdown("""
                    <div style="text-align: center; padding: 40px 20px; color: #9CA3AF;">
                        <p style="font-size: 14px; margin: 0;">Aucune activité enregistrée</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                for _, act in activities_df.head(5).iterrows():
                    icon = "📧" if act["type"] == "Email" else "📞" if act["type"] == "Appel" else "📅" if act["type"] == "RDV" else "📝"
                    st.markdown(f"""
                        <div style="padding: 12px; background: #F9FAFB; border-radius: 8px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <span style="font-weight: 600; font-size: 13px; color: #374151;">{icon} {act['type']}</span>
                                <span style="font-size: 11px; color: #9CA3AF; font-family: 'JetBrains Mono', monospace;">{act['date'][:10]}</span>
                            </div>
                            <p style="font-size: 13px; color: #6B7280; margin: 0;">{act['content'][:100]}{'...' if len(act['content']) > 100 else ''}</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 20px 0; border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
            
            st.markdown('<p class="form-label">➕ AJOUTER UNE ACTIVITÉ</p>', unsafe_allow_html=True)
            act_type = st.selectbox("type", ["Email", "Appel", "RDV", "Note"], key=f"at_{pid}", label_visibility="collapsed")
            act_content = st.text_area("content", height=80, key=f"ac_{pid}", placeholder="Décrivez l'activité...", label_visibility="collapsed")
            
            if st.button("Enregistrer l'activité", type="primary", key=f"save_act_{pid}"):
                if act_content.strip():
                    get_supabase().table("activities").insert({
                        "prospect_id": pid,
                        "type": act_type,
                        "content": act_content,
                        "date": datetime.now().isoformat(),
                    }).execute()
                    st.success("✅ Activité ajoutée")
                    st.rerun()
    
    # ══════════════════════════════════════════════════════════
    # FOOTER - BUTTONS
    # ══════════════════════════════════════════════════════════
    st.markdown("<hr style='margin: 24px 0 16px; border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
    fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1])
    
    with fc1:
        # Delete button (danger)
        if not is_new:
            if st.button("🗑️ Supprimer", key=f"del_{pid}", use_container_width=True):
                st.session_state[f"confirm_delete_{pid}"] = True
                st.rerun()
    
    # Confirmation de suppression
    if st.session_state.get(f"confirm_delete_{pid}", False):
        st.warning("⚠️ Êtes-vous sûr de vouloir supprimer ce projet ?")
        dc1, dc2 = st.columns(2)
        with dc1:
            if st.button("Oui, supprimer", type="primary", key=f"confirm_yes_{pid}"):
                get_supabase().table("samples").delete().eq("prospect_id", pid).execute()
                get_supabase().table("activities").delete().eq("prospect_id", pid).execute()
                get_supabase().table("contacts").delete().eq("prospect_id", pid).execute()
                get_supabase().table("prospects").delete().eq("id", pid).execute()
                safe_del(f"confirm_delete_{pid}")
                safe_del("active_prospect_id")
                reset_pipeline()
                st.rerun()
        with dc2:
            if st.button("Annuler", key=f"confirm_no_{pid}"):
                safe_del(f"confirm_delete_{pid}")
                st.rerun()
    else:
        with fc3:
            if st.button("Annuler", key=f"cancel_{pid}", use_container_width=True):
                if is_new:
                    # Delete the placeholder prospect
                    get_supabase().table("prospects").delete().eq("id", pid).execute()
                safe_del("active_prospect_id")
                st.rerun()
        
        with fc4:
            if st.button("💾 Enregistrer", type="primary", key=f"save_{pid}", use_container_width=True):
                try:
                    get_supabase().table("prospects").update({
                        "company_name": name,
                        "status": stat,
                        "country": pays,
                        "potential_volume": vol,
                        "last_salon": source,
                        "product_interest": prod,
                        "segment": app,
                        "notes": pain,
                        "tech_notes": tech,
                        "last_action_date": datetime.now().isoformat(),
                    }).eq("id", pid).execute()
                    
                    st.success("✅ Projet enregistré")
                    time.sleep(0.5)
                    safe_del("active_prospect_id")
                    reset_pipeline()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")

# =============================================================================
# 7. SIDEBAR NAVIGATION
# =============================================================================

def render_sidebar():
    with st.sidebar:
        # Logo & Brand
        st.markdown(f"""
            <div style="text-align: center; padding: 20px 0 16px;">
                {ICON_LOGO}
                <div style="font-weight: 700; font-size: 18px; color: #111827; margin-top: 12px;">ING Growth</div>
                <div style="font-size: 11px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px;">AI Platform</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        
        # ── NEW PROJECT BUTTON ──
        st.markdown('<div class="new-project-btn">', unsafe_allow_html=True)
        if st.button("⊕  Nouveau Projet", key="new_project", use_container_width=True):
            # Create new prospect and open modal immediately
            try:
                res = get_supabase().table("prospects").insert({
                    "company_name": "Nouveau Prospect",
                    "status": "Prospection",
                    "last_action_date": datetime.now().isoformat(),
                }).execute()
                if res.data:
                    st.session_state["active_prospect_id"] = res.data[0]["id"]
                    st.rerun()
            except Exception as e:
                st.error(f"Erreur: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # ── NAVIGATION ──
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'Pipeline'
        
        alert_count = count_alerts()
        
        nav_items = [
            ("Dashboard", "Tableau de Bord", "dashboard"),
            ("Pipeline", "Pipeline", "pipeline"),
            ("Kanban", "Kanban", "kanban"),
            ("Samples", "Échantillons", "samples"),
            ("Contacts", "Contacts", "contacts"),
            ("News", "Veille IA", "news"),
            ("Excel", "Import / Export", "export"),
            ("Webhooks", "Webhooks", "webhook"),
            ("Alertes", f"À Relancer ({alert_count})" if alert_count > 0 else "À Relancer", "alert"),
        ]
        
        for key, label, icon_name in nav_items:
            is_active = st.session_state.selected_page == key
            icon_color = "#1E3F35" if is_active else "#6B7280"
            active_class = "active" if is_active else ""
            
            # Using HTML for perfect alignment
            st.markdown(f"""
                <div class="nav-item {active_class}" onclick="document.getElementById('nav_{key}').click()">
                    <div class="nav-icon">{get_icon(icon_name, icon_color)}</div>
                    <span class="nav-text" style="color: {icon_color};">{label}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Hidden button for click handling
            if st.button(label, key=f"nav_{key}", label_visibility="collapsed"):
                st.session_state.selected_page = key
                st.rerun()
        
        # ── DATA SECTION ──
        st.markdown("<p class='sidebar-section-title'>Données</p>", unsafe_allow_html=True)
        
        col_exp, col_imp = st.columns(2)
        with col_exp:
            st.markdown('<div class="sidebar-action-btn">', unsafe_allow_html=True)
            if st.button("Exporter", key="export_btn", use_container_width=True):
                st.session_state.selected_page = "Excel"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_imp:
            st.markdown('<div class="sidebar-action-btn">', unsafe_allow_html=True)
            if st.button("Importer", key="import_btn", use_container_width=True):
                st.session_state.selected_page = "Excel"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Footer
        st.markdown("<div style='flex: 1;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div style="padding: 16px 0; border-top: 1px solid #E5E7EB; margin-top: 24px;">
                <p style="font-size: 12px; color: #9CA3AF; margin: 0;">👤 Utilisateur connecté</p>
            </div>
        """, unsafe_allow_html=True)
        
        return st.session_state.selected_page

# =============================================================================
# 8. PIPELINE PAGE
# =============================================================================

def page_pipeline():
    # Header
    st.markdown("""
        <div style="margin-bottom: 24px;">
            <h1 style="font-size: 24px; font-weight: 700; color: #111827; margin: 0;">Pipeline Food & Ingrédients</h1>
            <p style="font-size: 14px; color: #6B7280; margin: 4px 0 0;">Vue complète de tous vos projets en cours</p>
        </div>
    """, unsafe_allow_html=True)
    
    df_raw = get_prospects()
    if df_raw.empty:
        st.info("Aucun prospect. Cliquez sur 'Nouveau Projet' pour commencer.")
        return
    
    # Filters
    st.markdown('<div class="filter-bar" style="display: flex; gap: 12px; padding: 16px 0; margin-bottom: 16px;">', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    
    with f1:
        products = ["Tous Produits"] + sorted(df_raw["product_interest"].dropna().unique().tolist())
        p_filter = st.selectbox("prod_filter", products, key="pf", label_visibility="collapsed")
    with f2:
        statuses = ["Tous Statuts", "Prospection", "Qualification", "Échantillons en test", "Tests en cours", "Négociation", "Contrat", "Client Actif"]
        s_filter = st.selectbox("stat_filter", statuses, key="sf", label_visibility="collapsed")
    with f3:
        salons = ["Tous Salons"] + sorted(df_raw["last_salon"].dropna().unique().tolist())
        sal_filter = st.selectbox("salon_filter", salons, key="salf", label_visibility="collapsed")
    with f4:
        countries = ["Tous Pays"] + sorted(df_raw["country"].dropna().unique().tolist())
        c_filter = st.selectbox("country_filter", countries, key="cf", label_visibility="collapsed")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    df = df_raw.copy()
    if p_filter != "Tous Produits":
        df = df[df["product_interest"] == p_filter]
    if s_filter != "Tous Statuts":
        df = df[df["status"] == s_filter]
    if sal_filter != "Tous Salons":
        df = df[df["last_salon"] == sal_filter]
    if c_filter != "Tous Pays":
        df = df[df["country"] == c_filter]
    
    # Get samples data
    try:
        samples_map = pd.DataFrame(get_supabase().table("samples").select("prospect_id, status").execute().data)
    except:
        samples_map = pd.DataFrame()
    
    # Table Header
    st.markdown("""
        <div class="pipeline-container">
            <div class="table-header">
                <span class="table-header-cell">SOCIÉTÉ</span>
                <span class="table-header-cell">PAYS</span>
                <span class="table-header-cell">PRODUIT</span>
                <span class="table-header-cell">STATUT</span>
                <span class="table-header-cell">CONTACT</span>
                <span class="table-header-cell">SALON</span>
                <span class="table-header-cell">SAMPLES</span>
                <span class="table-header-cell"></span>
            </div>
    """, unsafe_allow_html=True)
    
    # Table Rows
    for _, row in df.iterrows():
        # Format date
        date_str = "—"
        date_color = "#6B7280"
        if row.get("last_action_date"):
            try:
                dt = datetime.strptime(row["last_action_date"][:10], "%Y-%m-%d")
                days_ago = (datetime.now() - dt).days
                date_str = dt.strftime("%d %b %y")
                date_color = "#DC2626" if days_ago > 45 else "#F59E0B" if days_ago > 30 else "#6B7280"
            except:
                pass
        
        # Check samples
        has_samples = False
        sample_status = "-"
        if not samples_map.empty and row["id"] in samples_map["prospect_id"].values:
            has_samples = True
            sample_row = samples_map[samples_map["prospect_id"] == row["id"]].iloc[0]
            sample_status = sample_row.get("status", "En test")
        
        # Create row with button
        cols = st.columns([2, 1, 1.2, 1.2, 1, 1.2, 0.8, 0.5])
        
        with cols[0]:
            if st.button(row["company_name"].upper(), key=f"row_{row['id']}", use_container_width=True):
                st.session_state["active_prospect_id"] = row["id"]
                st.rerun()
        
        with cols[1]:
            st.markdown(f'<span class="col-country">{row.get("country") or "—"}</span>', unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown(f'<span class="col-product">{clean_prod_name(row.get("product_interest"))}</span>', unsafe_allow_html=True)
        
        with cols[3]:
            st.markdown(get_status_html(row.get("status")), unsafe_allow_html=True)
        
        with cols[4]:
            st.markdown(f'<span class="col-date" style="color: {date_color};">{date_str}</span>', unsafe_allow_html=True)
        
        with cols[5]:
            st.markdown(f'<span class="col-salon">{row.get("last_salon") or "—"}</span>', unsafe_allow_html=True)
        
        with cols[6]:
            if has_samples:
                st.markdown(f'<span class="sample-badge">{get_icon("flask")} {sample_status}</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="color: #D1D5DB;">-</span>', unsafe_allow_html=True)
        
        with cols[7]:
            st.markdown(f'<span class="row-chevron">{get_icon("chevron", "#9CA3AF")}</span>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# 9. OTHER PAGES (Simplified)
# =============================================================================

def page_dashboard():
    st.markdown('<h1 style="font-size: 24px; font-weight: 700;">📊 Tableau de Bord</h1>', unsafe_allow_html=True)
    
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
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        pie_df = df[df["product_interest"].notna()]
        if not pie_df.empty:
            fig = px.pie(pie_df, names="product_interest", hole=0.45, title="Mix Produits", color_discrete_sequence=["#1E3F35", "#10B981", "#34D399"])
            st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        bar_df = df.groupby("status").size().reset_index(name="count")
        if not bar_df.empty:
            fig = px.bar(bar_df, x="status", y="count", title="Par Statut", color_discrete_sequence=["#1E3F35"])
            st.plotly_chart(fig, use_container_width=True)

def page_kanban():
    st.markdown('<h1 style="font-size: 24px; font-weight: 700;">▦ Kanban Board</h1>', unsafe_allow_html=True)
    
    df = get_prospects()
    if df.empty:
        st.info("Aucun prospect")
        return
    
    STAGES = ["Prospection", "Qualification", "Échantillons en test", "Tests en cours", "Négociation", "Contrat", "Client Actif"]
    COLORS = {"Prospection": "#3B82F6", "Qualification": "#6366F1", "Échantillons en test": "#F59E0B", "Tests en cours": "#EA580C", "Négociation": "#8B5CF6", "Contrat": "#10B981", "Client Actif": "#059669"}
    
    cols = st.columns(len(STAGES))
    for i, stage in enumerate(STAGES):
        with cols[i]:
            count = len(df[df["status"] == stage])
            color = COLORS.get(stage, "#6B7280")
            st.markdown(f"""
                <div style="border-bottom: 3px solid {color}; padding-bottom: 8px; margin-bottom: 12px;">
                    <p style="font-size: 11px; font-weight: 700; color: {color}; text-transform: uppercase; margin: 0;">{stage}</p>
                    <p style="font-size: 11px; color: #9CA3AF; margin: 4px 0 0;">{count} projet{'s' if count != 1 else ''}</p>
                </div>
            """, unsafe_allow_html=True)
            
            for _, row in df[df["status"] == stage].iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['company_name']}**")
                    st.caption(f"🌍 {row.get('country', 'N/A')} · {int(row.get('potential_volume', 0))} T")
                    
                    bc1, bc2, bc3 = st.columns([1, 2, 1])
                    with bc1:
                        if i > 0 and st.button("←", key=f"p_{row['id']}"):
                            get_supabase().table("prospects").update({"status": STAGES[i-1]}).eq("id", row["id"]).execute()
                            st.rerun()
                    with bc2:
                        if st.button("Ouvrir", key=f"o_{row['id']}", use_container_width=True):
                            st.session_state["active_prospect_id"] = row["id"]
                            st.rerun()
                    with bc3:
                        if i < len(STAGES)-1 and st.button("→", key=f"n_{row['id']}"):
                            get_supabase().table("prospects").update({"status": STAGES[i+1]}).eq("id", row["id"]).execute()
                            st.rerun()

def page_samples():
    st.markdown('<h1 style="font-size: 24px; font-weight: 700;">🧪 Échantillons</h1>', unsafe_allow_html=True)
    
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
    st.markdown('<h1 style="font-size: 24px; font-weight: 700;">👤 Contacts</h1>', unsafe_allow_html=True)
    
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
    st.markdown('<h1 style="font-size: 24px; font-weight: 700;">📰 Veille IA</h1>', unsafe_allow_html=True)
    st.info("Veille stratégique via Perplexity AI - Configuration requise")

def page_excel():
    st.markdown('<h1 style="font-size: 24px; font-weight: 700;">📥 Import / Export</h1>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("**📤 Export**")
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
            st.markdown("**📥 Import**")
            uploaded = st.file_uploader("Fichier Excel", type=["xlsx"], label_visibility="collapsed")
            if uploaded and st.button("Importer", type="primary"):
                st.success("Import réussi")

def page_webhooks():
    st.markdown('<h1 style="font-size: 24px; font-weight: 700;">🔗 Webhooks</h1>', unsafe_allow_html=True)
    st.code("https://your-app.streamlit.io/api/webhook/leads")
    st.info("Configurez ce webhook dans Make.com pour recevoir des leads automatiquement")

def page_alertes():
    st.markdown('<h1 style="font-size: 24px; font-weight: 700;">🔔 Alertes</h1>', unsafe_allow_html=True)
    
    # Retention alerts
    st.markdown("**⚠️ Clients sans contact (45+ jours)**")
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
    
    # Handle modal
    if "active_prospect_id" in st.session_state:
        try:
            data = get_supabase().table("prospects").select("*").eq("id", st.session_state["active_prospect_id"]).execute().data[0]
            show_prospect_modal(st.session_state["active_prospect_id"], data)
        except:
            safe_del("active_prospect_id")
    
    # Route pages
    pages = {
        "Dashboard": page_dashboard,
        "Pipeline": page_pipeline,
        "Kanban": page_kanban,
        "Samples": page_samples,
        "Contacts": page_contacts,
        "News": page_news,
        "Excel": page_excel,
        "Webhooks": page_webhooks,
        "Alertes": page_alertes,
    }
    
    pages.get(selected_page, page_pipeline)()

if __name__ == "__main__":
    main()
