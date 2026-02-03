# =============================================================================
# ING GROWTH AI — CRM Stratégique
# Version 2.1 CORRIGÉE | Structure modulaire | Streamlit + Supabase + Gemini + Perplexity
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta
import io
import time
import hashlib
import json
import urllib.parse
import requests
import openpyxl
from openpyxl import load_workbook
from io import BytesIO

# =============================================================================
# SVG ICONS
# =============================================================================

ICON_FUSION_AURORA = """<svg width="56" height="56" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="grad_fav_aurora" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#1E3F35;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#1E3F35;stop-opacity:1" />
        </linearGradient>
    </defs>
    <path d="M28 4c-4 10-12 14-22 14 10 4 18 12 22 22 4-10 12-18 22-22-10-4-18-8-22-14z" fill="url(#grad_fav_aurora)"/>
    <path d="M28 14c-2 6-8 10-14 10 6 2 12 8 14 14 2-6 8-10 14-10-6-2-12-4-14-14z" fill="white" fill-opacity="0.3"/>
</svg>"""

ICON_TABLEAU_DE_BORD = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1E3F35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="8" rx="2"/><rect x="3" y="14" width="8" height="7" rx="2"/><rect x="13" y="14" width="8" height="7" rx="2"/></svg>"""

ICON_PIPELINE = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1E3F35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 3.5 1 8h-3"/><path d="M3 21c3 0 7-1 7-8"/><circle cx="17.5" cy="15" r="2.5"/><path d="M17.5 17.5V22"/></svg>"""

ICON_KANBAN = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1E3F35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h18v18H3z"/><path d="M8 3v18"/><path d="M16 3v18"/><path d="M3 8h5"/><path d="M8 12h8"/><path d="M16 7h5"/></svg>"""

ICON_ECHANTILLONS = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1E3F35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v7.5L5 21h14l-5-11.5V2h-4z"/><path d="M8.5 15h7"/><rect x="10" y="2" width="4" height="1" rx="0.5" fill="#1E3F35"/></svg>"""

ICON_VEILLE_STRATEGIQUE = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1E3F35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m16 8-4 4-4 4 4-4 4-4Z" fill="#1E3F35"/><path d="M12 7V5M12 19v-2M7 12H5M19 12h-2"/></svg>"""

ICON_CONTACTS = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1E3F35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><circle cx="19" cy="5" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><circle cx="5" cy="19" r="2"/><line x1="7" y1="7" x2="10" y2="10"/><line x1="14" y1="14" x2="17" y2="17"/><line x1="17" y1="7" x2="14" y2="10"/><line x1="10" y1="14" x2="7" y2="17"/></svg>"""

ICON_A_RELANCER = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1E3F35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/><circle cx="18" cy="5" r="2" fill="#1E3F35"/></svg>"""

ICON_WEBHOOKS = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1E3F35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM6 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM18 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"/><path d="M9 19h3.5a3.5 3.5 0 0 0 3.5-3.5V8.5A3.5 3.5 0 0 1 19.5 5H21"/><path d="M6 16v-3.5A3.5 3.5 0 0 1 9.5 9H15"/></svg>"""

ICON_EXPORTER = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1E3F35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"/><polyline points="14 2 14 8 20 8"/><path d="M2 15h10"/><path d="m9 12 3 3-3 3"/><rect x="6" y="12" width="8" height="8" rx="1" opacity="0.3"/></svg>"""

# =============================================================================
# 1. CONFIGURATION GLOBALE & STYLES
# =============================================================================

