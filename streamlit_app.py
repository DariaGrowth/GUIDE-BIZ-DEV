import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta
import io
import numpy as np
import time

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="Ingood Growth", page_icon="favicon.png", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* BACKGROUND */
        .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; color: #334155; }
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        
        button[aria-label="Close"] { margin-top: 8px; margin-right: 8px; }
        div[data-testid="stVerticalBlock"] { gap: 0rem; } 
        
        /* TEXT STYLES */
        .stMarkdown label p, .stTextInput label p, .stNumberInput label p, .stSelectbox label p, .stTextArea label p, .stDateInput label p {
            color: #64748b !important; font-size: 11px !important; font-weight: 700 !important;
            text-transform: uppercase !important; letter-spacing: 0.5px;
        }

        /* ICONS FILTER */
        .stSelectbox div[data-baseweb="select"], div[role="radiogroup"] label p, .stMarkdown p { 
            filter: grayscale(100%) contrast(120%); color: #334155;
        }
        
        /* --- BUTTONS --- */
        /* Sidebar & Modal Buttons (Visible Green) */
        [data-testid="stSidebar"] .stButton > button, 
        button[kind="primary"] {
            width: 100%; background-color: #047857 !important; color: white !important;
            border: none; border-radius: 6px; padding: 10px 16px; font-weight: 600; font-size: 14px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1); transition: all 0.2s ease;
        }
        [data-testid="stSidebar"] .stButton > button:hover,
        button[kind="primary"]:hover { 
            background-color: #065f46 !important; transform: translateY(-1px); 
        }
        
        /* Delete Button */
        button[kind="secondary"] {
            background-color: white !important; border: 1px solid #fee2e2 !important; color: #ef4444 !important;
        }

        /* --- PIPELINE ROW STYLING (THE POLISH) --- */
        
        /* 1. Container for the whole table to give it white bg */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white; border-radius: 8px; border: 1px solid #e2e8f0;
            padding: 0px; overflow: hidden; /* Important for hover effect on edges */
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }

        /* 2. HEADER ROW */
        .header-container {
            padding: 16px 20px;
            background-color: #ffffff;
            border-bottom: 1px solid #f1f5f9;
        }
        .header-text { 
            color: #047857; font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; 
        }

        /* 3. DATA ROWS (Hover & Spacing) */
        /* We can't style the st.columns container directly easily, so we style the content wrapper */
        
        /* INVISIBLE BUTTON (The clickable area) */
        /* This makes the button in the last column transparent but clickable */
        div[data-testid="column"] .stButton > button {
            background-color: transparent !important;
            color: transparent !important; /* Hide text */
            border: none !important;
            box-shadow: none !important;
            height: 40px !important; /* Make click area tall */
        }
        /* No hover effect on the button itself, handled by row */
        div[data-testid="column"] .stButton > button:hover {
            background-color: transparent !important;
        }

        /* ROW VISUALS */
        .cell-company { color: #0f172a; font-weight: 600; font-size: 14px; }
        .cell-text { color: #64748b; font-size: 13px; font-weight: 400; }
        .cell-prod { color: #047857; font-weight: 700; font-size: 13px; }
        .cell-link { color: #3b82f6; font-size: 13px; font-weight: 500; }
        
        /* Badges */
        .badge { padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; display: inline-block; }
        .bg-yellow { background: #fef9c3; color: #854d0e; }
        .bg-gray { background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0; }
        .bg-green { background: #dcfce7; color: #166534; }
        .bg-sample { background: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; padding: 3px 10px; }

        /* MENU */
        div[role="radiogroup"] > label > div:first-child { display: none !important; }
        div[role="radiogroup"] label {
            display: flex; align-items: center; width: 100%; padding: 8px 16px;
            margin-bottom: 2px; border-radius: 6px; border: none; cursor: pointer;
            color: #64748b; font-weight: 500; font-size: 15px; transition: all 0.2s;
        }
        div[role="radiogroup"] label[data-checked="true"] { background-color: rgba(16, 185, 129, 0.1) !important; color: #047857 !important; font-weight: 600; }
        div[role="radiogroup"] label[data-checked="true"] p { filter: none !important; color: #047857 !important; }
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
def get_all_contacts():
    c = pd.DataFrame(supabase.table("contacts").select("*").execute().data)
    if c.empty: return pd.DataFrame(columns=["name", "role", "company_name", "email", "phone"])
    return c
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

# --- 5. FICHE PROSPECT (MODAL) ---
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
            with c_m1: camp = st.text_input("Dernière Action", value=data.get("marketing_campaign", "") or "", placeholder="Ex: Promo...")
            with c_m2: 
                d_val = datetime.now().date()
                if data.get("last_action_date"): 
                    try: d_val = datetime.strptime(str(data["last_action_date"])[:10], "%Y-%m-%d").date()
                    except: pass
                date_act = st.date_input("Date", value=d_val, format="DD/MM/YYYY")
            st.markdown("---")
            if st.button("📧 Email AI"): st.code(ai_mail(f"Client: {data['company_name']}"))

    with c_right:
        t1, t2, t3 = st.tabs(["Contexte", "Suivi Échantillons", "Journal d'Activité"])
        with t1:
            c1, c2 = st.columns(2)
            with c1: prod = st.selectbox("Ingrédient", ["LEN", "PEP", "NEW"], index=["LEN", "PEP", "NEW"].index(data.get("product_interest", "LEN")))
            with c2: app = st.selectbox("Application", ["Boulangerie", "Sauces", "Confiserie"], index=0)
            pain = st.text_area("Besoin", value=data.get("tech_pain_points", ""), height=80)
            notes = st.text_area("Notes", value=data.get("tech_notes", ""), height=80)
            st.markdown("---"); st.markdown("<p style='font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase;'>CONTACTS CLÉS</p>", unsafe_allow_html=True)
            contacts = st.data_editor(get_sub_data("contacts", pid), column_config={"id": None}, num_rows="dynamic", use_container_width=True, key=f"ed_{pid}")

        with t2:
            st.info("ℹ️ Valider fiche technique.")
            with st.container(border=True):
                c1, c2, _, c3 = st.columns([1.5, 2, 0.1, 1.2]) 
                with c1: ref = st.text_input("Ref", key="nr")
                with c2: pr = st.selectbox("Produit", ["LEN", "PEP", "NEW"], key="np")
                with c3: 
                    st.write(""); st.write("")
                    if st.button("Sauvegarder", key="ss", type="primary"): 
                        supabase.table("samples").insert({"prospect_id": pid, "reference": ref, "product_name": pr, "status": "Envoyé", "date_sent": datetime.now().isoformat()}).execute(); st.rerun()
            st.write(""); st.markdown("##### Historique")
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
            if st.button("Ajouter", type="primary"): add_log(pid, "Note", n); st.rerun()
            for _, r in get_sub_data("activities", pid).iterrows(): st.caption(f"{r['date'][:10]}"); st.write(r['content'])

    st.markdown("---")
    cd, cs = st.columns([1, 4])
    with cd: 
        if st.button("🗑️ Supprimer", type="secondary"): 
            supabase.table("prospects").delete().eq("id", pid).execute(); reset_pipeline(); st.rerun()
    with cs:
        if st.button("Enregistrer & Fermer", type="primary", use_container_width=True):
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

# --- 7. AUTO-OPEN & ROUTING ---
if 'open_new_id' in st.session_state:
    st.session_state['active_prospect_id'] = st.session_state.pop('open_new_id'); reset_pipeline()

if 'active_prospect_id' in st.session_state:
    try: show_prospect_card(st.session_state['active_prospect_id'], supabase.table("prospects").select("*").eq("id", st.session_state['active_prospect_id']).execute().data[0])
    except: safe_del('active_prospect_id')

# --- 8. PAGES ---
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
    # --- 1. FILTER BOX (White Window) ---
    with st.container(border=True):
        f1, f2, f3, f4 = st.columns(4)
        with f1: st.selectbox("Produits", ["Tous Produits", "LEN", "PEP"], label_visibility="collapsed")
        with f2: st.selectbox("Statuts", ["Tous Statuts", "Prospection", "Test"], label_visibility="collapsed")
        with f3: st.selectbox("Salons", ["Tous Salons", "CFIA"], label_visibility="collapsed")
        with f4: st.selectbox("Pays", ["Tous Pays", "France"], label_visibility="collapsed")
    
    st.write("")
    
    # --- 2. TABLE (White Window) ---
    with st.container(border=True):
        # HEADER
        st.markdown('<div class="header-container">', unsafe_allow_html=True)
        h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([2.5, 1, 1.2, 1.2, 1.2, 1.5, 1, 0.5])
        def header(t): return f"<span class='header-text'>{t}</span>"
        h1.markdown(header("SOCIÉTÉ"), unsafe_allow_html=True)
        h2.markdown(header("PAYS"), unsafe_allow_html=True)
        h3.markdown(header("PRODUIT"), unsafe_allow_html=True)
        h4.markdown(header("STATUT"), unsafe_allow_html=True)
        h5.markdown(header("D. CONTACT"), unsafe_allow_html=True)
        h6.markdown(header("ACTION"), unsafe_allow_html=True)
        h7.markdown(header("ÉCHANTILLONS"), unsafe_allow_html=True)
        h8.markdown(header("ACT"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # DATA ROWS
        df = get_data()
        samples_all = pd.DataFrame(supabase.table("samples").select("prospect_id").execute().data)
        
        # Hover logic is handled by global CSS for the columns container
        for index, row in df.iterrows():
            # Injecting a unique class for hover effect on the specific row block is hard in streamlit loop
            # BUT we set global styles for buttons inside columns to be transparent
            
            # CSS hack: We wrap the row in a div with hover effect? 
            # Streamlit doesn't allow nesting st.columns inside html.
            # We will use the native layout but rely on the "invisible button" to capture clicks.
            
            # Spacer for padding top
            st.markdown(f"""
            <style>
            div[data-testid="column"] {{
                transition: background-color 0.2s;
            }}
            /* Make this specific row hoverable? Hard to scope. 
               We will just render the content cleanly with padding. */
            </style>
            <div style="padding: 18px 20px; border-bottom: 1px solid #f8fafc; transition: background 0.2s;" onmouseover="this.style.background='#f0fdf4';" onmouseout="this.style.background='transparent';">
            """, unsafe_allow_html=True)
            
            # Note: The onmouseover hack above affects only the div, NOT the st.columns which are rendered separately by Streamlit.
            # Streamlit renders columns in a flex container. We can't wrap them easily.
            # We revert to simple clean spacing.
            
            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2.5, 1, 1.2, 1.2, 1.2, 1.5, 1, 0.5])
            
            # Vertical Align Hack (using newlines or css) -> We use CSS on classes
            c1.markdown(f"<div style='margin-top:8px'><span class='cell-company'>{row['company_name']}</span></div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='margin-top:8px'><span class='cell-text'>{row['country']}</span></div>", unsafe_allow_html=True)
            c3.markdown(f"<div style='margin-top:8px'><span class='cell-prod'>{row['product_interest']}</span></div>", unsafe_allow_html=True)
            
            status = row['status'] or "Prospection"
            cls = "bg-green" if "Client" in status else "bg-yellow" if "Test" in status else "bg-gray"
            c4.markdown(f"<div style='margin-top:6px'><span class='badge {cls}'>{status.split(' ')[1] if ' ' in status else status}</span></div>", unsafe_allow_html=True)
            
            d_fmt = "-"
            if row['last_action_date']:
                d_fmt = datetime.strptime(row['last_action_date'][:10], "%Y-%m-%d").strftime("%d %b. %y")
            c5.markdown(f"<div style='margin-top:8px'><span class='cell-text'>{d_fmt}</span></div>", unsafe_allow_html=True)
            
            c6.markdown(f"<div style='margin-top:8px'><span class='cell-link'>{row.get('marketing_campaign') or '-'}</span></div>", unsafe_allow_html=True)
            
            has_s = False
            if not samples_all.empty:
                if not samples_all[samples_all['prospect_id'] == row['id']].empty: has_s = True
            c7.markdown(f"<div style='margin-top:6px'><span class='badge bg-sample'>⚗ En test</span></div>" if has_s else "<div style='margin-top:8px'>-</div>", unsafe_allow_html=True)
            
            # Invisible Button covers this area
            if c8.button("Open", key=f"r_{row['id']}"):
                st.session_state['active_prospect_id'] = row['id']; st.rerun()
            
            # Close wrapper (visual separator mainly)
            st.markdown("<div style='margin-bottom: 2px;'></div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 0; border: 0; border-top: 1px solid #f8fafc;'>", unsafe_allow_html=True)

elif pg == "Contacts":
    st.title("Annuaire Contacts")
    st.dataframe(get_all_contacts(), use_container_width=True)

elif pg == "À Relancer":
    st.title("À Relancer 🔔")
    s = pd.DataFrame(supabase.table("samples").select("*").execute().data)
    if not s.empty: st.dataframe(s[s['feedback'].isna()], use_container_width=True)
    else: st.success("OK")
