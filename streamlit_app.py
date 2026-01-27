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

        .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; color: #334155; }
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        
        /* HIDE DIALOG HEADER */
        div[data-testid="stDialog"] div[data-testid="stVerticalBlock"] > div:first-child { display: none; }
        button[aria-label="Close"] { margin-top: 8px; margin-right: 8px; }
        
        /* LABELS */
        .stMarkdown label p, .stTextInput label p, .stNumberInput label p, .stSelectbox label p, .stTextArea label p {
            color: #94a3b8 !important; font-size: 11px !important; font-weight: 700 !important;
            text-transform: uppercase !important; letter-spacing: 0.5px;
        }

        /* MONOCHROME SELECT ICONS */
        div[data-testid="stSelectbox"] div[data-baseweb="select"] { filter: grayscale(100%); color: #475569; }
        
        /* BUTTON STYLES */
        .stButton > button {
            width: 100%; background-color: #047857 !important; color: white !important;
            border: none; border-radius: 8px; padding: 12px 16px; font-weight: 600; font-size: 15px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05); transition: all 0.2s ease;
        }
        .stButton > button:hover { transform: translateY(-1px); background-color: #065f46 !important; }
        
        /* SIDEBAR MENU */
        div[role="radiogroup"] > label > div:first-child { display: none !important; }
        div[role="radiogroup"] label {
            display: flex; align-items: center; width: 100%; padding: 10px 16px;
            margin-bottom: 4px; border-radius: 6px; border: none; cursor: pointer;
            color: #64748b; font-weight: 500; font-size: 15px; transition: all 0.2s;
        }
        div[role="radiogroup"] label p { font-size: 18px; margin: 0; display: flex; align-items: center; gap: 12px; color: transparent; text-shadow: 0 0 0 #64748b; }
        div[role="radiogroup"] label[data-checked="true"] { background-color: rgba(16, 185, 129, 0.1) !important; color: #047857 !important; font-weight: 600; }
        div[role="radiogroup"] label[data-checked="true"] p { text-shadow: 0 0 0 #047857; }

        /* SAMPLE CARD STYLE */
        .sample-card {
            background-color: white; border: 1px solid #e2e8f0; border-radius: 8px;
            padding: 15px; margin-bottom: 10px; border-left: 4px solid #047857;
        }
        .warning-badge {
            background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 700;
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

# --- 3. DATA FUNCTIONS ---
def get_data():
    return pd.DataFrame(supabase.table("prospects").select("*").order("last_action_date", desc=True).execute().data)

def get_sub_data(table, prospect_id):
    pid = int(prospect_id)
    data = supabase.table(table).select("*").eq("prospect_id", pid).order("id", desc=True).execute().data
    df = pd.DataFrame(data)
    
    if df.empty:
        if table == "contacts":
            df = pd.DataFrame(columns=["id", "name", "role", "email", "phone"])
        elif table == "samples":
            return pd.DataFrame(columns=["id", "date_sent", "product_name", "reference", "status", "feedback"])
        elif table == "activities":
            return pd.DataFrame(columns=["id", "date", "type", "content"])
            
    if table == "contacts":
        for col in ["name", "role", "email", "phone"]:
            if col not in df.columns: df[col] = ""
            df[col] = df[col].astype(str).replace({"nan": "", "None": "", "none": ""})
    return df

def get_all_contacts():
    contacts = pd.DataFrame(supabase.table("contacts").select("*").execute().data)
    if contacts.empty: return pd.DataFrame(columns=["name", "role", "company_name", "email", "phone"])
    return contacts

# Функция подсчета просроченных образцов
def count_relances():
    samples = pd.DataFrame(supabase.table("samples").select("*").execute().data)
    if samples.empty: return 0
    
    today = datetime.now()
    count = 0
    for _, row in samples.iterrows():
        # Если есть дата отправки
        if row.get("date_sent"):
            sent_date = datetime.strptime(row["date_sent"][:10], "%Y-%m-%d")
            delta = (today - sent_date).days
            # Если прошло > 15 дней и нет фидбека (или он пустой)
            feedback = str(row.get("feedback") or "").strip()
            if delta > 15 and (not feedback or feedback.lower() == "none"):
                count += 1
    return count

def add_log(pid, type_act, content):
    pid = int(pid)
    supabase.table("activities").insert({"prospect_id": pid, "type": type_act, "content": content, "date": datetime.now().isoformat()}).execute()
    supabase.table("prospects").update({"last_action_date": datetime.now().strftime("%Y-%m-%d")}).eq("id", pid).execute()

# --- 4. AI ---
def transcribe_audio(audio_file):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([ "Transcribe to French.", {"mime_type": "audio/wav", "data": audio_file.read()}])
    return response.text

def ai_email_assistant(context_text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model.generate_content(f"Act as email assistant. French. Context: {context_text}.").text

# --- 5. FICHE PROSPECT (MODAL) ---
@st.dialog(" ", width="large")
def show_prospect_card(pid, data):
    pid = int(pid)
    
    # Header
    st.markdown(f"<h2 style='margin-top: -45px; margin-bottom: 25px; font-size: 26px; color: #1e293b; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; font-weight: 700;'>{data['company_name']}</h2>", unsafe_allow_html=True)

    c_left, c_right = st.columns([1, 2], gap="large")

    # --- LEFT COLUMN (ADMIN) ---
    with c_left:
        with st.container(border=True):
            new_company_name = st.text_input("Société / Client", value=data['company_name'], key=f"title_{pid}")
            
            status_opts = ["🔭 Prospection", "📋 Qualification", "📦 Echantillon", "🔬 Test R&D", "🏭 Essai industriel", "⚖️ Négociation", "✅ Client signé"]
            curr = data.get("status", "Prospection")
            idx = 0
            for i, s in enumerate(status_opts):
                if curr in s or s.split(" ", 1)[1] in curr: idx = i; break
            stat = st.selectbox("Statut Pipeline", status_opts, index=idx)
            
            c_l1, c_l2 = st.columns(2)
            with c_l1: pays = st.text_input("Pays", value=data.get("country", ""))
            with c_l2: vol = st.number_input("Potentiel (T)", value=float(data.get("potential_volume") or 0))
            
            salon = st.text_input("Source / Salon", value=data.get("last_salon", ""))
            st.write("")
            cfia = st.checkbox("🔥 Prio CFIA", value=data.get("cfia_priority", False))

            st.markdown("---")
            if st.button("📧 Email AI", use_container_width=True):
                 res = ai_email_assistant(f"Client: {data['company_name']}")
                 st.code(res)

    # --- RIGHT COLUMN (WORK) ---
    with c_right:
        tab1, tab2, tab3 = st.tabs(["Contexte & Technique", "Suivi Échantillons", "Journal"])

        # TAB 1: TECH + CONTACTS
        with tab1:
            with st.form("main_form"):
                c_t1, c_t2 = st.columns(2)
                with c_t1:
                    prod_opts = ["LEN", "PEP", "NEW"]
                    curr_prod = data.get("product_interest", "LEN")
                    prod = st.selectbox("Ingrédient", prod_opts, index=prod_opts.index(curr_prod) if curr_prod in prod_opts else 0)
                with c_t2:
                    app_opts = ["Boulangerie / Pâtisserie", "Sauces", "Plats Cuisinés", "Confiserie"]
                    curr_app = data.get("segment", "Boulangerie / Pâtisserie")
                    app = st.selectbox("Application", app_opts, index=app_opts.index(curr_app) if curr_app in app_opts else 0)
                
                pain = st.text_area("Problématique / Besoin", value=data.get("tech_pain_points", ""), height=80)
                notes = st.text_area("Notes Techniques", value=data.get("tech_notes", ""), height=80)

                st.markdown("---")
                st.markdown("<p style='font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase;'>CONTACTS CLÉS</p>", unsafe_allow_html=True)
                
                contacts_df = get_sub_data("contacts", pid)
                edited_contacts = st.data_editor(
                    contacts_df,
                    column_config={
                        "id": None, 
                        "name": st.column_config.TextColumn("Nom", required=True),
                        "role": st.column_config.TextColumn("Poste"),
                        "email": st.column_config.TextColumn("Email"),
                        "phone": st.column_config.TextColumn("Tél")
                    },
                    column_order=("name", "role", "email", "phone"), 
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"editor_{pid}"
                )

                st.write("")
                if st.form_submit_button("💾 Enregistrer Tout", type="primary", use_container_width=True):
                    with st.spinner("Sauvegarde..."):
                        # 1. Update Prospect
                        supabase.table("prospects").update({
                            "company_name": new_company_name, "status": stat, "country": pays, 
                            "potential_volume": vol, "last_salon": salon, "cfia_priority": cfia,
                            "product_interest": prod, "segment": app, "tech_pain_points": pain, "tech_notes": notes
                        }).eq("id", pid).execute()
                        
                        # 2. Update Contacts (FIXED)
                        if not edited_contacts.empty:
                            # Convert to list of dicts to handle easily
                            records = edited_contacts.to_dict('records')
                            
                            for row in records:
                                name_val = str(row.get("name", "")).strip()
                                
                                # Skip empty rows
                                if not name_val or name_val.lower() == "nan": continue
                                
                                contact_data = {
                                    "prospect_id": pid,
                                    "name": name_val,
                                    "role": str(row.get("role", "")).strip(),
                                    "email": str(row.get("email", "")).strip(),
                                    "phone": str(row.get("phone", "")).strip()
                                }
                                
                                raw_id = row.get("id")
                                # If ID exists (float or int or string number) -> Upsert
                                if pd.notna(raw_id) and str(raw_id).replace('.','',1).isdigit():
                                     contact_data["id"] = int(float(raw_id))
                                     supabase.table("contacts").upsert(contact_data).execute()
                                else:
                                     # Insert new
                                     supabase.table("contacts").insert(contact_data).execute()
                        
                        time.sleep(1)
                    st.toast("✅ Modifié !")
                    st.rerun()

        # TAB 2: SAMPLE CARDS (REDESIGNED)
        with tab2:
            st.info("ℹ️ Protocole R&D : Toujours valider la fiche technique avant envoi.")
            
            # Formulaire d'envoi
            with st.container(border=True):
                c_s1, c_s2, c_s3 = st.columns([3, 1, 1])
                new_ref = c_s1.text_input("Référence (ex: Lot A12)", key="new_ref")
                new_prod = c_s2.selectbox("Produit", ["LEN", "PEP", "NEW"], key="new_prod")
                
                # Aligning button
                c_s3.write("") 
                c_s3.write("") 
                if c_s3.button("Sauvegarder", type="primary", use_container_width=True):
                    if new_ref:
                        supabase.table("samples").insert({
                            "prospect_id": pid, "reference": new_ref, "product_name": new_prod, 
                            "status": "Envoyé", "date_sent": datetime.now().isoformat()
                        }).execute()
                        st.rerun()

            st.write("")
            st.markdown("##### Historique & Feedback")
            
            # Список образцов (Карточки)
            samples = get_sub_data("samples", pid)
            if not samples.empty:
                for idx, row in samples.iterrows():
                    # Calculate delay
                    sent_date = datetime.strptime(row['date_sent'][:10], "%Y-%m-%d")
                    days_diff = (datetime.now() - sent_date).days
                    
                    # Card Container
                    with st.container(border=True):
                        # Header line
                        c_card1, c_card2 = st.columns([4, 1])
                        date_str = sent_date.strftime("%d %b %Y")
                        
                        # Warning Badge Logic
                        warning_html = ""
                        current_feedback = str(row['feedback'] or "")
                        if days_diff > 15 and (not current_feedback or current_feedback.lower() == "none"):
                            warning_html = f"<span class='warning-badge'>⚠️ Relance nécessaire (+{days_diff}j)</span>"
                        
                        c_card1.markdown(f"**{row['product_name']}** | Lot: {row['reference']} <span style='color:gray; font-size:12px'>({date_str})</span> {warning_html}", unsafe_allow_html=True)
                        
                        # Feedback input that saves automatically on blur/enter
                        new_fb = st.text_area(
                            "Feedback Client", 
                            value=current_feedback if current_feedback != "None" else "", 
                            key=f"fb_{row['id']}", 
                            height=70,
                            placeholder="En attente de retour..."
                        )
                        
                        # Save feedback if changed
                        if new_fb != current_feedback:
                            supabase.table("samples").update({"feedback": new_fb}).eq("id", row['id']).execute()
                            st.toast("Feedback enregistré !")
                            time.sleep(0.5)
                            st.rerun()

        # TAB 3: JOURNAL
        with tab3:
            with st.form("act_form", clear_on_submit=True):
                note = st.text_area("Note...")
                if st.form_submit_button("Ajouter", use_container_width=True):
                    add_log(pid, "Note", note)
                    time.sleep(1); st.rerun()
            st.markdown("### Historique")
            activities = get_sub_data("activities", pid)
            for _, row in activities.iterrows():
                with st.chat_message("user"):
                    st.caption(f"{row['date'][:10]} | {row['type']}")
                    st.write(row['content'])

# --- 6. SIDEBAR ---
with st.sidebar:
    st.image("favicon.png", width=65)
    
    if st.button("Nouveau Projet", use_container_width=True):
        res = supabase.table("prospects").insert({"company_name": "Nouveau Prospect"}).execute()
        if res.data:
            st.session_state['open_new_id'] = res.data[0]['id']
            st.rerun()
    
    st.write("") 
    
    # Calculate relance count
    relance_count = count_relances()
    
    icons = {"Tableau de Bord": "⊞", "Pipeline": "≡", "Contacts": "👤", "Kanban": "☷", "Échantillons": "⚗", "À Relancer": "🔔"}
    
    def format_func(option):
        if option == "À Relancer" and relance_count > 0:
            return f"{icons[option]}  {option} ({relance_count})"
        return f"{icons[option]}  {option}"

    menu_options = ["Tableau de Bord", "Pipeline", "Contacts", "Kanban", "Échantillons", "À Relancer"]
    page = st.radio("Navigation", menu_options, format_func=format_func, label_visibility="collapsed")
    
    st.markdown("---")
    st.caption("👤 Daria Growth")

# --- 7. AUTO-OPEN ---
if 'open_new_id' in st.session_state:
    new_pid = st.session_state['open_new_id']
    try:
        data = supabase.table("prospects").select("*").eq("id", new_pid).execute().data[0]
        del st.session_state['open_new_id']
        show_prospect_card(new_pid, data)
    except: pass

# --- 8. PAGES ---
if page == "Tableau de Bord":
    st.title("Tableau de Bord")
    df = get_data()
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Projets", len(df))
        c2.metric("En Test", len(df[df['status'].astype(str).str.contains('Test')]))
        c3.metric("Volume", f"{df['potential_volume'].sum():.0f}")
        c4.metric("Clients", len(df[df['status'].astype(str).str.contains('Client')]))
        
        cl, cr = st.columns(2)
        with cl:
            fig = px.pie(df, names='segment', color_discrete_sequence=['#047857', '#10b981', '#34d399', '#6ee7b7'], hole=0.7)
            fig.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            cnt = df['status'].value_counts().reset_index()
            fig = px.bar(cnt, x='status', y='count', color_discrete_sequence=['#047857'])
            fig.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

elif page == "Pipeline":
    st.title("Pipeline")
    st.markdown("<p class='caption'>Suivi des projets R&D et commerciaux.</p>", unsafe_allow_html=True)
    df = get_data()
    if not df.empty:
        c_search, c_space = st.columns([1, 3])
        search = c_search.text_input("Recherche", placeholder="Société...", label_visibility="collapsed")
        if search: df = df[df.apply(lambda x: search.lower() in str(x.values).lower(), axis=1)]
        df['company_name'] = df['company_name'].str.upper()
        df['actions'] = "›" 
        
        df = df.reset_index(drop=True)
        st.write("")
        selection = st.dataframe(
            df,
            column_order=("company_name", "country", "product_interest", "status", "last_action_date", "cfia_priority", "actions"),
            column_config={
                "company_name": st.column_config.TextColumn("Société", width="medium"),
                "country": st.column_config.TextColumn("Pays"),
                "product_interest": st.column_config.TextColumn("Produit"),
                "status": st.column_config.TextColumn("Statut", width="medium"),
                "last_action_date": st.column_config.DateColumn("Dernier Contact", format="DD MMM YYYY"),
                "cfia_priority": st.column_config.CheckboxColumn("CFIA", width="small"),
                "actions": st.column_config.TextColumn(" ", width="small")
            },
            hide_index=True, use_container_width=True, on_select="rerun", selection_mode="single-row"
        )
        if selection.selection.rows:
            idx = selection.selection.rows[0]
            row = df.iloc[idx]
            show_prospect_card(int(row['id']), row)

elif page == "Contacts":
    st.title("Annuaire Contacts")
    all_c = get_all_contacts()
    if not all_c.empty:
        search = st.text_input("Recherche contact...", placeholder="Nom, email...")
        if search:
            mask = all_c.apply(lambda x: search.lower() in str(x.values).lower(), axis=1)
            all_c = all_c[mask]
        st.dataframe(all_c, column_order=("name", "role", "company_name", "email", "phone"), hide_index=True, use_container_width=True)
    else: st.info("Aucun contact trouvé.")

elif page == "À Relancer":
    st.title("À Relancer 🔔")
    
    # Advanced logic for Relance page
    samples = pd.DataFrame(supabase.table("samples").select("*").execute().data)
    if not samples.empty:
        today = datetime.now()
        alerts = []
        
        for _, row in samples.iterrows():
            if row.get("date_sent"):
                sent_date = datetime.strptime(row["date_sent"][:10], "%Y-%m-%d")
                delta = (today - sent_date).days
                feedback = str(row.get("feedback") or "").strip()
                
                if delta > 15 and (not feedback or feedback.lower() == "none"):
                    # Get prospect name
                    p_data = supabase.table("prospects").select("company_name").eq("id", row['prospect_id']).execute().data
                    p_name = p_data[0]['company_name'] if p_data else "Inconnu"
                    
                    alerts.append({
                        "Société": p_name,
                        "Produit": row['product_name'],
                        "Ref": row['reference'],
                        "Envoyé le": row['date_sent'][:10],
                        "Retard": f"+{delta} jours"
                    })
        
        if alerts:
            st.warning(f"Vous avez {len(alerts)} échantillon(s) sans feedback depuis plus de 15 jours.")
            st.dataframe(pd.DataFrame(alerts), use_container_width=True)
        else:
            st.success("Aucune relance nécessaire. Tout est à jour ! 🎉")
    else:
        st.info("Aucun échantillon envoyé.")

else:
    st.title("En construction 🚧")
    st.info("Module bientôt disponible.")