st.set_page_config(
    page_title="ING Growth AI",
    page_icon="data:image/svg+xml;utf8," + urllib.parse.quote(ICON_FUSION_AURORA),
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

CSS_THEME = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp { 
        background: #fafbfc !important; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
    }
    section[data-testid="stSidebar"] { 
        background: #ffffff !important;
        border-right: 1px solid #e1e4e8 !important;
    }
    [data-testid="stVerticalBlock"] { gap: 0rem !important; }
    .stApp h1, .stApp h2, .stApp h3 { 
        font-family: 'Inter', sans-serif !important; 
        color: #24292e !important; 
        font-weight: 600 !important;
    }

    /* ── BOUTON NOUVEAU PROJET ── */
    [data-testid="stSidebar"] > div > div:first-child .stButton:first-of-type > button {
        width: 100% !important; 
        background: #1E3F35 !important;
        color: white !important;
        border: none !important; 
        border-radius: 6px !important; 
        padding: 11px 16px !important; 
        font-weight: 600 !important;
        font-size: 14px !important; 
        box-shadow: none !important;
        transition: all 0.2s ease !important;
        margin-bottom: 20px !important;
        outline: none !important;
    }
    [data-testid="stSidebar"] > div > div:first-child .stButton:first-of-type > button:hover {
        background: #2A5548 !important;
    }

    /* ── NAVIGATION ── */
    [data-testid="stSidebar"] [data-testid="column"] .stButton > button {
        background: transparent !important;
        color: #374151 !important;
        border: 0px !important;
        padding: 10px 8px 10px 4px !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] [data-testid="column"] .stButton > button:hover {
        background: #D1FAE5 !important;
        color: #065F46 !important;
    }

    /* ── PIPELINE ROWS ── */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important; 
        border: 1px solid #e1e4e8 !important;
        border-radius: 6px !important;
        padding: 12px 16px !important; 
        margin-bottom: 8px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover { 
        border-color: #d1d5db !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }

    /* ── BADGES ── */
    .badge { 
        padding: 4px 10px; 
        border-radius: 12px; 
        font-size: 11px; 
        font-weight: 600;
        display: inline-block; 
    }
    .badge-green { background: #d4edda; color: #155724; }
    .badge-yellow { background: #fff3cd; color: #856404; }
    .badge-blue { background: #cce5ff; color: #004085; }
    .badge-gray { background: #e9ecef; color: #495057; }
    .badge-red { background: #f8d7da; color: #721c24; }
    .badge-purple { background: #e9d5ff; color: #6b21a8; }
    .badge-amber { background: #fef3c7; color: #92400e; }
    .badge-emerald { background: #d1fae5; color: #065f46; }

    /* ── METRICS ── */
    [data-testid="stMetric"] { 
        background: #ffffff; 
        border-radius: 6px; 
        border: 1px solid #e1e4e8; 
        padding: 16px !important;
    }

    /* ── SECTION TITLES ── */
    .section-title {
        font-size: 24px; 
        font-weight: 600; 
        color: #24292e;
        margin-bottom: 4px;
    }
    .section-subtitle { 
        font-size: 14px; 
        color: #586069; 
        margin-bottom: 20px; 
    }

    .header-text-style {
        color: #6a737d !important; 
        font-size: 12px !important; 
        font-weight: 600 !important;
        text-transform: uppercase; 
        letter-spacing: 0.5px !important;
    }
</style>
"""
st.markdown(CSS_THEME, unsafe_allow_html=True)


# =============================================================================
# 2. AUTHENTIFICATION SIMPLE
# =============================================================================

def check_auth():
    access_token = st.secrets.get("ACCESS_TOKEN", "")
    access_password = st.secrets.get("ACCESS_PASSWORD", "")

    query_params = st.query_params
    if "token" in query_params:
        if query_params["token"] == access_token:
            st.session_state["authenticated"] = True
            return True

    if st.session_state.get("authenticated", False):
        return True

    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='text-align:center;'>"
            "<div style='font-size:42px; margin-bottom:8px;'>🧬</div>"
            "<h2 style='color:#0f172a; font-weight:800;'>ING Growth AI</h2>"
            "<p style='color:#64748b; font-size:13px;'>Plateforme Business Development</p>"
            "</div>", unsafe_allow_html=True
        )
        pwd = st.text_input("Mot de passe", type="password", label_visibility="collapsed")
        if st.button("Se connecter", use_container_width=True, type="primary"):
            if pwd and pwd == access_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")
    return False


# =============================================================================
# 3. CONNEXIONS (Supabase + Gemini)
# =============================================================================

@st.cache_resource
def init_connections():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Erreur de connexion : {e}")
        return None


def get_supabase():
    if 'supabase' not in st.session_state:
        st.session_state.supabase = init_connections()
    return st.session_state.supabase


# =============================================================================
# 4. HELPERS UTILITAIRES
# =============================================================================

if "pipeline_key" not in st.session_state:
    st.session_state["pipeline_key"] = 0


def reset_pipeline():
    st.session_state["pipeline_key"] += 1
    st.cache_data.clear()
    safe_del("active_prospect_id")
    safe_del("ai_draft")
    safe_del("editing_contacts")
    safe_del("contacts_to_delete")


def safe_del(key):
    if key in st.session_state:
        del st.session_state[key]


def clean_prod_name(name):
    if not name or name == "-" or str(name) == "nan":
        return "-"
    return str(name).split(" (")[0].split("(")[0].strip()


def get_status_badge(status):
    mapping = {
        "Prospection": ("badge badge-gray", "Prospection"),
        "Qualification": ("badge badge-blue", "Qualification"),
        "Échantillons en test": ("badge badge-yellow", "Échantillons en test"),
        "Tests en cours": ("badge badge-amber", "Tests en cours"),
        "Négociation": ("badge badge-purple", "Négociation"),
        "Contrat": ("badge badge-emerald", "Contrat"),
        "Client Actif": ("badge badge-green", "Client Actif"),
    }
    cls, label = mapping.get(status, ("badge badge-gray", status or "—"))
    return f"<span class='{cls}'>{label}</span>"


# =============================================================================
# 5. DATA LAYER (Requêtes Supabase)
# =============================================================================

def get_prospects():
    try:
        res = get_supabase().table("prospects").select("*").order("last_action_date", desc=True).execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()


def get_sub_data(table, prospect_id):
    try:
        data = (
            get_supabase().table(table)
            .select("*")
            .eq("prospect_id", prospect_id)
            .order("id", desc=True)
            .execute()
            .data
        )
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()


def count_retention_alerts():
    forty_five_days_ago = (datetime.now() - timedelta(days=45)).isoformat()
    try:
        res = (
            get_supabase().table("prospects")
            .select("id", count="exact")
            .eq("status", "Client Actif")
            .lte("last_action_date", forty_five_days_ago)
            .execute()
        )
        return res.count if res.count else 0
    except Exception:
        return 0


def count_sample_alerts():
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    try:
        res = (
            get_supabase().table("samples")
            .select("id", count="exact")
            .is_("feedback", "null")
            .lte("date_sent", fifteen_days_ago)
            .execute()
        )
        return res.count if res.count else 0
    except Exception:
        return 0


# =============================================================================
# 6. AI CORE — Gemini
# =============================================================================

def ai_generate_smart_email(company, product, tone, country, prospect_id):
    activities = get_sub_data("activities", prospect_id)
    activity_summary = ""
    if not activities.empty:
        last_acts = activities.head(3)
        activity_summary = "\n".join(
            [f"- {row.get('date','')[:10]} : {row.get('content','')}" for _, row in last_acts.iterrows()]
        )

    samples = get_sub_data("samples", prospect_id)
    sample_summary = ""
    if not samples.empty:
        sample_summary = "\n".join(
            [f"- {row.get('product_name','')} | Ref: {row.get('reference','')} | Statut: {row.get('status','')} | Feedback: {row.get('feedback','Aucun')}"
             for _, row in samples.iterrows()]
        )

    prompt = f"""
    Rôle : Manager commercial technique pour Ingood Growth.
    Cible : {company} ({country}). Produit : {product}. Ton : {tone}.

    CONTEXTE HISTORIQUE :
    Dernières activités :
    {activity_summary if activity_summary else "Aucune activité enregistrée."}

    Échantillons envoyés :
    {sample_summary if sample_summary else "Aucun échantillon envoyé."}

    Instructions :
    1. Analyse le contexte ci-dessus pour personnaliser l'email.
    2. Rédige un court email de prospection en français (max 150 mots).
    3. Lie leur activité aux bénéfices de notre produit {product}.
    4. Si des samples ont été envoyés, fais référence à leur statut.
    5. Termine par une action claire (next step).
    """

    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Service AI indisponible. Erreur : {str(e)}"


# =============================================================================
# 7. LINKEDIN SOCIAL SELLING
# =============================================================================

def generate_linkedin_url(company_name):
    query = f'{company_name} "R&D" OR "Purchasing" OR "Achats" OR "Recherche"'
    encoded = urllib.parse.quote(query)
    return f"https://www.linkedin.com/search/results/people/?keywords={encoded}"


# =============================================================================
# 8. EXPORT / IMPORT EXCEL
# =============================================================================

def export_prospects_excel():
    df = get_prospects()
    if df.empty:
        return None

    cols_export = ["id", "company_name", "status", "country", "potential_volume",
                   "product_interest", "segment", "website_url", "last_action_date",
                   "notes", "tech_notes", "last_salon"]
    df_export = df[[c for c in cols_export if c in df.columns]].copy()
    df_export.columns = [
        "ID", "Société", "Statut", "Pays", "Potentiel (T)",
        "Produit", "Segment", "Site Web", "Dernier Contact",
        "Problématique", "Notes R&D", "Salon"
    ][:len(df_export.columns)]

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Prospects")
    buffer.seek(0)
    return buffer


def import_prospects_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        col_mapping = {
            "Société": "company_name", "société": "company_name", "Company": "company_name",
            "Statut": "status", "statut": "status",
            "Pays": "country", "pays": "country",
            "Potentiel (T)": "potential_volume", "Potentiel": "potential_volume",
            "Produit": "product_interest", "produit": "product_interest",
            "Segment": "segment", "segment": "segment",
            "Site Web": "website_url",
            "Problématique": "notes",
            "Notes R&D": "tech_notes",
        }
        df.rename(columns=col_mapping, inplace=True)

        inserted = 0
        updated = 0
        errors = []

        for _, row in df.iterrows():
            company = str(row.get("company_name", "")).strip()
            if not company or company == "nan":
                continue

            record = {}
            for col in ["company_name", "status", "country", "potential_volume", "product_interest", "segment", "website_url", "notes", "tech_notes"]:
                if col in row and pd.notna(row[col]):
                    record[col] = row[col] if col != "potential_volume" else float(row[col])

            if "last_action_date" not in record:
                record["last_action_date"] = datetime.now().isoformat()

            try:
                existing = get_supabase().table("prospects").select("id").eq("company_name", company).execute()
                if existing.data:
                    get_supabase().table("prospects").update(record).eq("company_name", company).execute()
                    updated += 1
                else:
                    get_supabase().table("prospects").insert(record).execute()
                    inserted += 1
            except Exception as e:
                errors.append(f"{company} : {str(e)}")

        return {"inserted": inserted, "updated": updated, "errors": errors}
    except Exception as e:
        return {"inserted": 0, "updated": 0, "errors": [str(e)]}


# =============================================================================
# 9. VEILLE STRATEGIQUE (Perplexity)
# =============================================================================

def fetch_weekly_news():
    try:
        today = datetime.now()
        days_since_tuesday = (today.weekday() - 1) % 7
        last_tuesday = (today - timedelta(days=days_since_tuesday)).strftime("%Y-%m-%d")

        existing = get_supabase().table("weekly_news").select("*").gte("created_at", last_tuesday).order("created_at", desc=True).execute()
        if existing.data:
            return existing.data[0]

        perplexity_key = st.secrets.get("PERPLEXITY_API_KEY", "")
        if not perplexity_key:
            return {"content": "⚠️ Clé Perplexity non configurée.", "created_at": today.isoformat(), "is_error": True}

        prospects = get_prospects()
        prospect_names = prospects["company_name"].dropna().unique().tolist()[:5]
        companies_str = ", ".join(prospect_names) if prospect_names else "secteur alimentaire industriel"

        headers = {
            "Authorization": f"Bearer {perplexity_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "Tu es un analyste stratégique. Fournis une veille concise en français."},
                {"role": "user", "content": f"Résume les dernières actualités importantes concernant ces entreprises et le secteur : {companies_str}. Focus sur : acquisitions, lancements produits, partenariats. Format : bullet points courts, max 8 points."},
            ],
        }
        resp = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        content = result["choices"][0]["message"]["content"]

        get_supabase().table("weekly_news").insert({"content": content, "created_at": today.isoformat()}).execute()
        return {"content": content, "created_at": today.isoformat()}

    except Exception as e:
        return {"content": f"⚠️ Erreur lors de la veille : {str(e)}", "created_at": datetime.now().isoformat(), "is_error": True}


# =============================================================================
# 10. MODAL — FICHE PROSPECT (CORRIGÉE)
# =============================================================================

@st.dialog("Fiche Projet", width="large")
def show_prospect_card(pid, data):
    """Fiche prospect complète - Version corrigée"""
    pid = int(pid)
    company_name = data.get("company_name", "")
    
    # Constantes
    PRODUITS = ["LENGOOD® (Substitut Œuf)", "PEPTIPEA® (Protéine)", "NEWGOOD® (Nouveauté)"]
    APPLICATIONS = ["Boulangerie / Pâtisserie", "Sauces", "Confiserie", "Plats cuisinés", "Boissons"]
    STATUTS = ["Prospection", "Qualification", "Échantillons en test", "Tests en cours", "Négociation", "Contrat", "Client Actif"]
    
    st.markdown("<p style='color: #6B7280; font-size: 14px; margin: -20px 0 24px;'>Gestion et Suivi R&D</p>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([2, 3], gap="large")
    
    # ══════════════════════════════════════════════════════════════
    # COLONNE GAUCHE : FORMULAIRE PRINCIPAL
    # ══════════════════════════════════════════════════════════════
    with col_left:
        st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 6px;'>SOCIÉTÉ / CLIENT</p>", unsafe_allow_html=True)
        name = st.text_input("Société", value=company_name, key=f"n_{pid}", label_visibility="collapsed")
        
        st.write("")
        
        st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 6px;'>STATUT PIPELINE</p>", unsafe_allow_html=True)
        current_status = data.get("status", "Prospection")
        status_idx = next((i for i, s in enumerate(STATUTS) if s == current_status), 0)
        stat = st.selectbox("Statut", STATUTS, index=status_idx, key=f"stat_{pid}", label_visibility="collapsed")
        
        st.write("")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 6px;'>PAYS</p>", unsafe_allow_html=True)
            pays = st.text_input("Pays", value=data.get("country", ""), key=f"pays_{pid}", label_visibility="collapsed")
        with c2:
            st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 6px;'>POTENTIEL (T)</p>", unsafe_allow_html=True)
            vol = st.number_input("Potentiel", value=float(data.get("potential_volume") or 0), key=f"vol_{pid}", label_visibility="collapsed")
        
        st.write("")
        
        st.markdown(
            "<div style='background: #F3F4F6; padding: 14px; border-radius: 8px; margin-bottom: 16px;'>"
            "<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 8px;'>📍 DERNIER SALON / SOURCE</p></div>",
            unsafe_allow_html=True
        )
        source = st.text_input("Source", value=data.get("last_salon", ""), placeholder="ex: CFIA 2026", key=f"source_{pid}", label_visibility="collapsed")
        
        # LinkedIn Social Selling
        st.write("")
        st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 6px;'>🔗 LINKEDIN SOCIAL SELLING</p>", unsafe_allow_html=True)
        linkedin_url = generate_linkedin_url(company_name)
        st.markdown(
            f"<a href='{linkedin_url}' target='_blank' style='display:inline-flex; align-items:center; gap:6px; "
            f"background:#0a66c2; color:white; padding:8px 14px; border-radius:6px; font-size:12px; font-weight:700; "
            f"text-decoration:none;'>"
            f"<span style='font-size:15px;'>in</span> Rechercher R&D / Purchasing</a>",
            unsafe_allow_html=True,
        )
    
    # ══════════════════════════════════════════════════════════════
    # COLONNE DROITE : 3 ONGLETS
    # ══════════════════════════════════════════════════════════════
    with col_right:
        tab1, tab2, tab3 = st.tabs(["📋 Contexte & Technique", "🧪 Suivi Échantillons", "📓 Journal d'Activité"])
        
        # ─────────────────────────────────────────────────────────
        # ONGLET 1 : Contexte & Technique
        # ─────────────────────────────────────────────────────────
        with tab1:
            cr1, cr2 = st.columns(2)
            with cr1:
                st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 6px;'>INGRÉDIENT INGOOD</p>", unsafe_allow_html=True)
                prod_idx = PRODUITS.index(data.get("product_interest")) if data.get("product_interest") in PRODUITS else 0
                prod = st.selectbox("Ingrédient", PRODUITS, index=prod_idx, key=f"prod_{pid}", label_visibility="collapsed")
            with cr2:
                st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 6px;'>APPLICATION FINALE</p>", unsafe_allow_html=True)
                app_idx = APPLICATIONS.index(data.get("segment")) if data.get("segment") in APPLICATIONS else 0
                app = st.selectbox("Application", APPLICATIONS, index=app_idx, key=f"app_{pid}", label_visibility="collapsed")
            
            st.write("")
            st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 6px;'>PROBLÉMATIQUE / BESOIN (PAIN POINT)</p>", unsafe_allow_html=True)
            pain = st.text_area(
                "Problématique",
                value=data.get("notes", ""),
                height=100,
                placeholder="Ex: Volatilité prix œuf, Texture trop sèche, Besoin Clean Label...",
                key=f"pain_{pid}",
                label_visibility="collapsed"
            )
            
            st.write("")
            st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 6px;'>NOTES TECHNIQUES</p>", unsafe_allow_html=True)
            tech = st.text_area(
                "Notes techniques",
                value=data.get("tech_notes", ""),
                height=100,
                placeholder="pH, Température cuisson, dosage cible...",
                key=f"tech_{pid}",
                label_visibility="collapsed"
            )
        
        # ─────────────────────────────────────────────────────────
        # ONGLET 2 : Suivi Échantillons
        # ─────────────────────────────────────────────────────────
        with tab2:
            st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 12px;'>📦 ÉCHANTILLONS ENVOYÉS</p>", unsafe_allow_html=True)
            
            samples_df = get_sub_data("samples", pid)
            if samples_df.empty:
                st.info("Aucun échantillon envoyé pour cette société.")
            else:
                S_OPTS = ["En test", "Validé", "Rejeté", "Perdu"]
                for _, r in samples_df.iterrows():
                    with st.container(border=True):
                        sh1, sh2, sh3 = st.columns([3.5, 1.5, 0.5])
                        with sh1:
                            st.markdown(
                                f"**{clean_prod_name(r['product_name'])}** · {r['reference']} "
                                f"<small style='color:#94a3b8;'>({r['date_sent'][:10]})</small>",
                                unsafe_allow_html=True,
                            )
                        with sh2:
                            s_idx = S_OPTS.index(r["status"]) if r["status"] in S_OPTS else 0
                            new_s = st.selectbox("Statut", S_OPTS, index=s_idx, key=f"ss_{r['id']}", label_visibility="collapsed")
                            if new_s != r["status"]:
                                get_supabase().table("samples").update({"status": new_s}).eq("id", r["id"]).execute()
                        with sh3:
                            if st.button("🗑️", key=f"ds_{r['id']}"):
                                get_supabase().table("samples").delete().eq("id", r["id"]).execute()
                                st.rerun()
                        new_f = st.text_area(
                            "Feedback R&D",
                            value=r.get("feedback") or "",
                            key=f"f_{r['id']}",
                            height=60,
                            placeholder="Retour technique...",
                            label_visibility="collapsed",
                        )
                        if new_f != (r.get("feedback") or ""):
                            get_supabase().table("samples").update({"feedback": new_f}).eq("id", r["id"]).execute()
            
            st.write("")
            st.markdown("---")
            st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 12px;'>➕ AJOUTER UN ÉCHANTILLON</p>", unsafe_allow_html=True)
            cs1, cs2, cs3 = st.columns([2.2, 1.5, 0.7])
            with cs1:
                s_ref = st.text_input("Référence / Lot", key=f"sr_{pid}", placeholder="Ex: LOT-2024-001", label_visibility="collapsed")
            with cs2:
                s_prod = st.selectbox("Produit", PRODUITS, key=f"sp_{pid}", label_visibility="collapsed")
            with cs3:
                if st.button("Ajouter", type="primary", use_container_width=True, key=f"add_sample_{pid}"):
                    if s_ref.strip():
                        get_supabase().table("samples").insert({
                            "prospect_id": pid,
                            "reference": s_ref,
                            "product_name": s_prod,
                            "status": "En test",
                            "date_sent": datetime.now().isoformat(),
                        }).execute()
                        st.rerun()
        
        # ─────────────────────────────────────────────────────────
        # ONGLET 3 : Journal d'Activité
        # ─────────────────────────────────────────────────────────
        with tab3:
            st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 12px;'>📝 HISTORIQUE DES ACTIONS</p>", unsafe_allow_html=True)
            
            activities_df = get_sub_data("activities", pid)
            if activities_df.empty:
                st.info("Aucune activité enregistrée.")
            else:
                for _, act in activities_df.iterrows():
                    with st.container(border=True):
                        st.markdown(
                            f"**{act['type']}** · <small style='color:#94a3b8;'>{act['date'][:10]}</small>",
                            unsafe_allow_html=True
                        )
                        st.markdown(act['content'])
            
            st.write("")
            st.markdown("---")
            st.markdown("<p style='font-size: 12px; font-weight: 600; color: #6B7280; margin-bottom: 12px;'>➕ AJOUTER UNE ACTIVITÉ</p>", unsafe_allow_html=True)
            
            act_type = st.selectbox("Type", ["Email", "Appel", "RDV", "Note"], key=f"act_type_{pid}")
            act_content = st.text_area("Contenu", key=f"act_content_{pid}", height=80, placeholder="Décrivez l'action...", label_visibility="collapsed")
            
            if st.button("Enregistrer activité", type="primary", key=f"save_act_{pid}"):
                if act_content.strip():
                    get_supabase().table("activities").insert({
                        "prospect_id": pid,
                        "type": act_type,
                        "content": act_content,
                        "date": datetime.now().isoformat(),
                    }).execute()
                    st.success("✅ Activité ajoutée")
                    st.rerun()
    
    # ══════════════════════════════════════════════════════════════
    # FOOTER : BOUTONS D'ACTION
    # ══════════════════════════════════════════════════════════════
    st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("Annuler", use_container_width=True, key=f"cancel_{pid}"):
            safe_del("active_prospect_id")
            st.rerun()
    with col_btn2:
        if st.button("💾 Enregistrer", type="primary", use_container_width=True, key=f"save_{pid}"):
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
                
                st.success("✅ Prospect mis à jour avec succès !")
                time.sleep(1)
                reset_pipeline()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")


# =============================================================================
# 11. SIDEBAR NAVIGATION
# =============================================================================

def render_sidebar():
    with st.sidebar:
        st.markdown(
            f"<div style='padding: 24px 0; text-align: center;'>"
            f"{ICON_FUSION_AURORA}"
            f"<div style='font-weight: 600; font-size: 17px; color: #24292e; margin-top: 12px;'>ING Growth</div>"
            f"<div style='font-size: 11px; color: #959da5; text-transform: uppercase;'>AI Platform</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # ══════════════════════════════════════════════════════════════
        # BOUTON NOUVEAU PROJET - CORRIGÉ
        # ══════════════════════════════════════════════════════════════
        if st.button("⊕ Nouveau Projet", key="btn_nouveau_projet", use_container_width=True):
            try:
                supabase_client = get_supabase()
                if supabase_client:
                    res = supabase_client.table("prospects").insert({
                        "company_name": "Nouveau Prospect",
                        "status": "Prospection",
                        "last_action_date": datetime.now().isoformat(),
                    }).execute()
                    if res.data and len(res.data) > 0:
                        st.session_state["open_new_id"] = res.data[0]["id"]
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la création")
                else:
                    st.error("❌ Connexion base de données non disponible")
            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")

        st.write("")

        retention_cnt = count_retention_alerts()
        sample_cnt = count_sample_alerts()
        total_alerts = retention_cnt + sample_cnt

        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'Pipeline'
        
        nav_items = [
            ("Dashboard", "Tableau de Bord", ICON_TABLEAU_DE_BORD),
            ("Pipeline", "Pipeline", ICON_PIPELINE),
            ("Kanban", "Kanban", ICON_KANBAN),
            ("Samples", "Échantillons", ICON_ECHANTILLONS),
            ("Contacts", "Contacts", ICON_CONTACTS),
            ("News", "Veille Stratégique", ICON_VEILLE_STRATEGIQUE),
            ("Excel", "Import / Export", ICON_EXPORTER),
            ("Webhooks", "Webhooks Make", ICON_WEBHOOKS),
            ("Alertes", f"À Relancer ({total_alerts})" if total_alerts > 0 else "À Relancer", ICON_A_RELANCER),
        ]
        
        for key, label, icon in nav_items:
            is_selected = (st.session_state.selected_page == key)
            icon_color = "#1E3F35" if is_selected else "#9CA3AF"
            icon_display = icon.replace('stroke="#1E3F35"', f'stroke="{icon_color}"').replace('fill="#1E3F35"', f'fill="{icon_color}"').replace('width="32" height="32"', 'width="20" height="20"')
            
            col_icon, col_btn = st.columns([0.13, 0.87])
            with col_icon:
                st.markdown(f"<div style='display: flex; align-items: center; justify-content: center; height: 100%;'>{icon_display}</div>", unsafe_allow_html=True)
            with col_btn:
                if st.button(label, key=f"nav_{key}", use_container_width=True):
                    st.session_state.selected_page = key
                    st.rerun()
        
        st.markdown("---")
        st.markdown("<p style='font-size: 11px; font-weight: 700; color: #959da5; text-transform: uppercase;'>Données</p>", unsafe_allow_html=True)
        
        col_exp, col_imp = st.columns(2)
        with col_exp:
            if st.button("Exporter", use_container_width=True, key="sidebar_export"):
                st.session_state.selected_page = "Excel"
                st.rerun()
        with col_imp:
            if st.button("Importer", use_container_width=True, key="sidebar_import"):
                st.session_state.selected_page = "Excel"
                st.rerun()
        
        st.markdown("---")
        st.caption("👤 Utilisateur · ING Growth AI")
        return st.session_state.selected_page


# =============================================================================
# 12. PAGES
# =============================================================================

def page_pipeline():
    st.markdown('<p class="section-title">☰ Pipeline</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Vue complète de tous vos projets en cours</p>', unsafe_allow_html=True)

    df_raw = get_prospects()
    if df_raw.empty:
        st.info("Aucun prospect enregistré. Créez-en un depuis la sidebar !")
        return

    with st.container(border=True):
        f1, f2, f3 = st.columns(3)
        with f1:
            p_f = st.selectbox("🧪 Produit", ["Tous"] + sorted(df_raw["product_interest"].dropna().unique().tolist()), label_visibility="collapsed")
        with f2:
            STATUTS_FILTRES = ["Tous", "Prospection", "Qualification", "Échantillons en test", "Tests en cours", "Négociation", "Contrat", "Client Actif"]
            s_f = st.selectbox("📌 Statut", STATUTS_FILTRES, label_visibility="collapsed")
        with f3:
            py_f = st.selectbox("🌍 Pays", ["Tous"] + sorted(df_raw["country"].dropna().unique().tolist()), label_visibility="collapsed")

    df = df_raw.copy()
    if p_f != "Tous":
        df = df[df["product_interest"] == p_f]
    if s_f != "Tous":
        df = df[df["status"] == s_f]
    if py_f != "Tous":
        df = df[df["country"] == py_f]

    st.write("")

    W = [3.2, 1, 1.5, 1.8, 1.4, 1.6, 1.2]
    h_cols = st.columns(W)
    HEADERS = ["SOCIÉTÉ", "PAYS", "PRODUIT", "STATUT", "CONTACT", "SOURCE", "SAMPLES"]
    for i, label in enumerate(HEADERS):
        h_cols[i].markdown(f'<span class="header-text-style">{label}</span>', unsafe_allow_html=True)

    try:
        s_map = pd.DataFrame(get_supabase().table("samples").select("prospect_id").execute().data)
    except Exception:
        s_map = pd.DataFrame()

    for _, row in df.iterrows():
        with st.container(border=True):
            r = st.columns(W)
            if r[0].button(row["company_name"], key=f"b_{row['id']}"):
                st.session_state["active_prospect_id"] = row["id"]
                st.rerun()
            r[1].markdown(f"<span style='color:#64748b; font-size:12px;'>{row.get('country') or '—'}</span>", unsafe_allow_html=True)
            r[2].markdown(f"<span style='color:#047857; font-weight:700; font-size:12px;'>{clean_prod_name(row.get('product_interest'))}</span>", unsafe_allow_html=True)
            r[3].markdown(get_status_badge(row.get("status")), unsafe_allow_html=True)

            if row.get("last_action_date"):
                try:
                    dt = datetime.strptime(row["last_action_date"][:10], "%Y-%m-%d")
                    days_ago = (datetime.now() - dt).days
                    color = "#dc2626" if days_ago > 45 else "#d97706" if days_ago > 30 else "#64748b"
                    r[4].markdown(f"<span style='color:{color}; font-weight:700; font-size:12px;'>{dt.strftime('%d %b %y')}</span>", unsafe_allow_html=True)
                except Exception:
                    r[4].write("—")
            else:
                r[4].write("—")

            r[5].markdown(f"<span style='color:#64748b; font-size:12px;'>{row.get('last_salon') or '—'}</span>", unsafe_allow_html=True)

            has_samples = not s_map.empty and row["id"] in s_map["prospect_id"].values
            if has_samples:
                r[6].markdown("<span class='badge badge-blue'>🧪 Oui</span>", unsafe_allow_html=True)
            else:
                r[6].write("—")


def page_kanban():
    st.markdown('<p class="section-title">▦ Kanban Board</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Glissez vos projets entre les étapes</p>', unsafe_allow_html=True)

    df = get_prospects()
    if df.empty:
        st.info("Aucun prospect pour afficher le Kanban.")
        return

    STAGES = ["Prospection", "Qualification", "Échantillons en test", "Tests en cours", "Négociation", "Contrat", "Client Actif"]
    STAGE_COLORS = {
        "Prospection": "#64748b", "Qualification": "#2563eb",
        "Échantillons en test": "#d97706", "Tests en cours": "#ea580c",
        "Négociation": "#7c3aed", "Contrat": "#047857", "Client Actif": "#16a34a",
    }

    cols = st.columns(len(STAGES))
    for i, stage in enumerate(STAGES):
        with cols[i]:
            color = STAGE_COLORS.get(stage, "#64748b")
            count = len(df[df["status"] == stage])
            st.markdown(
                f"<div style='border-bottom: 3px solid {color}; padding-bottom:6px; margin-bottom:10px;'>"
                f"<p style='font-weight:800; color:{color}; font-size:10px; text-transform:uppercase;'>{stage}</p>"
                f"<p style='font-size:10px; color:#94a3b8;'>{count} projet{'s' if count != 1 else ''}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            stage_df = df[df["status"] == stage]
            for _, row in stage_df.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['company_name']}**")
                    st.caption(f"🌍 {row.get('country') or 'N/A'} · {int(row.get('potential_volume', 0))} T")
                    
                    km1, km2, km3 = st.columns([1, 2, 1])
                    with km1:
                        if i > 0 and st.button("←", key=f"prev_{row['id']}"):
                            get_supabase().table("prospects").update({"status": STAGES[i - 1]}).eq("id", row["id"]).execute()
                            reset_pipeline()
                            st.rerun()
                    with km2:
                        if st.button("Ouvrir", key=f"kb_{row['id']}", use_container_width=True):
                            st.session_state["active_prospect_id"] = row["id"]
                            st.rerun()
                    with km3:
                        if i < len(STAGES) - 1 and st.button("→", key=f"next_{row['id']}"):
                            get_supabase().table("prospects").update({"status": STAGES[i + 1]}).eq("id", row["id"]).execute()
                            reset_pipeline()
                            st.rerun()


def page_dashboard():
    st.markdown('<p class="section-title">📊 Tableau de Bord</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Analyse stratégique de votre pipeline</p>', unsafe_allow_html=True)

    df = get_prospects()
    if df.empty:
        st.info("Aucune donnée pour le dashboard.")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Projets actifs", len(df))
    m2.metric("Potentiel total", f"{int(df['potential_volume'].sum())} T")
    signed = len(df[df["status"].isin(["Contrat", "Client Actif"])])
    m3.metric("Taux conversion", f"{int(signed / len(df) * 100)}%")
    m4.metric("En test / R&D", len(df[df["status"].isin(["Échantillons en test", "Tests en cours"])]))

    st.write("")

    ca, cb = st.columns(2)
    with ca:
        pie_df = df[df["product_interest"].notna()].copy()
        if not pie_df.empty:
            st.plotly_chart(
                px.pie(pie_df, names="product_interest", hole=0.45, title="Mix Produits",
                       color_discrete_sequence=["#047857", "#10b981", "#34d399"]),
                use_container_width=True,
            )
    with cb:
        ton_df = df.groupby("product_interest")["potential_volume"].sum().reset_index().dropna()
        if not ton_df.empty:
            st.plotly_chart(
                px.bar(ton_df, x="product_interest", y="potential_volume",
                       title="Potentiel par Produit (Tonnes)", color_discrete_sequence=["#047857"]),
                use_container_width=True,
            )


def page_contacts():
    st.markdown('<p class="section-title">👤 Annuaire Global</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Tous vos contacts centralisés</p>', unsafe_allow_html=True)

    search_q = st.text_input("🔍 Rechercher...", placeholder="Nom, Poste, Email...", label_visibility="collapsed")

    try:
        cons = pd.DataFrame(get_supabase().table("contacts").select("*, prospects(company_name)").execute().data)
    except Exception:
        cons = pd.DataFrame()

    if not cons.empty:
        cons["Entreprise"] = cons["prospects"].apply(lambda x: x["company_name"] if x else "—")
        disp = cons[["name", "role", "email", "phone", "Entreprise"]].copy()
        disp.columns = ["Nom", "Poste", "Email", "Téléphone", "Entreprise"]
        if search_q:
            disp = disp[disp.apply(lambda r: search_q.lower() in r.astype(str).str.lower().values, axis=1)]
        st.dataframe(disp, use_container_width=True, height=500)
    else:
        st.info("Aucun contact enregistré.")


def page_samples():
    st.markdown('<p class="section-title">🧪 Gestion des Échantillons</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Suivi de tous les échantillons envoyés</p>', unsafe_allow_html=True)

    try:
        samp = pd.DataFrame(get_supabase().table("samples").select("*, prospects(company_name)").execute().data)
    except Exception:
        samp = pd.DataFrame()

    if not samp.empty:
        samp["Client"] = samp["prospects"].apply(lambda x: x["company_name"] if x else "—")
        disp = samp[["date_sent", "product_name", "reference", "status", "Client", "feedback"]].copy()
        disp.columns = ["Date envoi", "Produit", "Référence", "Statut", "Client", "Feedback R&D"]
        st.dataframe(disp, use_container_width=True, height=500)
    else:
        st.info("Aucun échantillon envoyé.")


def page_news():
    st.markdown('<p class="section-title">📰 Veille Stratégique</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Mise à jour automatique via Perplexity AI</p>', unsafe_allow_html=True)

    with st.spinner("Chargement de la veille..."):
        news = fetch_weekly_news()

    if news.get("is_error"):
        st.warning(news["content"])
    else:
        st.markdown(f"**📰 Veille du {news.get('created_at', '')[:10]}**")
        st.markdown(news["content"])

    if st.button("🔄 Forcer une nouvelle veille"):
        try:
            get_supabase().table("weekly_news").delete().neq("id", 0).execute()
            st.cache_data.clear()
            st.rerun()
        except Exception:
            st.rerun()


def page_excel():
    st.markdown('<p class="section-title">📥 Import / Export Excel</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Gérez vos données en format Excel</p>', unsafe_allow_html=True)

    col_exp, col_imp = st.columns(2, gap="large")

    with col_exp:
        with st.container(border=True):
            st.markdown("**📤 EXPORT DES PROSPECTS**")
            export_buffer = export_prospects_excel()
            if export_buffer:
                st.download_button(
                    label="⬇️ Télécharger l'export Excel",
                    data=export_buffer,
                    file_name=f"ING_Growth_Prospects_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                )
            else:
                st.info("Aucune donnée à exporter.")

    with col_imp:
        with st.container(border=True):
            st.markdown("**📥 IMPORT MASSIF**")
            st.caption("Colonnes : Société, Statut, Pays, Potentiel (T), Produit, Segment")
            uploaded = st.file_uploader("Choisir un fichier Excel", type=["xlsx", "xls"], label_visibility="collapsed")
            if uploaded is not None:
                if st.button("📥 Importer", type="primary", use_container_width=True):
                    with st.spinner("Import en cours..."):
                        result = import_prospects_excel(uploaded)
                    if result["errors"]:
                        st.warning(f"Erreurs :\n" + "\n".join(result["errors"]))
                    st.success(f"✅ {result['inserted']} créé(s), {result['updated']} mis à jour")
                    reset_pipeline()


def page_webhooks():
    st.markdown('<p class="section-title">🔗 Webhooks Make.com</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Points d\'entrée pour recevoir des leads</p>', unsafe_allow_html=True)

    webhook_url = "https://your-app.streamlit.io/api/webhook/leads"

    with st.container(border=True):
        st.markdown("**📌 URL DU WEBHOOK**")
        st.code(webhook_url)
        st.caption("Copiez cette URL dans Make.com")

    with st.expander("📋 Format du payload JSON", expanded=True):
        payload_example = {
            "company_name": "Entreprise Exemple SAS",
            "country": "France",
            "product_interest": "LENGOOD® (Substitut Œuf)",
            "segment": "Boulangerie",
            "source": "Clay",
            "contact_name": "Jean Dupont",
            "contact_email": "jean.dupont@exemple.com",
        }
        st.code(json.dumps(payload_example, indent=2, ensure_ascii=False), language="json")


def page_alertes():
    st.markdown('<p class="section-title">🔔 Alertes & Relances</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Surveillance automatique</p>', unsafe_allow_html=True)

    st.markdown("**🚨 ALERTES DE RÉTENTION (45+ jours)**")
    forty_five_days_ago = (datetime.now() - timedelta(days=45)).isoformat()
    try:
        retention_alerts = pd.DataFrame(
            get_supabase().table("prospects")
            .select("*")
            .eq("status", "Client Actif")
            .lte("last_action_date", forty_five_days_ago)
            .execute()
            .data
        )
    except Exception:
        retention_alerts = pd.DataFrame()

    if not retention_alerts.empty:
        for _, alert in retention_alerts.iterrows():
            with st.container(border=True):
                st.markdown(f"⚠️ **{alert['company_name']}** - Dernier contact: {alert.get('last_action_date', '')[:10]}")
                if st.button(f"Ouvrir la fiche", key=f"ret_btn_{alert['id']}"):
                    st.session_state["active_prospect_id"] = alert["id"]
                    st.rerun()
    else:
        st.success("✅ Tous vos clients actifs sont à jour !")

    st.write("")
    st.markdown("**🧪 ÉCHANTILLONS SANS FEEDBACK (15+ jours)**")
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    try:
        sample_alerts = pd.DataFrame(
            get_supabase().table("samples")
            .select("*, prospects(company_name)")
            .is_("feedback", "null")
            .lte("date_sent", fifteen_days_ago)
            .execute()
            .data
        )
    except Exception:
        sample_alerts = pd.DataFrame()

    if not sample_alerts.empty:
        for _, alert in sample_alerts.iterrows():
            client = alert.get("prospects", {}).get("company_name", "—") if alert.get("prospects") else "—"
            with st.container(border=True):
                st.markdown(f"🧪 **{client}** - {alert.get('product_name', '')} - Envoyé le {alert.get('date_sent', '')[:10]}")
                if st.button(f"Ouvrir", key=f"sam_btn_{alert.get('prospect_id', alert['id'])}"):
                    st.session_state["active_prospect_id"] = alert.get("prospect_id")
                    st.rerun()
    else:
        st.success("✅ Tous vos échantillons ont des feedbacks !")


# =============================================================================
# 13. MAIN — ENTRY POINT
# =============================================================================

def main():
    if not check_auth():
        return

    supabase = get_supabase()
    if not supabase:
        st.stop()

    selected_page = render_sidebar()

    # Gestion modal nouveau prospect
    if "open_new_id" in st.session_state:
        st.session_state["active_prospect_id"] = st.session_state.pop("open_new_id")
        reset_pipeline()

    # Afficher le modal si un prospect est sélectionné
    if "active_prospect_id" in st.session_state:
        try:
            row_data = get_supabase().table("prospects").select("*").eq("id", st.session_state["active_prospect_id"]).execute().data[0]
            show_prospect_card(st.session_state["active_prospect_id"], row_data)
        except Exception:
            safe_del("active_prospect_id")

    # Routing des pages
    PAGE_MAP = {
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

    page_fn = PAGE_MAP.get(selected_page, page_pipeline)
    page_fn()


# =============================================================================
# RUN
# =============================================================================
if __name__ == "__main__":
    main()
