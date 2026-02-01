# =============================================================================
# ING GROWTH AI — CRM Stratégique
# Version 2.0 | Structure modulaire | Streamlit + Supabase + Gemini + Perplexity
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
# 1. CONFIGURATION GLOBALE & STYLES
# =============================================================================

st.set_page_config(
    page_title="ING Growth AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

CSS_THEME = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── BASE ── */
    .stApp { background-color: #ffffff !important; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #f8fafc; border-right: 1px solid #e2e8f0; }
    [data-testid="stVerticalBlock"] { gap: 0rem !important; }
    .stApp h1, .stApp h2, .stApp h3 { font-family: 'Inter', sans-serif !important; color: #0f172a !important; }

    /* ── SIDEBAR BOUTONS ── */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%; background-color: #047857 !important; color: white !important;
        border: none; border-radius: 8px; padding: 11px 16px; font-weight: 700;
        font-size: 13px; box-shadow: 0 2px 4px rgba(4,120,87,0.25);
        transition: all 0.2s ease; letter-spacing: 0.3px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #065f46 !important; transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(4,120,87,0.3);
    }

    /* ── PIPELINE HEADER ── */
    .pipeline-header-row { padding: 10px 18px 6px; margin-bottom: 2px; display: flex; align-items: center; }
    .header-text-style {
        color: #047857 !important; font-size: 11px !important; font-weight: 800 !important;
        text-transform: uppercase; letter-spacing: 1px;
    }

    /* ── PIPELINE ROWS ── */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important; border: none !important;
        border-bottom: 1px solid #f1f5f9 !important; border-radius: 0px !important;
        padding: 3px 18px !important; margin-bottom: 0px !important;
        transition: background 0.15s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover { background-color: #f8fafc !important; }

    /* ── COMPANY NAME (Link Style) ── */
    div[data-testid="column"]:first-child .stButton > button {
        background: transparent !important; border: none !important; padding: 0 !important;
        margin: 0 !important; color: #047857 !important; font-weight: 700 !important;
        font-size: 14px !important; text-align: left !important; box-shadow: none !important;
        min-height: 0px !important; height: 34px !important; line-height: 34px !important;
        display: inline-block !important; width: auto !important;
        text-decoration: none; transition: color 0.15s;
    }
    div[data-testid="column"]:first-child .stButton > button:hover { color: #065f46 !important; text-decoration: underline; }

    /* ── TRASH / DELETE ── */
    .trash-container { display: flex; align-items: center; justify-content: center; height: 36px; }
    .trash-container button {
        background: transparent !important; border: none !important; box-shadow: none !important;
        color: #94a3b8 !important; padding: 0 !important; font-size: 16px !important;
        width: 30px !important; height: 30px !important; border-radius: 6px;
        transition: all 0.15s;
    }
    .trash-container button:hover { color: #ef4444 !important; background: #fee2e2 !important; }

    /* ── BADGES ── */
    .badge { padding: 3px 10px; border-radius: 12px; font-size: 10px; font-weight: 700;
             display: inline-block; letter-spacing: 0.3px; }
    .badge-green { background: #dcfce7; color: #166534; }
    .badge-emerald { background: #d1fae5; color: #047857; }
    .badge-yellow { background: #fef9c3; color: #854d0e; }
    .badge-amber { background: #fef3c7; color: #92400e; }
    .badge-blue { background: #dbeafe; color: #1d4ed8; border: 1px solid #bfdbfe; }
    .badge-purple { background: #ede9fe; color: #6d28d9; }
    .badge-gray { background: #f1f5f9; color: #64748b; }
    .badge-red { background: #fee2e2; color: #dc2626; }

    /* ── LABELS ── */
    .label-sm { font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase;
                letter-spacing: 0.8px; margin-bottom: 4px; display: block; }
    .label-field { font-size: 11px !important; font-weight: 700 !important; color: #64748b !important;
                   text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; }

    /* ── KANBAN ── */
    .kanban-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 14px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    .kanban-card:hover { border-color: #047857; box-shadow: 0 3px 8px rgba(4,120,87,0.12); transform: translateY(-1px); }

    /* ── ALERT BOXES ── */
    .alert-retention {
        background: #fef2f2; border: 1px solid #fecaca; border-left: 4px solid #dc2626;
        border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;
    }
    .alert-news {
        background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #047857;
        border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;
    }

    /* ── FILTER BAR ── */
    .filter-bar {
        background: #047857; border-radius: 10px; padding: 14px 20px;
        margin-bottom: 18px;
    }
    .filter-bar .stSelectbox label { color: white !important; font-weight: 700 !important; font-size: 11px !important; }

    /* ── SECTION TITLES ── */
    .section-title {
        font-size: 22px; font-weight: 800; color: #0f172a;
        margin-bottom: 4px; letter-spacing: -0.3px;
    }
    .section-subtitle { font-size: 13px; color: #64748b; margin-bottom: 18px; font-weight: 500; }

    /* ── VOICE RECORDER ── */
    .voice-box {
        background: #f8fafc; border: 2px dashed #e2e8f0; border-radius: 10px;
        padding: 20px; text-align: center; margin: 10px 0;
    }
    .voice-box:hover { border-color: #047857; background: #f0fdf4; }

    /* ── WEBHOOK INFO ── */
    .webhook-box {
        background: #0f172a; border-radius: 8px; padding: 14px 18px;
        font-family: 'JetBrains Mono', monospace; font-size: 13px;
        color: #22c55e; word-break: break-all;
    }

    /* ── TABS ── */
    .stTabs [data-baseid="tabs"] { border-bottom: 2px solid #e2e8f0; }
    .stTabs [role="tab"] { font-weight: 600 !important; font-size: 13px !important; color: #64748b !important; }
    .stTabs [role="tab"][aria-selected="true"] { color: #047857 !important; border-bottom-color: #047857 !important; }

    /* ── METRICS ── */
    [data-testid="stMetric"] { background: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0; padding: 12px !important; }
    [data-testid="stMetricValue"] { color: #047857 !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] { color: #64748b !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }
</style>
"""
st.markdown(CSS_THEME, unsafe_allow_html=True)


# =============================================================================
# 2. AUTHENTIFICATION SIMPLE
# =============================================================================

def check_auth():
    """Accès restreint par mot de passe ou lien unique via query param."""
    access_token = st.secrets.get("ACCESS_TOKEN", "")
    access_password = st.secrets.get("ACCESS_PASSWORD", "")

    # Vérification via query parameter (lien unique)
    query_params = st.query_params
    if "token" in query_params:
        if query_params["token"] == access_token:
            st.session_state["authenticated"] = True
            return True

    # Déjà authentifié dans cette session
    if st.session_state.get("authenticated", False):
        return True

    # Sinon → écran de login
    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='text-align:center;'>"
            "<div style='font-size:42px; margin-bottom:8px;'>🧬</div>"
            "<h2 style='color:#0f172a; font-weight:800; margin:0; font-size:24px;'>ING Growth AI</h2>"
            "<p style='color:#64748b; font-size:13px; margin-top:4px;'>Plateforme Business Development</p>"
            "</div>", unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        pwd = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe", label_visibility="collapsed")
        if st.button("Se connecter", use_container_width=True, type="primary"):
            if pwd and pwd == access_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")
        st.markdown(
            "<p style='text-align:center; font-size:11px; color:#94a3b8; margin-top:16px;'>"
            "Vous pouvez aussi accéder via un lien unique partagé.</p>", unsafe_allow_html=True
        )
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
    """Retourne le HTML d'un badge coloré selon le statut."""
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

@st.cache_data(ttl=60)
def get_prospects(supabase):
    try:
        res = supabase.table("prospects").select("*").order("last_action_date", desc=True).execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()


def get_sub_data(supabase, table, prospect_id):
    try:
        data = (
            supabase.table(table)
            .select("*")
            .eq("prospect_id", prospect_id)
            .order("id", desc=True)
            .execute()
            .data
        )
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()


def count_retention_alerts(supabase):
    """Compte les clients actifs sans interaction depuis 45+ jours."""
    forty_five_days_ago = (datetime.now() - timedelta(days=45)).isoformat()
    try:
        res = (
            supabase.table("prospects")
            .select("id", count="exact")
            .eq("status", "Client Actif")
            .lte("last_action_date", forty_five_days_ago)
            .execute()
        )
        return res.count if res.count else 0
    except Exception:
        return 0


def count_sample_alerts(supabase):
    """Compte les échantillons sans feedback depuis 15+ jours."""
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    try:
        res = (
            supabase.table("samples")
            .select("id", count="exact")
            .is_("feedback", "null")
            .lte("date_sent", fifteen_days_ago)
            .execute()
        )
        return res.count if res.count else 0
    except Exception:
        return 0


# =============================================================================
# 6. AI CORE — Gemini + Perplexity
# =============================================================================

def ai_generate_smart_email(supabase, company, product, tone, country, prospect_id):
    """Génère un email ultra-personnalisé en synthétisant historique + samples + news."""
    # Récupérer l'historique des activités
    activities = get_sub_data(supabase, "activities", prospect_id)
    activity_summary = ""
    if not activities.empty:
        last_acts = activities.head(3)
        activity_summary = "\n".join(
            [f"- {row.get('date','')[:10]} : {row.get('content','')}" for _, row in last_acts.iterrows()]
        )

    # Récupérer les samples
    samples = get_sub_data(supabase, "samples", prospect_id)
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
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[{"google_search_retrieval": {}}],
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        try:
            model_basic = genai.GenerativeModel(model_name="gemini-1.5-flash")
            return model_basic.generate_content(prompt).text
        except Exception as e:
            return f"⚠️ Service AI indisponible. Erreur : {str(e)}"


def ai_transcribe_audio(audio_bytes):
    """Transcribe un fichier audio via Gemini."""
    try:
        import base64
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content([
            {
                "inline_data": {
                    "mime_type": "audio/wav",
                    "data": audio_b64,
                }
            },
            "Transcribe ce fichier audio en français. Retourne uniquement le texte transcrit, sans introduction ni explication."
        ])
        return response.text
    except Exception as e:
        return f"⚠️ Erreur de transcription : {str(e)}"


def fetch_weekly_news(supabase):
    """Récupère la veille stratégique via Perplexity API."""
    try:
        # Vérifie si une veille existe déjà cette semaine (mardi)
        today = datetime.now()
        # Calcul du dernier mardi
        days_since_tuesday = (today.weekday() - 1) % 7
        last_tuesday = (today - timedelta(days=days_since_tuesday)).strftime("%Y-%m-%d")

        # Cherche une veille existante pour cette semaine
        existing = supabase.table("weekly_news").select("*").gte("created_at", last_tuesday).order("created_at", desc=True).execute()
        if existing.data:
            return existing.data[0]

        # Sinon, génère une nouvelle via Perplexity
        perplexity_key = st.secrets.get("PERPLEXITY_API_KEY", "")
        if not perplexity_key:
            return {"content": "⚠️ Clé Perplexity non configurée.", "created_at": today.isoformat(), "is_error": True}

        # Récupérer les noms de prospects pour la veille
        prospects = get_prospects(supabase)
        prospect_names = prospects["company_name"].dropna().unique().tolist()[:5]
        companies_str = ", ".join(prospect_names) if prospect_names else "secteur alimentaire industriel"

        headers = {
            "Authorization": f"Bearer {perplexity_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un analyste stratégique. Fournis une veille concise en français.",
                },
                {
                    "role": "user",
                    "content": f"Résume les dernières actualités importantes concernant ces entreprises et le secteur : {companies_str}. "
                               f"Focus sur : acquisitions, lancements produits, partenariats, problèmes qualité, innovations. "
                               f"Format : bullet points courts, max 8 points, très synthétique.",
                },
            ],
        }
        resp = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        content = result["choices"][0]["message"]["content"]

        # Sauvegarder dans Supabase
        supabase.table("weekly_news").insert({
            "content": content,
            "created_at": today.isoformat(),
        }).execute()

        return {"content": content, "created_at": today.isoformat()}

    except Exception as e:
        return {"content": f"⚠️ Erreur lors de la veille : {str(e)}", "created_at": datetime.now().isoformat(), "is_error": True}


# =============================================================================
# 7. LINKEDIN SOCIAL SELLING
# =============================================================================

def generate_linkedin_url(company_name):
    """Génère une URL de recherche LinkedIn ciblée R&D / Purchasing."""
    query = f'{company_name} "R&D" OR "Purchasing" OR "Achats" OR "Recherche"'
    encoded = urllib.parse.quote(query)
    return f"https://www.linkedin.com/search/results/people/?keywords={encoded}"


# =============================================================================
# 8. EXPORT / IMPORT EXCEL
# =============================================================================

def export_prospects_excel(supabase):
    """Export de tous les prospects en .xlsx."""
    df = get_prospects(supabase)
    if df.empty:
        return None

    # Colonnes à exporter
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
        # Styling basique
        wb = writer.book
        ws = writer.sheets["Prospects"]
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        header_font = Font(name="Inter", bold=True, color="FFFFFF", size=10)
        header_fill = PatternFill(start_color="047857", end_color="047857", fill_type="solid")
        thin_border = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        )

        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=ws.max_column):
            for cell in row:
                cell.border = thin_border
                cell.font = Font(name="Inter", size=10)

        # Largeurs auto
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    buffer.seek(0)
    return buffer


def import_prospects_excel(supabase, uploaded_file):
    """Import massif depuis un fichier Excel vers Supabase."""
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

        # Mapping des colonnes possibles vers les colonnes Supabase
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
                # Vérifie si le prospect existe déjà
                existing = supabase.table("prospects").select("id").eq("company_name", company).execute()
                if existing.data:
                    supabase.table("prospects").update(record).eq("company_name", company).execute()
                    updated += 1
                else:
                    supabase.table("prospects").insert(record).execute()
                    inserted += 1
            except Exception as e:
                errors.append(f"{company} : {str(e)}")

        return {"inserted": inserted, "updated": updated, "errors": errors}

    except Exception as e:
        return {"inserted": 0, "updated": 0, "errors": [str(e)]}


# =============================================================================
# 9. WEBHOOKS MAKE.COM — Logic Layer
# =============================================================================

def process_webhook_lead(supabase, payload):
    """
    Traite un lead entrant depuis Make.com (Clay, Waalaxy, etc.).
    Payload attendu (JSON) :
    {
        "company_name": "...",
        "country": "...",
        "product_interest": "...",
        "segment": "...",
        "source": "...",         // ex: "Clay", "Waalaxy", "LinkedIn"
        "contact_name": "...",
        "contact_email": "...",
        "contact_role": "...",
        "contact_phone": "..."
    }
    """
    try:
        company = payload.get("company_name", "").strip()
        if not company:
            return {"success": False, "error": "company_name est obligatoire"}

        # Créer ou récupérer le prospect
        existing = supabase.table("prospects").select("id").eq("company_name", company).execute()
        if existing.data:
            prospect_id = existing.data[0]["id"]
        else:
            new_prospect = {
                "company_name": company,
                "status": "Prospection",
                "country": payload.get("country", ""),
                "product_interest": payload.get("product_interest", ""),
                "segment": payload.get("segment", ""),
                "last_action_date": datetime.now().isoformat(),
                "last_salon": payload.get("source", "Webhook"),
            }
            res = supabase.table("prospects").insert(new_prospect).execute()
            prospect_id = res.data[0]["id"]

        # Ajouter le contact si fourni
        contact_name = payload.get("contact_name", "").strip()
        if contact_name:
            contact = {
                "prospect_id": prospect_id,
                "name": contact_name,
                "email": payload.get("contact_email", ""),
                "role": payload.get("contact_role", ""),
                "phone": payload.get("contact_phone", ""),
            }
            supabase.table("contacts").insert(contact).execute()

        # Enregistrer dans le journal
        supabase.table("activities").insert({
            "prospect_id": prospect_id,
            "type": "Webhook",
            "content": f"Lead reçu via {payload.get('source', 'Make.com')}",
            "date": datetime.now().isoformat(),
        }).execute()

        return {"success": True, "prospect_id": prospect_id}

    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# 10. MODAL — FICHE PROSPECT AUGMENTÉE
# =============================================================================

@st.dialog(" ", width="large")
def show_prospect_card(supabase, pid, data):
    pid = int(pid)
    company_name = data.get("company_name", "")

    st.markdown(
        f"<h2 style='margin-top:-28px; margin-bottom:20px; font-size:22px; color:#0f172a; "
        f"font-weight:800; border-bottom:2px solid #047857; padding-bottom:10px;'>"
        f"🧬 {company_name}</h2>",
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1, 2], gap="large")

    # ── COLONNE GAUCHE : CRM + Social Selling ──
    with col_left:
        with st.container(border=True):
            name = st.text_input("SOCIÉTÉ", value=company_name, key=f"n_{pid}")

            STATUTS = [
                "Prospection", "Qualification", "Échantillons en test",
                "Tests en cours", "Négociation", "Contrat", "Client Actif",
            ]
            current_status = data.get("status", "Prospection")
            status_idx = next((i for i, s in enumerate(STATUTS) if s == current_status), 0)
            stat = st.selectbox("STATUT", STATUTS, index=status_idx, key=f"stat_{pid}")

            c1, c2 = st.columns(2)
            with c1:
                pays = st.text_input("PAYS", value=data.get("country", ""), key=f"pays_{pid}")
            with c2:
                vol = st.number_input("POTENTIEL (T)", value=float(data.get("potential_volume") or 0), key=f"vol_{pid}")

            web_url = st.text_input("SITE WEB", value=data.get("website_url", ""), placeholder="https://...", key=f"web_{pid}")

            last_c_str = data.get("last_action_date") or datetime.now().strftime("%Y-%m-%d")
            try:
                last_c_date = st.date_input("DERNIER CONTACT", value=datetime.strptime(last_c_str[:10], "%Y-%m-%d"), key=f"date_{pid}")
            except Exception:
                last_c_date = st.date_input("DERNIER CONTACT", value=datetime.now(), key=f"date_{pid}")

            st.markdown("---")

            # ── LINKEDIN SOCIAL SELLING ──
            st.markdown("<p class='label-field'>🔗 SOCIAL SELLING — LINKEDIN</p>", unsafe_allow_html=True)
            linkedin_url = generate_linkedin_url(company_name)
            st.markdown(
                f"<a href='{linkedin_url}' target='_blank' style='display:inline-flex; align-items:center; gap:6px; "
                f"background:#0a66c2; color:white; padding:8px 14px; border-radius:6px; font-size:12px; font-weight:700; "
                f"text-decoration:none; margin-top:4px;'>"
                f"<span style='font-size:15px;'>in</span> Rechercher R&D / Purchasing</a>",
                unsafe_allow_html=True,
            )

            st.markdown("---")

            # ── SMART EMAIL AI ──
            st.markdown("<p class='label-field'>🪄 SMART EMAIL AI</p>", unsafe_allow_html=True)
            tone = st.selectbox("Ton", ["Professionnel", "Relance amicale", "Urgent / Technique"], key=f"tone_{pid}")
            if st.button("✨ Générer l'email", use_container_width=True, type="primary"):
                with st.spinner("Analyse en cours..."):
                    st.session_state["ai_draft"] = ai_generate_smart_email(
                        supabase, company_name, data.get("product_interest", ""), tone, data.get("country", ""), pid
                    )
            if "ai_draft" in st.session_state:
                st.text_area("📧 Brouillon AI", value=st.session_state["ai_draft"], height=180, key=f"draft_{pid}")

    # ── COLONNE DROITE : 3 ONGLETS ──
    with col_right:
        tab1, tab2, tab3 = st.tabs(["📋 Contexte & Technique", "🧪 Suivi Samples", "📓 Journal & Voice"])

        # ──────── ONGLET 1 : Contexte & Technique ────────
        with tab1:
            PRODUITS = ["LENGOOD® (Substitut Œuf)", "PEPTIPEA® (Protéine)", "NEWGOOD® (Nouveauté)"]
            APPLICATIONS = ["Boulangerie", "Sauces", "Confiserie", "Plats cuisinés", "Boissons"]

            cr1, cr2 = st.columns(2)
            with cr1:
                prod_idx = PRODUITS.index(data.get("product_interest")) if data.get("product_interest") in PRODUITS else 0
                prod = st.selectbox("INGRÉDIENT", PRODUITS, index=prod_idx, key=f"prod_{pid}")
            with cr2:
                app_idx = APPLICATIONS.index(data.get("segment")) if data.get("segment") in APPLICATIONS else 0
                app = st.selectbox("APPLICATION", APPLICATIONS, index=app_idx, key=f"app_{pid}")

            pain = st.text_area("PROBLÉMATIQUE", value=data.get("notes", ""), height=75, key=f"pain_{pid}")
            tech = st.text_area("NOTES R&D", value=data.get("tech_notes", ""), height=75, key=f"tech_{pid}")

            st.markdown("---")
            st.markdown("<p class='label-field'>👥 CONTACTS</p>", unsafe_allow_html=True)

            if "editing_contacts" not in st.session_state:
                st.session_state["editing_contacts"] = get_sub_data(supabase, "contacts", pid).to_dict("records")

            hc = st.columns([1.2, 1.2, 1.6, 1.2, 0.4])
            for label, col in zip(["Nom", "Poste", "Email", "Tel", ""], hc):
                col.markdown(f'<span class="label-sm">{label}</span>', unsafe_allow_html=True)

            for i, c in enumerate(st.session_state["editing_contacts"]):
                r = st.columns([1.2, 1.2, 1.6, 1.2, 0.4])
                st.session_state["editing_contacts"][i]["name"] = r[0].text_input("N", value=c.get("name", ""), key=f"cn_{i}", label_visibility="collapsed")
                st.session_state["editing_contacts"][i]["role"] = r[1].text_input("P", value=c.get("role", ""), key=f"cp_{i}", label_visibility="collapsed")
                st.session_state["editing_contacts"][i]["email"] = r[2].text_input("E", value=c.get("email", ""), key=f"ce_{i}", label_visibility="collapsed")
                st.session_state["editing_contacts"][i]["phone"] = r[3].text_input("T", value=c.get("phone", ""), key=f"ct_{i}", label_visibility="collapsed")
                with r[4]:
                    st.markdown('<div class="trash-container">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_c_{i}"):
                        if c.get("id"):
                            if "contacts_to_delete" not in st.session_state:
                                st.session_state["contacts_to_delete"] = []
                            st.session_state["contacts_to_delete"].append(c["id"])
                        st.session_state["editing_contacts"].pop(i)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

            if st.button("⊕ Ajouter un contact"):
                st.session_state["editing_contacts"].append({"id": None, "name": ""})
                st.rerun()

        # ──────── ONGLET 2 : Suivi Samples ────────
        with tab2:
            st.markdown("<p class='label-field'>📦 ENVOYER UN ÉCHANTILLON</p>", unsafe_allow_html=True)
            cs1, cs2, cs3 = st.columns([2.2, 1.5, 0.7])
            with cs1:
                s_ref = st.text_input("Référence / Lot", key=f"sr_{pid}", placeholder="Ex: LOT-2024-001")
            with cs2:
                s_prod = st.selectbox("Produit", PRODUITS, key=f"sp_{pid}")
            with cs3:
                if st.button("+ Ajouter", type="primary"):
                    supabase.table("samples").insert({
                        "prospect_id": pid,
                        "reference": s_ref,
                        "product_name": s_prod,
                        "status": "En test",
                        "date_sent": datetime.now().isoformat(),
                    }).execute()
                    st.rerun()

            st.markdown("---")
            samples_df = get_sub_data(supabase, "samples", pid)
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
                                supabase.table("samples").update({"status": new_s}).eq("id", r["id"]).execute()
                        with sh3:
                            if st.button("🗑️", key=f"ds_{r['id']}"):
                                supabase.table("samples").delete().eq("id", r["id"]).execute()
                                st.rerun()
                        new_f = st.text_area(
                            "Feedback R&D", value=r.get("feedback") or "",
                            key=f"f_{r['id']}", height=60, placeholder="Retour technique...",
                            label_visibility="collapsed",
                        )
                        if new_f != (r.get("feedback") or ""):
                            supabase.table("samples").update({"feedback": new_f}).eq("id", r["id"]).execute()

        # ──────── ONGLET 3 : Journal & Voice-to-Text ────────
        with tab3:
            st.markdown("<p class='label-field'>🎤 COMPTE-RENDU VOCAL</p>", unsafe_allow_html=True)
            st.markdown(
                '<div class="voice-box">'
                '<p style="color:#64748b; font-size:13px; margin:0 0 10px;">Enregistre un audio après un RDV.<br>'
                '<span style="color:#94a3b8; font-size:11px;">Format accepté : WAV, MP3, OGG</span></p>'
                '</div>',
                unsafe_allow_html=True,
            )
            audio_input = st.audio_input("Enregistrer un message vocal", key=f"audio_{pid}", label_visibility="collapsed")

            if audio_input is not None:
                audio_bytes = audio_input.getvalue()
                if audio_bytes:
                    col_t1, col_t2 = st.columns([3, 1])
                    with col_t1:
                        st.audio(audio_input)
                    with col_t2:
                        if st.button("🎧 Transcrire", type="primary"):
                            with st.spinner("Transcription en cours..."):
                                transcription = ai_transcribe_audio(audio_bytes)
                                st.session_state["voice_transcription"] = transcription

                    if "voice_transcription" in st.session_state:
                        st.text_area("📝 Transcription", value=st.session_state["voice_transcription"], height=100, key=f"trans_{pid}")
                        if st.button("💾 Sauvegarder dans le journal", type="primary"):
                            supabase.table("activities").insert({
                                "prospect_id": pid,
                                "type": "Compte-rendu vocal",
                                "content": st.session_state["voice_transcription"],
                                "date": datetime.now().isoformat(),
                            }).execute()
                            safe_del("voice_transcription")
                            st.success("✅ Sauvegardé dans le journal !")
                            st.rerun()

            st.markdown("---")
            st.markdown("<p class='label-field'>📓 HISTORIQUE D'ACTIVITÉS</p>", unsafe_allow_html=True)

            # Nouvelle note manuelle
            note = st.text_area("Nouvelle activité...", key=f"act_n_{pid}", placeholder="Décris une réunion, un email, une action...", height=70)
            if st.button("+ Enregistrer la note"):
                if note.strip():
                    supabase.table("activities").insert({
                        "prospect_id": pid,
                        "type": "Note",
                        "content": note,
                        "date": datetime.now().isoformat(),
                    }).execute()
                    st.rerun()

            # Afficher historique
            activities = get_sub_data(supabase, "activities", pid)
            if activities.empty:
                st.info("Aucune activité enregistrée.")
            else:
                for _, act in activities.iterrows():
                    act_type = act.get("type", "Note")
                    type_icon = "🎤" if "vocal" in act_type.lower() else "📝" if act_type == "Note" else "🔗" if act_type == "Webhook" else "📋"
                    with st.container(border=True):
                        st.markdown(
                            f"<div style='display:flex; align-items:center; gap:8px; margin-bottom:4px;'>"
                            f"<span style='font-size:14px;'>{type_icon}</span>"
                            f"<span style='font-size:11px; color:#94a3b8; font-weight:600;'>{act['date'][:10]}</span>"
                            f"<span class='badge badge-gray' style='font-size:9px;'>{act_type}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                        st.write(act["content"])

    # ── BOUTON SAUVEGARDER ──
    st.markdown("---")
    if st.button("💾 Enregistrer & Fermer", type="primary", use_container_width=True):
        try:
            update_data = {
                "company_name": name,
                "status": stat,
                "country": pays,
                "potential_volume": float(vol),
                "website_url": web_url,
                "last_action_date": last_c_date.isoformat(),
                "product_interest": prod,
                "segment": app,
                "notes": pain,
                "tech_notes": tech,
            }
            supabase.table("prospects").update(update_data).eq("id", pid).execute()

            # Supprimer les contacts marqués
            if "contacts_to_delete" in st.session_state and st.session_state["contacts_to_delete"]:
                supabase.table("contacts").delete().in_("id", st.session_state.pop("contacts_to_delete")).execute()

            # Upsert des contacts
            for rc in st.session_state.get("editing_contacts", []):
                if str(rc.get("name", "")).strip():
                    payload = {
                        "prospect_id": pid,
                        "name": rc["name"],
                        "role": rc.get("role", ""),
                        "email": rc.get("email", ""),
                        "phone": rc.get("phone", ""),
                    }
                    if rc.get("id"):
                        supabase.table("contacts").upsert({**payload, "id": int(rc["id"])}).execute()
                    else:
                        supabase.table("contacts").insert(payload).execute()

            reset_pipeline()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")


# =============================================================================
# 11. SIDEBAR NAVIGATION
# =============================================================================

def render_sidebar(supabase):
    with st.sidebar:
        st.markdown(
            "<div style='padding: 16px 0 8px;'>"
            "<div style='display:flex; align-items:center; gap:10px;'>"
            "<span style='font-size:28px;'>🧬</span>"
            "<div><div style='font-weight:800; font-size:15px; color:#0f172a;'>ING Growth</div>"
            "<div style='font-size:10px; color:#94a3b8; font-weight:600; letter-spacing:0.5px;'>AI PLATFORM</div></div>"
            "</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        if st.button("⊕ Nouveau Projet"):
            res = supabase.table("prospects").insert({
                "company_name": "Nouveau Prospect",
                "status": "Prospection",
                "last_action_date": datetime.now().isoformat(),
            }).execute()
            st.session_state["open_new_id"] = res.data[0]["id"]
            st.rerun()

        st.write("")

        # Compteurs d'alertes
        retention_cnt = count_retention_alerts(supabase)
        sample_cnt = count_sample_alerts(supabase)
        total_alerts = retention_cnt + sample_cnt

        NAV_ITEMS = {
            "Dashboard": "📊  Tableau de bord",
            "Pipeline": "☰   Pipeline",
            "Kanban": "▦   Kanban",
            "Samples": "🧪  Échantillons",
            "Contacts": "👤  Contacts",
            "News": "📰  Veille Stratégique",
            "Excel": "📥  Import / Export",
            "Webhooks": "🔗  Webhooks Make",
            "Alertes": f"🔔  Alertes ({total_alerts})" if total_alerts > 0 else "🔔  Alertes",
        }

        sel = st.radio(
            "Navigation",
            list(NAV_ITEMS.keys()),
            format_func=lambda x: NAV_ITEMS[x],
            label_visibility="collapsed",
            index=1,
        )

        st.markdown("---")
        st.caption("👤 Utilisateur · ING Growth AI")
        return sel


# =============================================================================
# 12. PAGES
# =============================================================================

def page_pipeline(supabase):
    st.markdown('<p class="section-title">☰ Pipeline</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Vue complète de tous vos projets en cours</p>', unsafe_allow_html=True)

    df_raw = get_prospects(supabase)
    if df_raw.empty:
        st.info("Aucun prospect enregistré. Créez-en un depuis la sidebar !")
        return

    # Filtres
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

    # Header columns
    W = [3.2, 1, 1.5, 1.8, 1.4, 1.6, 1.2]
    st.markdown('<div class="pipeline-header-row">', unsafe_allow_html=True)
    h_cols = st.columns(W)
    HEADERS = ["SOCIÉTÉ", "PAYS", "PRODUIT", "STATUT", "CONTACT", "SOURCE", "SAMPLES"]
    for i, label in enumerate(HEADERS):
        h_cols[i].markdown(f'<span class="header-text-style">{label}</span>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Précharger samples
    try:
        s_map = pd.DataFrame(supabase.table("samples").select("prospect_id").execute().data)
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

            # Dernier contact
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


def page_kanban(supabase):
    st.markdown('<p class="section-title">▦ Kanban Board</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Glissez vos projets entre les étapes</p>', unsafe_allow_html=True)

    df = get_prospects(supabase)
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
                f"<p style='font-weight:800; color:{color}; font-size:10px; margin:0; text-transform:uppercase; letter-spacing:0.5px;'>"
                f"{stage}</p>"
                f"<p style='font-size:10px; color:#94a3b8; margin:2px 0 0;'>{count} projet{'s' if count != 1 else ''}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            stage_df = df[df["status"] == stage]
            for _, row in stage_df.iterrows():
                st.markdown(
                    f"<div class='kanban-card'>"
                    f"<div style='font-weight:700; color:#0f172a; font-size:13px;'>{row['company_name']}</div>"
                    f"<div style='font-size:10px; color:#64748b; margin-top:4px;'>🌍 {row.get('country') or 'N/A'}</div>"
                    f"<div style='font-size:10px; color:#047857; font-weight:600;'>📦 {clean_prod_name(row.get('product_interest'))}</div>"
                    f"<div style='font-size:11px; font-weight:800; color:#047857; margin-top:6px;'>{int(row.get('potential_volume', 0))} T</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                km1, km2, km3 = st.columns([1, 2, 1])
                with km1:
                    if i > 0 and st.button("←", key=f"prev_{row['id']}"):
                        supabase.table("prospects").update({"status": STAGES[i - 1]}).eq("id", row["id"]).execute()
                        reset_pipeline()
                        st.rerun()
                with km2:
                    if st.button("Ouvrir", key=f"kb_{row['id']}", use_container_width=True):
                        st.session_state["active_prospect_id"] = row["id"]
                        st.rerun()
                with km3:
                    if i < len(STAGES) - 1 and st.button("→", key=f"next_{row['id']}"):
                        supabase.table("prospects").update({"status": STAGES[i + 1]}).eq("id", row["id"]).execute()
                        reset_pipeline()
                        st.rerun()


def page_dashboard(supabase):
    st.markdown('<p class="section-title">📊 Tableau de Bord</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Analyse stratégique de votre pipeline</p>', unsafe_allow_html=True)

    df = get_prospects(supabase)
    if df.empty:
        st.info("Aucune donnée pour le dashboard.")
        return

    # KPIs
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Projets actifs", len(df))
    m2.metric("Potentiel total", f"{int(df['potential_volume'].sum())} T")
    signed = len(df[df["status"].isin(["Contrat", "Client Actif"])])
    m3.metric("Taux conversion", f"{int(signed / len(df) * 100)}%")
    m4.metric("En test / R&D", len(df[df["status"].isin(["Échantillons en test", "Tests en cours"])]))

    st.write("")

    # Charts
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

    # Répartition par statut
    st.write("")
    status_df = df["status"].value_counts().reset_index()
    status_df.columns = ["Statut", "Nombre"]
    st.plotly_chart(
        px.bar(status_df, x="Statut", y="Nombre", title="Répartition par Statut",
               color_discrete_sequence=["#047857"], orientation="h"),
        use_container_width=True,
    )


def page_contacts(supabase):
    st.markdown('<p class="section-title">👤 Annuaire Global</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Tous vos contacts centralisés</p>', unsafe_allow_html=True)

    search_q = st.text_input("🔍 Rechercher...", placeholder="Nom, Poste, Email, Entreprise...", label_visibility="collapsed")

    try:
        cons = pd.DataFrame(supabase.table("contacts").select("*, prospects(company_name)").execute().data)
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


def page_samples(supabase):
    st.markdown('<p class="section-title">🧪 Gestion des Échantillons</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Suivi de tous les échantillons envoyés</p>', unsafe_allow_html=True)

    try:
        samp = pd.DataFrame(supabase.table("samples").select("*, prospects(company_name)").execute().data)
    except Exception:
        samp = pd.DataFrame()

    if not samp.empty:
        samp["Client"] = samp["prospects"].apply(lambda x: x["company_name"] if x else "—")
        disp = samp[["date_sent", "product_name", "reference", "status", "Client", "feedback"]].copy()
        disp.columns = ["Date envoi", "Produit", "Référence", "Statut", "Client", "Feedback R&D"]
        st.dataframe(disp, use_container_width=True, height=500)
    else:
        st.info("Aucun échantillon envoyé.")


def page_news(supabase):
    st.markdown('<p class="section-title">📰 Veille Stratégique</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Mise à jour automatique chaque mardi à 10h via Perplexity AI</p>', unsafe_allow_html=True)

    with st.spinner("Chargement de la veille..."):
        news = fetch_weekly_news(supabase)

    if news.get("is_error"):
        st.warning(news["content"])
    else:
        st.markdown(
            f'<div class="alert-news">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
            f'<span style="font-weight:800; color:#047857; font-size:14px;">📰 Veille Hebdomadaire</span>'
            f'<span style="font-size:11px; color:#64748b;">Généré le {news.get("created_at", "")[:10]}</span>'
            f'</div>'
            f'<div style="color:#1e293b; font-size:13px; line-height:1.7;">{news["content"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Option pour forcer une nouvelle génération
    st.write("")
    if st.button("🔄 Forcer une nouvelle veille"):
        try:
            supabase.table("weekly_news").delete().neq("id", 0).execute()
            st.cache_data.clear()
            st.rerun()
        except Exception:
            st.rerun()


def page_excel(supabase):
    st.markdown('<p class="section-title">📥 Import / Export Excel</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Gérez vos données en format Excel</p>', unsafe_allow_html=True)

    col_exp, col_imp = st.columns(2, gap="large")

    # ── EXPORT ──
    with col_exp:
        with st.container(border=True):
            st.markdown("<p class='label-field'>📤 EXPORT DES PROSPECTS</p>", unsafe_allow_html=True)
            st.markdown(
                "<p style='font-size:12px; color:#64748b; margin:0 0 12px;'>"
                "Télécharge la base complète des prospects au format .xlsx avec un formatage professionnel.</p>",
                unsafe_allow_html=True,
            )
            export_buffer = export_prospects_excel(supabase)
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

    # ── IMPORT ──
    with col_imp:
        with st.container(border=True):
            st.markdown("<p class='label-field'>📥 IMPORT MASSIF</p>", unsafe_allow_html=True)
            st.markdown(
                "<p style='font-size:12px; color:#64748b; margin:0 0 12px;'>"
                "Upload un fichier Excel pour créer ou mettre à jour des prospects en masse.<br>"
                "<strong>Colonnes attendues :</strong> Société, Statut, Pays, Potentiel (T), Produit, Segment.</p>",
                unsafe_allow_html=True,
            )
            uploaded = st.file_uploader("Choisir un fichier Excel", type=["xlsx", "xls"], label_visibility="collapsed")
            if uploaded is not None:
                if st.button("📥 Importer", type="primary", use_container_width=True):
                    with st.spinner("Import en cours..."):
                        result = import_prospects_excel(supabase, uploaded)
                    if result["errors"]:
                        st.warning(f"Erreurs lors de l'import :\n" + "\n".join(result["errors"]))
                    st.success(
                        f"✅ Import terminé ! "
                        f"**{result['inserted']}** nouveau(x) prospect(s) créé(s), "
                        f"**{result['updated']}** prospect(s) mis à jour."
                    )
                    reset_pipeline()


def page_webhooks(supabase):
    st.markdown('<p class="section-title">🔗 Webhooks Make.com</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Points d\'entrée pour recevoir des leads depuis Make.com</p>', unsafe_allow_html=True)

    # URL du webhook (simulée — en prod, ce serait un endpoint FastAPI séparé)
    webhook_url = "https://your-app.streamlit.io/api/webhook/leads"

    with st.container(border=True):
        st.markdown("<p class='label-field'>📌 URL DU WEBHOOK</p>", unsafe_allow_html=True)
        st.markdown(f'<div class="webhook-box">{webhook_url}</div>', unsafe_allow_html=True)
        st.caption("Copiez cette URL dans Make.com pour connecter Clay, Waalaxy ou tout autre outil.")

    st.write("")

    # Format du payload attendu
    with st.expander("📋 Format du payload JSON attendu", expanded=True):
        payload_example = {
            "company_name": "Entreprise Exemple SAS",
            "country": "France",
            "product_interest": "LENGOOD® (Substitut Œuf)",
            "segment": "Boulangerie",
            "source": "Clay",
            "contact_name": "Jean Dupont",
            "contact_email": "jean.dupont@exemple.com",
            "contact_role": "Purchasing Manager",
            "contact_phone": "+33 6 12 34 56 78",
        }
        st.code(json.dumps(payload_example, indent=2, ensure_ascii=False), language="json")

    st.write("")

    # Test manuel du webhook
    with st.container(border=True):
        st.markdown("<p class='label-field'>🧪 TEST MANUEL DU WEBHOOK</p>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:12px; color:#64748b; margin:0 0 12px;'>"
            "Simulez la réception d'un lead pour tester le pipeline.</p>",
            unsafe_allow_html=True,
        )
        tc1, tc2 = st.columns(2)
        with tc1:
            test_company = st.text_input("Société", value="Test Company Demo", key="wh_company")
            test_country = st.text_input("Pays", value="France", key="wh_country")
            test_source = st.text_input("Source", value="Clay", key="wh_source")
        with tc2:
            test_contact = st.text_input("Nom contact", value="Marie Test", key="wh_contact")
            test_email = st.text_input("Email", value="marie@test.com", key="wh_email")
            test_role = st.text_input("Poste", value="R&D Manager", key="wh_role")

        if st.button("▶️ Simuler la réception du lead", type="primary"):
            test_payload = {
                "company_name": test_company,
                "country": test_country,
                "product_interest": "LENGOOD® (Substitut Œuf)",
                "segment": "Boulangerie",
                "source": test_source,
                "contact_name": test_contact,
                "contact_email": test_email,
                "contact_role": test_role,
            }
            with st.spinner("Traitement..."):
                result = process_webhook_lead(supabase, test_payload)

            if result["success"]:
                st.success(f"✅ Lead créé avec succès ! ID prospect : {result['prospect_id']}")
                reset_pipeline()
            else:
                st.error(f"❌ Erreur : {result['error']}")


def page_alertes(supabase):
    st.markdown('<p class="section-title">🔔 Alertes & Relances</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Surveillance automatique de vos clients et échantillons</p>', unsafe_allow_html=True)

    has_alert = False

    # ── ALERTES RÉTENTION : Clients Actifs sans interaction 45+ jours ──
    st.markdown("<p class='label-field' style='margin-top:8px;'>🚨 ALERTES DE RÉTENTION (45+ jours sans interaction)</p>", unsafe_allow_html=True)
    forty_five_days_ago = (datetime.now() - timedelta(days=45)).isoformat()
    try:
        retention_alerts = pd.DataFrame(
            supabase.table("prospects")
            .select("*")
            .eq("status", "Client Actif")
            .lte("last_action_date", forty_five_days_ago)
            .execute()
            .data
        )
    except Exception:
        retention_alerts = pd.DataFrame()

    if not retention_alerts.empty:
        has_alert = True
        for _, alert in retention_alerts.iterrows():
            last_date = alert.get("last_action_date", "")[:10]
            try:
                days = (datetime.now() - datetime.strptime(last_date, "%Y-%m-%d")).days
            except Exception:
                days = "?"
            st.markdown(
                f'<div class="alert-retention">'
                f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                f'<div>'
                f'<span style="font-weight:800; color:#dc2626; font-size:14px;">⚠️ {alert["company_name"]}</span>'
                f'<span style="font-size:11px; color:#991b1b;"> · Client Actif</span>'
                f'</div>'
                f'<span class="badge badge-red">{days} jours sans contact</span>'
                f'</div>'
                f'<p style="font-size:12px; color:#7f1d1d; margin:6px 0 0;">Dernier contact : {last_date} · Aucune interaction depuis plus de 45 jours.</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Ouvrir la fiche", key=f"ret_btn_{alert['id']}"):
                st.session_state["active_prospect_id"] = alert["id"]
                st.rerun()
    else:
        st.success("✅ Tous vos clients actifs sont à jour !")

    st.write("")

    # ── ALERTES SAMPLES : Échantillons sans feedback 15+ jours ──
    st.markdown("<p class='label-field'>🧪 ÉCHANTILLONS EN ATTENTE DE FEEDBACK (15+ jours)</p>", unsafe_allow_html=True)
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    try:
        sample_alerts = pd.DataFrame(
            supabase.table("samples")
            .select("*, prospects(company_name)")
            .is_("feedback", "null")
            .lte("date_sent", fifteen_days_ago)
            .execute()
            .data
        )
    except Exception:
        sample_alerts = pd.DataFrame()

    if not sample_alerts.empty:
        has_alert = True
        for _, alert in sample_alerts.iterrows():
            client = alert.get("prospects", {}).get("company_name", "—") if alert.get("prospects") else "—"
            st.markdown(
                f'<div class="alert-retention">'
                f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                f'<div>'
                f'<span style="font-weight:800; color:#dc2626; font-size:14px;">🧪 {client}</span>'
                f'<span style="font-size:11px; color:#991b1b;"> · {alert.get("product_name", "")}</span>'
                f'</div>'
                f'<span class="badge badge-red">Sans feedback</span>'
                f'</div>'
                f'<p style="font-size:12px; color:#7f1d1d; margin:6px 0 0;">'
                f'Ref : {alert.get("reference", "")} · Envoyé le {alert.get("date_sent", "")[:10]} · Aucun retour R&D.</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Ouvrir la fiche", key=f"sam_btn_{alert.get('prospect_id', alert['id'])}"):
                st.session_state["active_prospect_id"] = alert.get("prospect_id")
                st.rerun()
    else:
        st.success("✅ Tous vos échantillons ont des feedbacks !")


# =============================================================================
# 13. MAIN — ENTRY POINT
# =============================================================================

def main():
    # Auth
    if not check_auth():
        return

    # Connexions
    supabase = init_connections()
    if not supabase:
        st.stop()

    # Sidebar + routing
    selected_page = render_sidebar(supabase)

    # Gestion modal prospect
    if "open_new_id" in st.session_state:
        st.session_state["active_prospect_id"] = st.session_state.pop("open_new_id")
        reset_pipeline()

    if "active_prospect_id" in st.session_state:
        try:
            row_data = supabase.table("prospects").select("*").eq("id", st.session_state["active_prospect_id"]).execute().data[0]
            show_prospect_card(supabase, st.session_state["active_prospect_id"], row_data)
        except Exception:
            safe_del("active_prospect_id")

    # Pages routing
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
    page_fn(supabase)


# =============================================================================
# RUN
# =============================================================================
if __name__ == "__main__":
    main()
