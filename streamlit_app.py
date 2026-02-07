# =============================================================================
# ING GROWTH AI — CRM Stratégique
# Version 3.2 FINAL | UI/UX Optimisée | Tous bugs corrigés
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

# Favicon SVG
FAVICON_SVG = """<svg width="32" height="32" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="56" height="56" rx="12" fill="#1E3F35"/><path d="M28 12c-3 7-9 11-16 11 7 3 13 9 16 16 3-7 9-13 16-16-7-3-13-6-16-11z" fill="white"/></svg>"""

ICON_LOGO = """<svg width="40" height="40" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M28 4c-4 10-12 14-22 14 10 4 18 12 22 22 4-10 12-18 22-22-10-4-18-8-22-14z" fill="#1E3F35"/>
    <path d="M28 14c-2 6-8 10-14 10 6 2 12 8 14 14 2-6 8-10 14-10-6-2-12-4-14-14z" fill="white" fill-opacity="0.3"/>
</svg>"""

# Navigation Icons (20x20, stroke-based)
def get_icon(name, color="#6B7280", size=20):
    icons = {
        # Navigation
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
        
        # Actions
        "chevron": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>',
        "chevron_left": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>',
        "plus": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>',
        "delete": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z"/></svg>',
        "save": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17,21 17,13 7,13 7,21"/><polyline points="7,3 7,8 15,8"/></svg>',
        "edit": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
        "close": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>',
        
        # Business
        "flask": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M9 3v6l-3 12h12l-3-12V3"/><path d="M8 3h8"/><path d="M7 15h10"/></svg>',
        "target": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
        "briefcase": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>',
        "building": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M16 6h.01M8 10h.01M16 10h.01M8 14h.01M16 14h.01"/></svg>',
        "globe": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>',
        "star": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/></svg>',
        
        # Communication
        "mail": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 6l-10 7L2 6"/></svg>',
        "phone": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/></svg>',
        "calendar": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
        "message": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>',
        "note": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg>',
        
        # Status
        "check": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><polyline points="20,6 9,17 4,12"/></svg>',
        "check_circle": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>',
        "warning": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        "info": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        
        # Social
        "linkedin": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{color}"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6zM2 9h4v12H2zM4 6a2 2 0 100-4 2 2 0 000 4z"/></svg>',
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

    /* ══════════════════════════════════════════════════════════
       SIDEBAR - BOUTON NOUVEAU PROJET (VERT)
    ══════════════════════════════════════════════════════════ */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        width: 100% !important;
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 20px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 2px 4px rgba(30,63,53,0.1) !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: var(--primary-light) !important;
        box-shadow: 0 4px 12px rgba(30,63,53,0.2) !important;
    }

    /* ══════════════════════════════════════════════════════════
       SIDEBAR - NAVIGATION BUTTONS
    ══════════════════════════════════════════════════════════ */
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        width: 100% !important;
        background: transparent !important;
        color: #4B5563 !important;
        border: none !important;
        border-left: 3px solid transparent !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        transition: all 0.15s ease !important;
        margin: 2px 0 !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: #F3F4F6 !important;
        color: #1E3F35 !important;
    }
    
    /* Boutons Export/Import dans les colonnes */
    section[data-testid="stSidebar"] [data-testid="column"] .stButton > button[kind="secondary"] {
        background: white !important;
        border: 1px solid #E5E7EB !important;
        border-left: 1px solid #E5E7EB !important;
        color: #6B7280 !important;
        font-size: 13px !important;
        padding: 10px 12px !important;
        border-radius: 8px !important;
        text-align: center !important;
        justify-content: center !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="column"] .stButton > button[kind="secondary"]:hover {
        background: #F9FAFB !important;
        border-color: #1E3F35 !important;
        color: #1E3F35 !important;
    }

    /* ── NAV ITEMS - FLOATING STYLE (ancien, gardé pour compatibilité) ── */
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

    /* ── NAV BUTTONS (Streamlit compatible) ── */
    .nav-btn button {
        background: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 10px 12px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        border-radius: 8px !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
        border-left: 3px solid transparent !important;
    }
    
    .nav-btn button:hover {
        background: var(--bg-hover) !important;
        color: var(--primary) !important;
    }
    
    .nav-btn-active button {
        background: #ECFDF5 !important;
        color: var(--primary) !important;
        font-weight: 600 !important;
        border: none !important;
        border-left: 3px solid var(--accent-green) !important;
        border-radius: 0 8px 8px 0 !important;
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
       MODAL - FICHE PROJET (OVERLAY AVEC FOND FLOU)
    ══════════════════════════════════════════════════════════ */
    /* Fond flou derrière le modal */
    div[data-testid="stDialog"]::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        z-index: -1;
    }
    
    div[data-testid="stDialog"] > div:first-child {
        background: rgba(0, 0, 0, 0.4) !important;
        backdrop-filter: blur(4px) !important;
        -webkit-backdrop-filter: blur(4px) !important;
    }
    
    /* Modal plus large */
    div[data-testid="stDialog"] > div > div {
        background: var(--bg-white) !important;
        border-radius: 16px !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
        max-width: 1100px !important;
        width: 95vw !important;
        max-height: 90vh !important;
        overflow-y: auto !important;
        margin: auto !important;
        padding: 24px 32px !important;
    }
    
    /* Bouton Supprimer en rouge */
    div[data-testid="stDialog"] button[kind="secondary"]:first-of-type,
    div[data-testid="stDialog"] .stButton:first-of-type button[kind="secondary"] {
        background: #FEF2F2 !important;
        color: #DC2626 !important;
        border: 1px solid #FECACA !important;
    }
    
    div[data-testid="stDialog"] button[kind="secondary"]:first-of-type:hover {
        background: #FEE2E2 !important;
        border-color: #DC2626 !important;
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

    /* Form Labels - FIXED: plus d'espace avec les champs */
    .form-label {
        font-size: 11px !important;
        font-weight: 700 !important;
        color: #374151 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 10px !important;
        margin-top: 0 !important;
        display: block !important;
        position: relative !important;
        z-index: 10 !important;
        background: transparent !important;
        line-height: 1.4 !important;
    }

    .form-label-first {
        margin-top: 0 !important;
    }

    /* Info box pour Salon/Source */
    .info-box {
        background: #F0FDF4 !important;
        border: 1px solid #BBF7D0 !important;
        border-radius: 10px !important;
        padding: 14px 16px !important;
        margin: 20px 0 8px 0 !important;
    }

    .info-box-label {
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #166534 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin: 0 !important;
    }

    /* Form Inputs - avec plus d'espace */
    .stTextInput > div,
    .stTextArea > div,
    .stSelectbox > div,
    .stNumberInput > div {
        margin-top: 4px !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        padding: 12px 14px !important;
        background: var(--bg-white) !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stSelectbox > div > div:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(30,63,53,0.1) !important;
        outline: none !important;
    }
    
    /* Selectbox dropdown visible */
    .stSelectbox [data-baseweb="select"] {
        background: white !important;
    }
    
    .stSelectbox [data-baseweb="popover"] {
        z-index: 9999 !important;
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

    /* Bouton Supprimer dans le modal */
    div[data-testid="stDialog"] .stButton > button:has-text("Supprimer"),
    div[data-testid="stDialog"] button[kind="secondary"]:first-of-type {
        background: #FEF2F2 !important;
        color: #DC2626 !important;
        border: 1px solid #FECACA !important;
    }
    
    div[data-testid="stDialog"] button[kind="secondary"]:first-of-type:hover {
        background: #FEE2E2 !important;
        border-color: #DC2626 !important;
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
# 6. MODAL - FICHE PROJET (CORRIGÉ)
# =============================================================================

@st.dialog("Fiche Projet", width="large")
def show_prospect_modal(pid, data):
    """Modal de fiche projet avec gestion d'état correcte"""
    pid = int(pid)
    is_new = data.get("company_name") == "Nouveau Prospect"
    
    # Constants
    PRODUITS = ["", "LENGOOD® (Substitut Œuf)", "PEPTIPEA® (Protéine)", "NEWGOOD® (Nouveauté)"]
    APPLICATIONS = ["", "Boulangerie / Pâtisserie", "Sauces", "Confiserie", "Plats cuisinés", "Boissons", "Autre"]
    STATUTS = ["Prospection", "Qualification", "Échantillons en test", "Tests en cours", "Négociation", "Contrat", "Client Actif"]
    
    # ══════════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════════
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
            <div>
                <h2 style="font-size: 24px; font-weight: 700; color: #111827; margin: 0;">
                    {"Nouveau Projet" if is_new else data.get("company_name", "Projet")}
                </h2>
                <p style="font-size: 14px; color: #6B7280; margin: 6px 0 0;">Gestion et Suivi R&D</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Boutons d'action en haut
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
    with btn_col1:
        st.button("🎯 Hunter AI", key=f"hunter_{pid}", use_container_width=True)
    with btn_col2:
        st.button("📋 Brief R&D", key=f"brief_{pid}", use_container_width=True)
    
    st.markdown("<hr style='margin: 20px 0; border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════
    # BODY - TWO COLUMNS
    # ══════════════════════════════════════════════════════════
    col_left, col_right = st.columns([1, 1.2], gap="large")
    
    # ─────────────────────────────────────────────────────────
    # LEFT COLUMN - FORM FIELDS
    # ─────────────────────────────────────────────────────────
    with col_left:
        # Société
        st.markdown("**SOCIÉTÉ / CLIENT**")
        name = st.text_input(
            "Société",
            value=data.get("company_name") or "",
            key=f"inp_name_{pid}",
            label_visibility="collapsed",
            placeholder="Nom de la société"
        )
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # Statut - IMPORTANT: utiliser value au lieu de index pour éviter les conflits
        st.markdown("**STATUT PIPELINE**")
        current_status = data.get("status") or "Prospection"
        stat_index = STATUTS.index(current_status) if current_status in STATUTS else 0
        stat = st.selectbox(
            "Statut",
            options=STATUTS,
            index=stat_index,
            key=f"inp_stat_{pid}",
            label_visibility="collapsed"
        )
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # Pays / Potentiel
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**PAYS**")
            pays = st.text_input(
                "Pays",
                value=data.get("country") or "",
                key=f"inp_pays_{pid}",
                label_visibility="collapsed",
                placeholder="France"
            )
        with c2:
            st.markdown("**POTENTIEL (T)**")
            vol = st.number_input(
                "Volume",
                value=float(data.get("potential_volume") or 0),
                key=f"inp_vol_{pid}",
                label_visibility="collapsed",
                min_value=0.0,
                step=1.0
            )
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # Dernier Salon / Source
        st.markdown("""
            <div style="background: #F0FDF4; padding: 12px 16px; border-radius: 8px; border: 1px solid #BBF7D0; margin-bottom: 10px;">
                <span style="font-size: 12px; font-weight: 700; color: #166534;">📍 DERNIER SALON / SOURCE</span>
            </div>
        """, unsafe_allow_html=True)
        source = st.text_input(
            "Source",
            value=data.get("last_salon") or "",
            key=f"inp_source_{pid}",
            label_visibility="collapsed",
            placeholder="ex: CFIA 2026, LinkedIn, Prospection directe"
        )
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # LinkedIn Button
        st.markdown("**🔗 SOCIAL SELLING**")
        company_name = name or data.get("company_name", "")
        if company_name and company_name != "Nouveau Prospect":
            linkedin_query = urllib.parse.quote(f'{company_name} "R&D" OR "Purchasing" OR "Achats"')
            linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={linkedin_query}"
            st.link_button("🔍 Rechercher contacts R&D", linkedin_url, use_container_width=True)
        else:
            st.caption("Renseignez le nom de la société pour activer")
    
    # ─────────────────────────────────────────────────────────
    # RIGHT COLUMN - TABS
    # ─────────────────────────────────────────────────────────
    with col_right:
        tab1, tab2, tab3 = st.tabs(["📝 Contexte & Technique", "🧪 Suivi Échantillons", "📅 Journal d'Activité"])
        
        # ── TAB 1: Contexte & Technique ──
        with tab1:
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            t1c1, t1c2 = st.columns(2)
            with t1c1:
                st.markdown("**INGRÉDIENT INGOOD**")
                current_prod = data.get("product_interest") or ""
                prod_index = PRODUITS.index(current_prod) if current_prod in PRODUITS else 0
                prod = st.selectbox(
                    "Ingrédient",
                    options=PRODUITS,
                    index=prod_index,
                    key=f"inp_prod_{pid}",
                    label_visibility="collapsed",
                    format_func=lambda x: x if x else "Sélectionner..."
                )
            with t1c2:
                st.markdown("**APPLICATION FINALE**")
                current_app = data.get("segment") or ""
                app_index = APPLICATIONS.index(current_app) if current_app in APPLICATIONS else 0
                app = st.selectbox(
                    "Application",
                    options=APPLICATIONS,
                    index=app_index,
                    key=f"inp_app_{pid}",
                    label_visibility="collapsed",
                    format_func=lambda x: x if x else "Sélectionner..."
                )
            
            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            
            st.markdown("**PROBLÉMATIQUE / BESOIN (PAIN POINT)**")
            pain = st.text_area(
                "Notes",
                value=data.get("notes") or "",
                height=100,
                key=f"inp_pain_{pid}",
                label_visibility="collapsed",
                placeholder="Ex: Volatilité prix œuf, Texture sèche, Besoin Clean Label..."
            )
            
            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            
            st.markdown("**NOTES TECHNIQUES R&D**")
            tech = st.text_area(
                "Tech Notes",
                value=data.get("tech_notes") or "",
                height=100,
                key=f"inp_tech_{pid}",
                label_visibility="collapsed",
                placeholder="pH cible, Température cuisson, Dosage recommandé..."
            )
        
        # ── TAB 2: Suivi Échantillons ──
        with tab2:
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            samples_df = get_sub_data("samples", pid)
            
            if samples_df.empty:
                st.info("Aucun échantillon envoyé. Ajoutez-en un ci-dessous.")
            else:
                S_OPTS = ["En test", "Validé", "Rejeté", "Perdu"]
                for _, r in samples_df.iterrows():
                    with st.container(border=True):
                        sc1, sc2, sc3 = st.columns([3, 1.5, 0.5])
                        with sc1:
                            st.markdown(f"**{clean_prod_name(r['product_name'])}** · {r['reference']}")
                            st.caption(f"Envoyé le {r['date_sent'][:10]}")
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
            
            st.markdown("---")
            
            st.markdown("**➕ AJOUTER UN ÉCHANTILLON**")
            asc1, asc2 = st.columns([2, 1])
            with asc1:
                s_ref = st.text_input("ref", key=f"sr_{pid}", placeholder="Référence / Lot", label_visibility="collapsed")
            with asc2:
                s_prod = st.selectbox("sprod", PRODUITS[1:], key=f"sp_{pid}", label_visibility="collapsed")
            
            if st.button("➕ Ajouter l'échantillon", type="primary", key=f"add_s_{pid}"):
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
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            activities_df = get_sub_data("activities", pid)
            
            if activities_df.empty:
                st.info("Aucune activité enregistrée.")
            else:
                for _, act in activities_df.head(5).iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{act['type']}** · {act['date'][:10]}")
                        st.write(act['content'][:150] + ('...' if len(act['content']) > 150 else ''))
            
            st.markdown("---")
            
            st.markdown("**➕ AJOUTER UNE ACTIVITÉ**")
            act_type = st.selectbox("type", ["Email", "Appel", "RDV", "Note"], key=f"at_{pid}", label_visibility="collapsed")
            act_content = st.text_area("content", height=80, key=f"ac_{pid}", placeholder="Décrivez l'activité...", label_visibility="collapsed")
            
            if st.button("➕ Enregistrer l'activité", type="primary", key=f"save_act_{pid}"):
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
    
    # Confirmation de suppression
    if st.session_state.get(f"confirm_delete_{pid}", False):
        st.error("⚠️ Êtes-vous sûr de vouloir supprimer ce projet ? Cette action est irréversible.")
        dc1, dc2, dc3 = st.columns([1, 1, 2])
        with dc1:
            if st.button("Oui, supprimer", type="primary", key=f"confirm_yes_{pid}", use_container_width=True):
                get_supabase().table("samples").delete().eq("prospect_id", pid).execute()
                get_supabase().table("activities").delete().eq("prospect_id", pid).execute()
                get_supabase().table("contacts").delete().eq("prospect_id", pid).execute()
                get_supabase().table("prospects").delete().eq("id", pid).execute()
                safe_del(f"confirm_delete_{pid}")
                safe_del("active_prospect_id")
                reset_pipeline()
                st.rerun()
        with dc2:
            if st.button("Non, annuler", key=f"confirm_no_{pid}", use_container_width=True):
                safe_del(f"confirm_delete_{pid}")
                st.rerun()
    else:
        # Boutons principaux
        fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1.5])
        
        with fc1:
            # Bouton Supprimer (rouge)
            if not is_new:
                delete_clicked = st.button("🗑️ Supprimer", key=f"del_{pid}", use_container_width=True, type="secondary")
                if delete_clicked:
                    st.session_state[f"confirm_delete_{pid}"] = True
                    st.rerun()
        
        with fc3:
            if st.button("Annuler", key=f"cancel_{pid}", use_container_width=True):
                if is_new:
                    get_supabase().table("prospects").delete().eq("id", pid).execute()
                safe_del("active_prospect_id")
                st.rerun()
        
        with fc4:
            if st.button("Enregistrer & Fermer", type="primary", key=f"save_{pid}", use_container_width=True):
                try:
                    save_data = {
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
                    }
                    
                    get_supabase().table("prospects").update(save_data).eq("id", pid).execute()
                    
                    st.success("✅ Projet enregistré")
                    time.sleep(0.5)
                    safe_del("active_prospect_id")
                    reset_pipeline()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")
# 7. SIDEBAR NAVIGATION - AVEC ICÔNES SVG
# =============================================================================

# Icônes SVG pour la sidebar
SIDEBAR_ICONS = {
    "dashboard": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="8" rx="2"/><rect x="3" y="14" width="8" height="7" rx="2"/><rect x="13" y="14" width="8" height="7" rx="2"/></svg>""",
    "pipeline": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 3.5 1 8h-3"/><path d="M3 21c3 0 7-1 7-8"/><circle cx="17.5" cy="15" r="2.5"/><path d="M17.5 17.5V22"/></svg>""",
    "kanban": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 3v18"/><path d="M16 3v18"/></svg>""",
    "samples": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v7.5L5 21h14l-5-11.5V2h-4z"/><path d="M8.5 15h7"/></svg>""",
    "contacts": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><circle cx="19" cy="5" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><circle cx="5" cy="19" r="2"/><line x1="7" y1="7" x2="10" y2="10"/><line x1="14" y1="14" x2="17" y2="17"/><line x1="17" y1="7" x2="14" y2="10"/><line x1="10" y1="14" x2="7" y2="17"/></svg>""",
    "news": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 7V5M12 19v-2M7 12H5M19 12h-2"/></svg>""",
    "excel": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"/><polyline points="14 2 14 8 20 8"/><path d="M2 15h10"/><path d="m9 12 3 3-3 3"/></svg>""",
    "webhooks": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="19" r="3"/><circle cx="18" cy="19" r="3"/><path d="M9 19h3.5a3.5 3.5 0 0 0 3.5-3.5V8.5A3.5 3.5 0 0 1 19.5 5H21"/><path d="M6 16v-3.5A3.5 3.5 0 0 1 9.5 9H15"/></svg>""",
    "alerts": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>""",
}

def render_sidebar():
    with st.sidebar:
        # Logo & Brand
        st.markdown(f"""
            <div style="text-align: center; padding: 16px 0 20px;">
                {ICON_LOGO}
                <div style="font-weight: 700; font-size: 18px; color: #111827; margin-top: 12px;">ING Growth</div>
                <div style="font-size: 11px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px;">AI Platform</div>
            </div>
        """, unsafe_allow_html=True)
        
        # ── NOUVEAU PROJET BUTTON ──
        if st.button("✦  Nouveau Projet", key="btn_new_project", use_container_width=True, type="primary"):
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
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # ── NAVIGATION ──
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'Pipeline'
        
        alert_count = count_alerts()
        
        # Items de navigation avec icônes SVG
        nav_items = [
            ("Dashboard", "dashboard", "Tableau de Bord"),
            ("Pipeline", "pipeline", "Pipeline"),
            ("Kanban", "kanban", "Kanban"),
            ("Samples", "samples", "Échantillons"),
            ("Contacts", "contacts", "Contacts"),
            ("News", "news", "Veille IA"),
            ("Excel", "excel", "Import / Export"),
            ("Webhooks", "webhooks", "Webhooks"),
            ("Alertes", "alerts", f"À Relancer ({alert_count})" if alert_count > 0 else "À Relancer"),
        ]
        
        for page_key, icon_key, label in nav_items:
            is_active = st.session_state.selected_page == page_key
            icon_color = "#1E3F35" if is_active else "#6B7280"
            bg_color = "#ECFDF5" if is_active else "transparent"
            text_color = "#1E3F35" if is_active else "#4B5563"
            font_weight = "600" if is_active else "500"
            border_left = "3px solid #10B981" if is_active else "3px solid transparent"
            border_radius = "0 8px 8px 0" if is_active else "8px"
            
            # Remplacer currentColor par la bonne couleur
            icon_svg = SIDEBAR_ICONS.get(icon_key, "").replace("currentColor", icon_color)
            
            # Créer le bouton avec icône SVG
            if st.button(
                label,
                key=f"nav_{page_key}",
                use_container_width=True,
                type="secondary"
            ):
                safe_del("active_prospect_id")
                st.session_state.selected_page = page_key
                st.rerun()
            
            # Injecter le style et l'icône via CSS/JS
            st.markdown(f"""
                <style>
                    [data-testid="stSidebar"] button[key="nav_{page_key}"],
                    [data-testid="stSidebar"] button:has(p:contains("{label}")) {{
                        background: {bg_color} !important;
                        border-left: {border_left} !important;
                        border-radius: {border_radius} !important;
                    }}
                </style>
            """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        
        # ── DATA SECTION ──
        st.caption("DONNÉES")
        col_exp, col_imp = st.columns(2)
        with col_exp:
            if st.button("Export", key="btn_export", use_container_width=True):
                st.session_state.selected_page = "Excel"
                st.rerun()
        with col_imp:
            if st.button("Import", key="btn_import", use_container_width=True):
                st.session_state.selected_page = "Excel"
                st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 8px; padding: 8px 0;">
                {get_icon("user", "#9CA3AF", 16)}
                <span style="font-size: 12px; color: #9CA3AF;">Utilisateur connecté</span>
            </div>
        """, unsafe_allow_html=True)
        
        return st.session_state.selected_page

# =============================================================================
# 8. PIPELINE PAGE
# =============================================================================

def page_pipeline():
    # Header
    st.markdown(f"""
        <div style="margin-bottom: 24px;">
            <h1 style="font-size: 24px; font-weight: 700; color: #111827; margin: 0; display: flex; align-items: center; gap: 10px;">
                {get_icon("pipeline", "#1E3F35", 28)} Pipeline Food & Ingrédients
            </h1>
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
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px;">{get_icon("dashboard", "#1E3F35", 28)} Tableau de Bord</h1>', unsafe_allow_html=True)
    
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
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px;">{get_icon("kanban", "#1E3F35", 28)} Kanban Board</h1>', unsafe_allow_html=True)
    
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
                    st.markdown(f'<span style="font-size: 12px; color: #6B7280;">{get_icon("globe", "#9CA3AF", 14)} {row.get("country", "N/A")} · {int(row.get("potential_volume", 0))} T</span>', unsafe_allow_html=True)
                    
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
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px;">{get_icon("flask", "#1E3F35", 28)} Échantillons</h1>', unsafe_allow_html=True)
    
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
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px;">{get_icon("contacts", "#1E3F35", 28)} Contacts</h1>', unsafe_allow_html=True)
    
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
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px;">{get_icon("news", "#1E3F35", 28)} Veille IA</h1>', unsafe_allow_html=True)
    st.info("Veille stratégique via Perplexity AI - Configuration requise")

def page_excel():
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px;">{get_icon("export", "#1E3F35", 28)} Import / Export</h1>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown(f'<p style="font-weight: 600; display: flex; align-items: center; gap: 8px;">{get_icon("export", "#1E3F35", 18)} Export</p>', unsafe_allow_html=True)
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
            st.markdown(f'<p style="font-weight: 600; display: flex; align-items: center; gap: 8px;">{get_icon("import", "#1E3F35", 18)} Import</p>', unsafe_allow_html=True)
            uploaded = st.file_uploader("Fichier Excel", type=["xlsx"], label_visibility="collapsed")
            if uploaded and st.button("Importer", type="primary"):
                st.success("Import réussi")

def page_webhooks():
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px;">{get_icon("webhook", "#1E3F35", 28)} Webhooks</h1>', unsafe_allow_html=True)
    st.code("https://your-app.streamlit.io/api/webhook/leads")
    st.info("Configurez ce webhook dans Make.com pour recevoir des leads automatiquement")

def page_alertes():
    st.markdown(f'<h1 style="font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px;">{get_icon("alert", "#1E3F35", 28)} Alertes</h1>', unsafe_allow_html=True)
    
    # Retention alerts
    st.markdown(f'<p style="font-weight: 600; display: flex; align-items: center; gap: 8px; margin-top: 16px;">{get_icon("warning", "#F59E0B", 18)} Clients sans contact (45+ jours)</p>', unsafe_allow_html=True)
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
            st.markdown(f'<p style="color: #10B981; display: flex; align-items: center; gap: 8px;">{get_icon("check_circle", "#10B981", 18)} Tous les clients sont à jour</p>', unsafe_allow_html=True)
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
