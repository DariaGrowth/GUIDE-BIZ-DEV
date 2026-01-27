import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime
import io
import numpy as np
import time

# --- 1. CONFIGURATION & VISUAL IDENTITY (PIXEL-PERFECT CSS) ---
st.set_page_config(page_title="Ingood Growth", page_icon="favicon.png", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* 1. ГЛОБАЛЬНЫЙ СТИЛЬ */
        .stApp { 
            background-color: #f8fafc;
            font-family: 'Inter', sans-serif;
            color: #334155;
        }
        
        /* 2. САЙДБАР */
        section[data-testid="stSidebar"] { 
            background-color: #ffffff; 
            border-right: 1px solid #e2e8f0;
            padding-top: 10px;
        }
        
        /* 3. КНОПКА "NOUVEAU PROJET" */
        .stButton > button {
            width: 100%;
            background-color: #047857 !important;
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 12px 16px;
            font-weight: 600;
            font-size: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #065f46 !important;
            transform: translateY(-1px);
        }
        .stButton > button::before {
            content: "⊕ ";
            font-size: 18px;
            margin-right: 8px;
            font-weight: 400;
        }

        /* 4. МЕНЮ НАВИГАЦИИ */
        div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }
        
        div[role="radiogroup"] label {
            display: flex;
            align-items: center;
            width: 100%;
            padding: 10px 16px;
            margin-bottom: 4px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            transition: all 0.2s;
            color: #64748b; /* Серый цвет иконок и текста */
            font-weight: 500;
            font-size: 15px;
        }
        
        /* Стиль для текста иконок */
        div[role="radiogroup"] label p {
            font-size: 18px; /* Чуть крупнее для иконок */
            margin: 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        /* АКТИВНЫЙ пункт меню */
        div[role="radiogroup"] label[data-checked="true"] {
            background-color: #ecfdf5 !important; /* Светло-зеленый фон */
            color: #047857 !important; /* Зеленый текст */
            font-weight: 600;
        }

        div[role="radiogroup"] label:hover {
            background-color: #f1f5f9;
            color: #334155;
        }

        /* 5. ТАБЛИЦА (PIPELINE) */
        div[data-testid="stDataFrame"] {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            background: white;
        }
        
        thead tr th {
            background-color: #f8fafc !important;
            color: #64748b !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            text-transform: none !important;
            border-bottom: 1px solid #e2e8f0 !important;
            padding: 12px 16px !important;
        }
        
        tbody tr td {
            color: #334155 !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            padding: 12px 16px !important;
            border-bottom: 1px solid #f1f5f9 !important;
        }
        
        thead tr th:first-child, tbody tr td:first-child { display: none; }

        h1 { color: #0f172a; font-weight: 700; font-size: 28px; margin-bottom: 0.5rem; }
        .caption { color: #64748b; font-size: 14px; }
        
        /* Красный бейдж для уведомлений */
        .notification-badge {
            background-color: #ef4444;
            color: white;
            border-radius: 50%;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 8px;
            vertical-align: middle;
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
            df = pd.DataFrame(columns=["id", "name", "role", "email"])
        elif table == "samples":
            return pd.DataFrame(columns=["id", "date_sent", "product_name", "reference", "status", "feedback"])
        elif table == "activities":
            return pd.DataFrame(columns=["id", "date", "type", "content"])
            
    if table == "contacts":
        for col in ["name", "role", "email"]:
            if col not in df.columns: df[col] = ""
            df[col] = df[col].astype(str).replace({"nan": "", "None": "", "none": ""})
    return df

def get_all_contacts():
    contacts = pd.DataFrame(supabase.table("contacts").select("*").execute().data)
    prospects = pd.DataFrame(supabase.table("prospects").select("id, company_name").execute().data)
    
    if contacts.empty:
        return pd.DataFrame(columns=["name", "role", "company_name", "email"])
    if not prospects.empty:
        merged = pd.merge(contacts, prospects, left_on='prospect_id', right_on='id', how='left')
        return merged
    return contacts

def add_log(pid, type_act, content):
    pid = int(pid)
    supabase.table("activities").insert({"prospect_id": pid, "type": type_act, "content": content, "date": datetime.now().isoformat()}).execute()
    supabase.table("prospects").update({"last_action_date": datetime.now().strftime("%Y-%m-%d")}).eq("id", pid).execute()

# --- 4. AI ---
def transcribe_audio(audio_file):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = "Transcribe this meeting audio to French text. Summarize key points."
    response = model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_file.read()}])
    return response.text

def ai_email_assistant(context_text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Act as an email assistant. French language. Context: {context_text}."
    return model.generate_content(prompt).text

# --- 5. FICHE PROSPECT (MODAL) ---
@st.dialog("Fiche Prospect", width="large")
def show_prospect_card(pid, data):
    pid = int(pid)
    
    c_head1, c_head2 = st.columns([3, 1])
    c_head1.subheader(f"🏢 {data['company_name']}")
    c_head1.caption("Gestion et Suivi R&D")
    
    with c_head2:
        with st.popover("✨ AI Assistant"):
            if st.button("📧 Hunter Email"):
                res = ai_email_assistant(f"Client: {data['company_name']}, Pain: {data['tech_pain_points']}")
                st.code(res, language="text")
            if st.button("🔬 Brief R&D"):
                res = ai_email_assistant(f"Brief for {data['company_name']}, Product: {data['product_interest']}")
                st.code(res, language="text")

    tab1, tab2, tab3 = st.tabs(["Contexte", "Échantillons", "Journal"])

    with tab1:
        with st.form("main_form"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("**INFO**")
                stat = st.selectbox("Statut", ["Prospection", "Qualification", "Envoi Echantillon", "Test R&D", "Négociation", "Client"], index=["Prospection", "Qualification", "Envoi Echantillon", "Test R&D", "Négociation", "Client"].index(data.get("status", "Prospection")))
                pays = st.text_input("Pays", value=data.get("country", ""))
                vol = st.number_input("Potentiel (T)", value=float(data.get("potential_volume") or 0))
                salon = st.text_input("Source", value=data.get("last_salon", ""))
                cfia = st.checkbox("🔥 CFIA", value=data.get("cfia_priority", False))

            with c2:
                st.markdown("**TECHNIQUE**")
                r1, r2 = st.columns(2)
                prod = r1.selectbox("Ingrédient", ["LENGOOD", "PEPTIPEA", "SULFODYNE"], index=0 if not data.get("product_interest") else ["LENGOOD", "PEPTIPEA", "SULFODYNE"].index(data.get("product_interest")))
                app = r2.text_input("Application", value=data.get("segment", ""))
                pain = st.text_area("Pain Point", value=data.get("tech_pain_points", ""), height=100)
                notes = st.text_area("Notes", value=data.get("tech_notes", ""), height=100)

            st.markdown("---")
            st.markdown("**CONTACTS** (Ajoutez des lignes ici 👇)")
            
            contacts_df = get_sub_data("contacts", pid)
            
            edited_contacts = st.data_editor(
                contacts_df,
                column_config={"id": None, "name": "Nom", "role": "Rôle", "email": "Email"},
                column_order=("name", "role", "email"), 
                num_rows="dynamic",
                use_container_width=True,
                key=f"editor_{pid}"
            )

            if st.form_submit_button("💾 Enregistrer Tout", type="primary"):
                with st.spinner("Sauvegarde..."):
                    supabase.table("prospects").update({
                        "status": stat, "country": pays, "potential_volume": vol,
                        "last_salon": salon, "cfia_priority": cfia,
                        "product_interest": prod, "segment": app,
                        "tech_pain_points": pain, "tech_notes": notes
                    }).eq("id", pid).execute()
                    
                    if not edited_contacts.empty:
                        records = edited_contacts.to_dict('records')
                        for row in records:
                            name_val = str(row.get("name", "")).strip()
                            role_val = str(row.get("role", "")).strip()
                            email_val = str(row.get("email", "")).strip()
                            
                            if role_val.lower() == "nan": role_val = ""
                            if email_val.lower() == "nan": email_val = ""

                            if name_val and name_val != "nan":
                                contact_data = {"prospect_id": pid, "name": name_val, "role": role_val, "email": email_val}
                                raw_id = row.get("id")
                                if raw_id and pd.notna(raw_id) and str(raw_id) != "":
                                     try:
                                        contact_data["id"] = int(float(raw_id))
                                        supabase.table("contacts").upsert(contact_data).execute()
                                     except: supabase.table("contacts").insert(contact_data).execute()
                                else: supabase.table("contacts").insert(contact_data).execute()
                    time.sleep(1.2)
                st.toast(f"✅ Sauvegardé !")
                st.rerun()

    with tab2:
        with st.form("sample_form", clear_on_submit=True):
            c_s1, c_s2, c_s3 = st.columns([2, 1, 1])
            ref = c_s1.text_input("Ref (Lot)")
            s_prod = c_s2.selectbox("Produit", ["LENGOOD", "PEPTIPEA", "SULFODYNE"])
            if c_s3.form_submit_button("Envoyer 🚀"):
                supabase.table("samples").insert({"prospect_id": pid, "reference": ref, "product_name": s_prod, "status": "Envoyé"}).execute()
                add_log(pid, "Sample", f"Envoi échantillon {s_prod} ({ref})")
                time.sleep(1)
                st.rerun()
        samples = get_sub_data("samples", pid)
        st.dataframe(samples[["date_sent", "product_name", "reference", "status", "feedback"]], use_container_width=True, hide_index=True)

    with tab3:
        with st.form("act_form", clear_on_submit=True):
            note = st.text_area("Note...")
            if st.form_submit_button("Ajouter"):
                add_log(pid, "Note", note)
                time.sleep(1)
                st.rerun()
        with st.expander("🎙️ Dictaphone IA"):
            audio = st.audio_input("Enregistrer")
            if audio:
                with st.spinner("Transcription..."):
                    text = transcribe_audio(audio)
                    st.success("OK")
                    if st.button("Sauvegarder"):
                        add_log(pid, "Meeting", text)
                        time.sleep(1)
                        st.rerun()
        st.markdown("### Timeline")
        activities = get_sub_data("activities", pid)
        for _, row in activities.iterrows():
            with st.chat_message("user"):
                st.caption(f"{row['date'][:10]} | {row['type']}")
                st.write(row['content'])

# --- 6. MAIN SIDEBAR & NAVIGATION (PERFECT MONOCHROME ICONS) ---
with st.sidebar:
    st.image("favicon.png", width=65)
    
    if st.button("Nouveau Projet", use_container_width=True):
        res = supabase.table("prospects").insert({"company_name": "NOUVEAU CLIENT"}).execute()
        show_prospect_card(int(res.data[0]['id']), res.data[0])
    
    st.write("") # Отступ
    
    # ИКОНКИ (Строгий монохром, подобранный под макет)
    icons = {
        "Tableau de Bord": "⊞",   # Сетка / Окно
        "Pipeline": "≡",          # Список линий
        "Kanban": "☷",            # Триграмма (похожа на колонки)
        "Échantillons": "⚗",      # Алембик (Монохромная колба!)
        "À Relancer": "⍾"         # Контурный колокольчик
    }

    # Меню с новой опцией "À Relancer"
    menu_options = [
        "Tableau de Bord", 
        "Pipeline", 
        "Contacts", 
        "Kanban", 
        "Échantillons",
        "À Relancer"
    ]
    
    def format_func(option):
        # Добавляем красный индикатор (текстом) для "À Relancer"
        if option == "À Relancer":
             return f"{icons[option]}  {option} (1)" # Имитация бейджа
        return f"{icons.get(option, '•')}  {option}"

    page = st.radio("Navigation", menu_options, format_func=format_func, label_visibility="collapsed")
    
    st.markdown("---")
    c_prof1, c_prof2 = st.columns([1, 4])
    with c_prof1:
        st.write("👤")
    with c_prof2:
        st.caption("Daria Growth\nAdmin")

# --- 7. PAGES LOGIC ---

if page == "Tableau de Bord":
    st.title("Tableau de Bord")
    st.markdown("<p class='caption'>Suivi des performances commerciales</p>", unsafe_allow_html=True)
    df = get_data()
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Projets Actifs", len(df))
        c2.metric("En Test R&D", len(df[df['status'] == 'Test R&D']))
        c3.metric("Volume (T)", f"{df['potential_volume'].sum():.0f}")
        c4.metric("Gagnés", len(df[df['status'] == 'Client']))
        
        st.markdown("### Répartition")
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
    st.title("Pipeline Food & Ingrédients")
    st.markdown("<p class='caption'>Suivi des projets R&D et commerciaux.</p>", unsafe_allow_html=True)
    
    df = get_data()
    if not df.empty:
        c_search, c_space = st.columns([1, 3])
        search = c_search.text_input("Recherche", placeholder="Société...", label_visibility="collapsed")
        
        if search: df = df[df.apply(lambda x: search.lower() in str(x.values).lower(), axis=1)]
        df['company_name'] = df['company_name'].str.upper()
        df['actions'] = "›" 
        
        st.write("")
        
        selection = st.dataframe(
            df,
            column_order=("company_name", "country", "product_interest", "status", "last_action_date", "cfia_priority", "actions"),
            column_config={
                "company_name": st.column_config.TextColumn("Société", width="medium"),
                "country": st.column_config.TextColumn("Pays"),
                "product_interest": st.column_config.TextColumn("Produit"),
                "status": st.column_config.SelectboxColumn("Statut", options=["Prospection", "Qualification", "Envoi Echantillon", "Test R&D", "Négociation", "Client"], width="medium", disabled=True),
                "last_action_date": st.column_config.DateColumn("Dernier Contact", format="DD MMM YYYY"),
                "cfia_priority": st.column_config.CheckboxColumn("CFIA", width="small"),
                "actions": st.column_config.TextColumn(" ", width="small")
            },
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row"
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
        
        st.dataframe(
            all_c, 
            column_order=("name", "role", "company_name", "email"),
            column_config={"name": "Nom", "role": "Rôle", "company_name": "Société", "email": "Email"},
            hide_index=True, use_container_width=True
        )
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            all_c.to_excel(writer, sheet_name='Contacts', index=False)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name="contacts.xlsx", mime="application/vnd.ms-excel")
    else:
        st.info("Aucun contact trouvé.")

elif page == "À Relancer":
    st.title("À Relancer")
    st.info("Cette section affichera automatiquement les clients qui nécessitent un suivi (ex: 14 jours après envoi d'échantillon).")

else:
    st.title("En construction 🚧")
    st.info("Module bientôt disponible.")
