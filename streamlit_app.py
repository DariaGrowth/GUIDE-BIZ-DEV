import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta
import io
import numpy as np
import time

# --- 1. CONFIGURATION & STYLE (MODERN UI) ---
st.set_page_config(page_title="Ingood Growth", page_icon="favicon.png", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* GLOBAL APP STYLE */
        .stApp { background-color: #f1f5f9; font-family: 'Inter', sans-serif; color: #0f172a; }
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        
        /* HIDE DEFAULT STREAMLIT ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        button[aria-label="Close"] { margin-top: 8px; margin-right: 8px; }

        /* --- TYPOGRAPHY & COLORS --- */
        .stMarkdown label p, .stTextInput label p, .stNumberInput label p, .stSelectbox label p, .stTextArea label p {
            color: #64748b !important; font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.5px;
        }
        
        /* MONOCHROME ICONS FILTER */
        .stSelectbox div[data-baseweb="select"], div[role="radiogroup"] label p, .stMarkdown p { 
            filter: grayscale(100%) contrast(120%); color: #334155;
        }

        /* --- BUTTONS (INGOOD GREEN) --- */
        .stButton > button {
            width: 100%; background-color: #047857 !important; color: white !important;
            border: none; border-radius: 6px; padding: 10px 16px; font-weight: 600; font-size: 14px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1); transition: all 0.2s ease;
        }
        .stButton > button:hover { background-color: #065f46 !important; transform: translateY(-1px); }

        /* RED DELETE BUTTON */
        div[data-testid="column"] button[kind="secondary"] {
            background-color: white !important; border: 1px solid #fee2e2 !important; color: #ef4444 !important;
        }
        div[data-testid="column"] button[kind="secondary"]:hover {
            background-color: #fef2f2 !important; border-color: #ef4444 !important;
        }

        /* TRANSPARENT ACTION BUTTON (ARROW) */
        .action-btn button {
            background-color: transparent !important; border: none !important; color: #94a3b8 !important; 
            box-shadow: none !important; font-size: 18px !important; padding: 0 !important;
        }
        .action-btn button:hover { color: #047857 !important; background-color: transparent !important; transform: translateX(2px); }

        /* --- MODERN PIPELINE DESIGN (CSS GRID) --- */
        
        /* 1. Filter Container */
        .filter-box {
            background-color: white; border: 1px solid #e2e8f0; border-radius: 8px;
            padding: 16px 20px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }

        /* 2. Table Container */
        .table-container {
            background-color: white; border: 1px solid #e2e8f0; border-radius: 8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02); overflow: hidden;
        }

        /* 3. Header Row */
        .header-row {
            display: grid;
            grid-template-columns: 2.5fr 1fr 1.2fr 1.2fr 1.2fr 1.5fr 1fr 0.5fr;
            background-color: #f8fafc; /* Light Gray Header */
            border-bottom: 1px solid #e2e8f0;
            padding: 12px 24px;
            align-items: center;
        }
        
        /* Header Text (Dark Green, Bold like LENGOOD) */
        .header-title {
            color: #047857; /* Pantone Ingood Green */
            font-weight: 800; /* Extra Bold */
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* 4. Data Row */
        .data-row {
            display: grid;
            grid-template-columns: 2.5fr 1fr 1.2fr 1.2fr 1.2fr 1.5fr 1fr 0.5fr;
            border-bottom: 1px solid #f1f5f9;
            padding: 10px 24px;
            align-items: center;
            background-color: white;
            transition: background 0.15s;
        }
        .data-row:hover { background-color: #f8fafc; }
        .data-row:last-child { border-bottom: none; }

        /* Cell Typography */
        .cell-company { font-weight: 700; color: #0f172a; font-size: 13px; }
        .cell-text { color: #64748b; font-size: 13px; font-weight: 500; }
        .cell-product { color: #047857; font-weight: 700; font-size: 12px; } /* Green Product */
        .cell-action { color: #3b82f6; font-size: 13px; font-weight: 500; cursor: pointer; } /* Blue Link */

        /* Badges */
        .badge { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; display: inline-flex; align-items: center; }
        .bg-yellow { background: #fef9c3; color: #854d0e; } /* Test */
        .bg-gray { background: #f1f5f9; color: #475569; } /* Prospection */
        .bg-green { background: #dcfce7; color: #166534; } /* Client */
        .bg-sample { background: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; padding: 2px 8px; gap: 4px; } /* Sample */

        /* Override Streamlit Column Spacing for tight table */
        div[data-testid="column"] { padding: 0 !important; }
        div[data-testid="stVerticalBlock"] { gap: 0 !important; }
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
def reset_pipeline(): st.session_state['pipeline_key'] += 1; safe_del('active_prospect_id')
def safe_del(key): 
    if key in st.session_state: del st.session_state[key]

# --- 4. DATA ---
def get_data(): return pd.DataFrame(supabase.table("prospects").select("*").order("last_action_date", desc=True).execute().data)
def get_sub_data(t, pid):
    d = supabase.table(t).select("*").eq("prospect_id", pid).order("id", desc=True).execute().data
    df = pd.DataFrame(d)
    if df.empty:
        if t == "contacts": return pd.DataFrame(columns=["id", "name", "role", "email", "phone"])
        if t == "samples": return pd.DataFrame(columns=["id", "date_sent", "product_name", "reference", "status", "feedback"])
        if t == "activities": return pd.DataFrame(columns=["id", "date", "type", "content"])
    if t == "contacts":
        for c in ["name", "role", "email", "phone"]: 
            if c not in df.columns: df[c] = ""
            df[c] = df[c].astype(str).replace({"nan": "", "None": "", "none": ""})
    return df
def count_relances():
    s = pd.DataFrame(supabase.table("samples").select("*").execute().data)
    if s.empty: return 0
    now = datetime.now(); cnt = 0
    for _, r in s.iterrows():
        if r.get("date_sent"):
            d = datetime.strptime(r["date_sent"][:10], "%Y-%m-%d"); diff = (now - d).days
            if diff > 15 and (not str(r.get("feedback") or "").strip() or str(r.get("feedback")).lower() == "none"): cnt += 1
    return cnt
def add_log(pid, t, c):
    supabase.table("activities").insert({"prospect_id": pid, "type": t, "content": c, "date": datetime.now().isoformat()}).execute()
    supabase.table("prospects").update({"last_action_date": datetime.now().strftime("%Y-%m-%d")}).eq("id", pid).execute()
def ai_mail(ctx):
    return genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Act as email assistant. French. Context: {ctx}.").text

# --- 5. FICHE PROSPECT ---
@st.dialog(" ", width="large")
def show_prospect_card(pid, data):
    pid = int(pid)
    st.markdown(f"<h2 style='margin-top: -30px; margin-bottom: 25px; font-size: 26px; color: #1e293b; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; font-weight: 700;'>{data['company_name']}</h2>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 2], gap="large")

    with c_left:
        with st.container(border=True):
            name = st.text_input("Société", value=data['company_name'], key=f"n_{pid}")
            opts = ["🔭 Prospection", "📋 Qualification", "📦 Echantillon", "🔬 Test R&D", "🏭 Essai industriel", "⚖️ Négociation", "✅ Client signé"]
            curr = data.get("status", "Prospection")
            stat = st.selectbox("Statut", opts, index=next((i for i, s in enumerate(opts) if curr in s), 0))
            c1, c2 = st.columns(2)
            with c1: pays = st.text_input("Pays", value=data.get("country", ""))
            with c2: vol = st.number_input("Potentiel (T)", value=float(data.get("potential_volume") or 0))
            salon = st.text_input("Source", value=data.get("last_salon", ""))
            st.write("")
            c_m1, c_m2 = st.columns([1.5, 1])
            with c_m1: camp = st.text_input("Dernière Action", value=data.get("marketing_campaign", ""), placeholder="Ex: Promo...")
            with c_m2: 
                d_val = datetime.now().date()
                if data.get("last_action_date"): 
                    try: d_val = datetime.strptime(str(data["last_action_date"])[:10], "%Y-%m-%d").date()
                    except: pass
                date_act = st.date_input("Date", value=d_val, format="DD/MM/YYYY")
            st.markdown("---")
            if st.button("📧 Email AI"): st.code(ai_mail(f"Client: {data['company_name']}"))

    with c_right:
        t1, t2, t3 = st.tabs(["Contexte", "Suivi Échantillons", "Journal"])
        with t1:
            c1, c2 = st.columns(2)
            with c1: prod = st.selectbox("Ingrédient", ["LEN", "PEP", "NEW"], index=["LEN", "PEP", "NEW"].index(data.get("product_interest", "LEN")))
            with c2: app = st.selectbox("Application", ["Boulangerie", "Sauces", "Confiserie"], index=0)
            pain = st.text_area("Besoin", value=data.get("tech_pain_points", ""), height=80)
            notes = st.text_area("Notes", value=data.get("tech_notes", ""), height=80)
            st.markdown("---"); st.caption("CONTACTS CLÉS")
            contacts = st.data_editor(get_sub_data("contacts", pid), column_config={"id": None}, num_rows="dynamic", use_container_width=True, key=f"ed_{pid}")

        with t2:
            st.info("ℹ️ Valider fiche technique.")
            with st.container(border=True):
                c1, c2, _, c3 = st.columns([1.5, 2, 0.1, 1.2])
                with c1: ref = st.text_input("Ref", key="nr")
                with c2: pr = st.selectbox("Produit", ["LEN", "PEP"], key="np")
                with c3: 
                    st.write(""); st.write("")
                    if st.button("Sauvegarder", key="ss"): 
                        supabase.table("samples").insert({"prospect_id": pid, "reference": ref, "product_name": pr, "status": "Envoyé", "date_sent": datetime.now().isoformat()}).execute(); st.rerun()
            st.write(""); st.caption("Historique")
            for _, r in get_sub_data("samples", pid).iterrows():
                with st.container(border=True):
                    c_i, c_d = st.columns([9, 1])
                    with c_i: 
                        st.markdown(f"**{r['product_name']}** | {r['reference']} <span style='color:gray; font-size:12px'>({r['date_sent'][:10]})</span>", unsafe_allow_html=True)
                        fb = st.text_area("Feedback", value=r['feedback'] or "", key=f"fb_{r['id']}", height=60, label_visibility="collapsed")
                    with c_d:
                        st.write("")
                        if st.button("🗑️", key=f"d_{r['id']}", type="secondary"): supabase.table("samples").delete().eq("id", r['id']).execute(); st.rerun()
                    if fb != (r['feedback'] or ""): supabase.table("samples").update({"feedback": fb}).eq("id", r['id']).execute(); st.toast("Saved")

        with t3:
            n = st.text_area("Note...", key="nn"); 
            if st.button("Ajouter"): add_log(pid, "Note", n); st.rerun()
            for _, r in get_sub_data("activities", pid).iterrows(): st.caption(f"{r['date'][:10]}"); st.write(r['content'])

    st.markdown("---")
    cd, cs = st.columns([1, 4])
    with cd: 
        if st.button("🗑️ Supprimer", type="secondary"): 
            supabase.table("prospects").delete().eq("id", pid).execute(); reset_pipeline(); st.rerun()
    with cs:
        if st.button("Enregistrer & Fermer"):
            supabase.table("prospects").update({
                "company_name": name, "status": stat, "country": pays, "potential_volume": vol, "last_salon": salon,
                "marketing_campaign": camp, "last_action_date": date_act.isoformat(), "product_interest": prod, "segment": app, "tech_pain_points": pain, "tech_notes": notes
            }).eq("id", pid).execute()
            if not contacts.empty:
                for r in contacts.to_dict('records'):
                    if r.get("name"):
                        d = {"prospect_id": pid, "name": r["name"], "role": r.get("role",""), "email": r.get("email",""), "phone": r.get("phone","")}
                        if r.get("id"): supabase.table("contacts").upsert({**d, "id": r["id"]}).execute()
                        else: supabase.table("contacts").insert(d).execute()
            reset_pipeline(); st.rerun()

# --- 6. SIDEBAR ---
with st.sidebar:
    st.image("favicon.png", width=65)
    if st.button("Nouveau Projet"):
        res = supabase.table("prospects").insert({"company_name": "Nouveau Prospect"}).execute()
        st.session_state['open_new_id'] = res.data[0]['id']; st.rerun()
    st.write("")
    rc = count_relances()
    pg = st.radio("Nav", ["Tableau de Bord", "Pipeline", "Contacts", "À Relancer"], format_func=lambda x: f"{'🔔' if x=='À Relancer' and rc else '≡'} {x}", label_visibility="collapsed")
    st.markdown("---"); st.caption("👤 Daria Growth")

# --- 7. ROUTING ---
if 'open_new_id' in st.session_state:
    st.session_state['active_prospect_id'] = st.session_state.pop('open_new_id'); reset_pipeline()

if 'active_prospect_id' in st.session_state:
    try: show_prospect_card(st.session_state['active_prospect_id'], supabase.table("prospects").select("*").eq("id", st.session_state['active_prospect_id']).execute().data[0])
    except: safe_del('active_prospect_id')

if pg == "Tableau de Bord":
    st.title("Tableau de Bord")
    df = get_data()
    c1, c2, c3, c4 = st.columns(4)
    if not df.empty:
        c1.metric("Projets", len(df)); c2.metric("En Test", len(df[df['status'].str.contains('Test', na=False)]))
        c3.metric("Volume", int(df['potential_volume'].sum())); c4.metric("Clients", len(df[df['status'].str.contains('Client', na=False)]))
        cl, cr = st.columns(2)
        with cl: st.plotly_chart(px.pie(df, names='product_interest', color_discrete_sequence=['#047857', '#10b981']), use_container_width=True)
        with cr: st.plotly_chart(px.bar(df['status'].value_counts(), color_discrete_sequence=['#047857']), use_container_width=True)

elif pg == "Pipeline":
    # 1. FILTERS (SEPARATE CARD)
    with st.container():
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns(4)
        with f1: st.selectbox("Produits", ["Tous", "LEN", "PEP"], label_visibility="collapsed")
        with f2: st.selectbox("Statuts", ["Tous", "Prospection", "Test"], label_visibility="collapsed")
        with f3: st.selectbox("Salons", ["Tous", "CFIA"], label_visibility="collapsed")
        with f4: st.selectbox("Pays", ["Tous", "France"], label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. TABLE (SEPARATE CARD)
    with st.container():
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        
        # TABLE HEADER (GREY BG, DARK GREEN TEXT)
        st.markdown('''
            <div class="header-row">
                <span class="header-title">SOCIÉTÉ</span>
                <span class="header-title">PAYS</span>
                <span class="header-title">PRODUIT</span>
                <span class="header-title">STATUT</span>
                <span class="header-title">DERNIER CONTACT</span>
                <span class="header-title">DERNIER ACTION</span>
                <span class="header-title">ÉCHANTILLONS</span>
                <span class="header-title">ACT</span>
            </div>
        ''', unsafe_allow_html=True)

        # DATA ROWS
        df = get_data()
        samples_all = pd.DataFrame(supabase.table("samples").select("prospect_id").execute().data)
        
        for index, row in df.iterrows():
            # PREPARE DATA FOR HTML
            status = row['status'] or "Prospection"
            badge_class = "bg-green" if "Client" in status else "bg-yellow" if "Test" in status else "bg-gray"
            short_stat = status.split(" ")[1] if " " in status else status
            
            d_fmt = "-"
            if row['last_action_date']:
                d_fmt = datetime.strptime(row['last_action_date'][:10], "%Y-%m-%d").strftime("%d %b. %y")
            
            act = row.get('marketing_campaign') or "-"
            
            has_s = False
            if not samples_all.empty:
                if not samples_all[samples_all['prospect_id'] == row['id']].empty: has_s = True
            
            sample_html = f'<span class="badge bg-sample">⚗ En test</span>' if has_s else "-"

            # RENDER ROW USING COLUMNS TO ALLOW CLICKABLE BUTTON
            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2.5, 1, 1.2, 1.2, 1.2, 1.5, 1, 0.5])
            
            # CSS WRAPPER START
            st.markdown('<div class="data-row" style="margin-top:-10px; margin-bottom:-10px; padding-top:12px; padding-bottom:12px;">', unsafe_allow_html=True)
            
            # INJECT CONTENT INTO COLUMNS (To align with the grid)
            # Note: We rely on the CSS grid defined in .data-row, so we just populate the streamlit columns to hold the button logic
            # This is a hybrid approach: Streamlit handles the button, CSS handles the look.
            
            # We construct a single HTML block for the non-interactive parts to ensure perfect alignment
            # But wait, st.columns inside a loop creates separate divs. 
            # BEST APPROACH: Use a single markdown block for the visual row, and a transparent button overlaid or next to it.
            # However, overlaying is hard in Streamlit.
            # Let's use the native columns but style them.
            
            with c1: st.markdown(f'<span class="cell-company">{row["company_name"]}</span>', unsafe_allow_html=True)
            with c2: st.markdown(f'<span class="cell-text">{row["country"]}</span>', unsafe_allow_html=True)
            with c3: st.markdown(f'<span class="cell-product">{row["product_interest"]}</span>', unsafe_allow_html=True)
            with c4: st.markdown(f'<span class="badge {badge_class}">{short_stat}</span>', unsafe_allow_html=True)
            with c5: st.markdown(f'<span class="cell-text">{d_fmt}</span>', unsafe_allow_html=True)
            with c6: st.markdown(f'<span class="cell-action">{act}</span>', unsafe_allow_html=True)
            with c7: st.markdown(sample_html, unsafe_allow_html=True)
            with c8: 
                # Transparent Button via CSS class 'action-btn'
                st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                if st.button("›", key=f"r_{row['id']}"):
                    st.session_state['active_prospect_id'] = row['id']; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True) # End Row CSS wrapper
            st.markdown("<div style='border-bottom: 1px solid #f1f5f9;'></div>", unsafe_allow_html=True) # Separator

        st.markdown('</div>', unsafe_allow_html=True) # End Table Container

elif pg == "Contacts":
    st.title("Annuaire"); st.dataframe(get_all_contacts(), use_container_width=True)

elif pg == "À Relancer":
    st.title("Relances"); 
    s = pd.DataFrame(supabase.table("samples").select("*").execute().data)
    if not s.empty: st.dataframe(s[s['feedback'].isna()], use_container_width=True)
    else: st.success("OK")
