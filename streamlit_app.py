import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime
import io

# --- 1. CONFIGURATION & DESIGN SYSTEM (LUXURY EMERALD THEME) ---
st.set_page_config(page_title="Ingood Growth", page_icon="favicon.png", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        
        /* Кнопки - Изумрудный градиент */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #046c4e 0%, #065f46 100%);
            color: white; border: none; border-radius: 6px; font-weight: 600;
            box-shadow: 0 4px 6px rgba(4, 108, 78, 0.2);
            transition: all 0.2s;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 12px rgba(4, 108, 78, 0.3);
        }
        
        /* Карточки KPI */
        div[data-testid="stMetric"] {
            background-color: white; border: 1px solid #e2e8f0; border-radius: 10px;
            padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        div[data-testid="stMetricValue"] { color: #046c4e; font-weight: 800; }
        
        /* Заголовки */
        h1, h2, h3 { color: #1e293b; font-weight: 700; letter-spacing: -0.01em; }
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
    """Получает проекты"""
    return pd.DataFrame(supabase.table("prospects").select("*").order("last_action_date", desc=True).execute().data)

def get_sub_data(table, prospect_id):
    """Получает детали (контакты/активность/образцы) для конкретного проекта"""
    return pd.DataFrame(supabase.table(table).select("*").eq("prospect_id", prospect_id).order("id", desc=True).execute().data)

def get_all_contacts():
    """Получает ВСЕ контакты и объединяет с названиями компаний"""
    contacts = pd.DataFrame(supabase.table("contacts").select("*").execute().data)
    prospects = pd.DataFrame(supabase.table("prospects").select("id, company_name").execute().data)
    
    if not contacts.empty and not prospects.empty:
        # Объединяем таблицы по ID
        merged = pd.merge(contacts, prospects, left_on='prospect_id', right_on='id', how='left')
        return merged
    return contacts

def add_log(pid, type_act, content):
    """Добавляет активность и обновляет дату"""
    supabase.table("activities").insert({"prospect_id": pid, "type": type_act, "content": content, "date": datetime.now().isoformat()}).execute()
    supabase.table("prospects").update({"last_action_date": datetime.now().strftime("%Y-%m-%d")}).eq("id", pid).execute()

# --- 4. AI FUNCTIONS ---
def transcribe_audio(audio_file):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = "Transcribe this meeting audio to French text. Summarize key points."
    response = model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_file.read()}])
    return response.text

def ai_email_assistant(context_text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Act as an email assistant. Improve or draft an email based on this context: {context_text}. Language: French."
    return model.generate_content(prompt).text

# --- 5. FICHE PROSPECT (MODAL) ---
@st.dialog("Fiche Prospect", width="large")
def show_prospect_card(pid, data):
    c_head1, c_head2 = st.columns([3, 1])
    c_head1.subheader(f"🏢 {data['company_name']}")
    c_head1.caption("Gestion et Suivi R&D")
    
    with c_head2:
        with st.popover("✨ AI Assistant"):
            if st.button("📧 Hunter Email"):
                res = ai_email_assistant(f"Client: {data['company_name']}, Pain: {data['tech_pain_points']}")
                st.code(res, language="text")
            if st.button("🔬 Brief R&D"):
                res = ai_email_assistant(f"Technical Brief for {data['company_name']}, Product: {data['product_interest']}")
                st.code(res, language="text")

    tab1, tab2, tab3 = st.tabs(["Contexte & Technique", "Suivi Échantillons", "Journal d'Activité"])

    # TAB 1
    with tab1:
        with st.form("main_form"):
            col_left, col_right = st.columns([1, 2])
            with col_left:
                st.markdown("**INFO PIPELINE**")
                stat = st.selectbox("Statut Pipeline", ["Prospection", "Qualification", "Envoi Echantillon", "Test R&D", "Négociation", "Client"], index=["Prospection", "Qualification", "Envoi Echantillon", "Test R&D", "Négociation", "Client"].index(data.get("status", "Prospection")))
                c_l1, c_l2 = st.columns(2)
                pays = c_l1.text_input("Pays", value=data.get("country", ""))
                vol = c_l2.number_input("Potentiel (T)", value=float(data.get("potential_volume") or 0))
                salon = st.text_input("Dernier Salon", value=data.get("last_salon", ""))
                cfia = st.checkbox("🔥 Cible Prioritaire CFIA", value=data.get("cfia_priority", False))

            with col_right:
                st.markdown("**DONNÉES TECHNIQUES**")
                c_r1, c_r2 = st.columns(2)
                prod = c_r1.selectbox("Ingrédient", ["LENGOOD", "PEPTIPEA", "SULFODYNE"], index=0 if not data.get("product_interest") else ["LENGOOD", "PEPTIPEA", "SULFODYNE"].index(data.get("product_interest")))
                app = c_r2.text_input("Application", value=data.get("segment", ""))
                pain = st.text_area("Pain Point", value=data.get("tech_pain_points", ""), height=100)
                notes = st.text_area("Notes Techniques", value=data.get("tech_notes", ""), height=100)

            st.markdown("---")
            st.markdown("**CONTACTS CLÉS**")
            contacts_df = get_sub_data("contacts", pid)
            edited_contacts = st.data_editor(contacts_df[["name", "role", "email"]], num_rows="dynamic", use_container_width=True, key="contact_editor")

            c_btn1, c_btn2 = st.columns([4, 1])
            if c_btn2.form_submit_button("💾 Enregistrer", type="primary"):
                supabase.table("prospects").update({
                    "status": stat, "country": pays, "potential_volume": vol,
                    "last_salon": salon, "cfia_priority": cfia,
                    "product_interest": prod, "segment": app,
                    "tech_pain_points": pain, "tech_notes": notes
                }).eq("id", pid).execute()
                
                # Логика добавления контактов (упрощенная)
                # В реальном проекте тут нужно сравнивать data_editor с базой
                st.toast("Modifications enregistrées !")
                st.rerun()

    # TAB 2
    with tab2:
        st.info("ℹ️ Protocole R&D : Valider fiche technique avant envoi.")
        with st.form("sample_form", clear_on_submit=True):
            c_s1, c_s2, c_s3 = st.columns([2, 1, 1])
            ref = c_s1.text_input("Ref (Lot)")
            s_prod = c_s2.selectbox("Produit", ["LENGOOD", "PEPTIPEA", "SULFODYNE"])
            if c_s3.form_submit_button("Envoyer 🚀"):
                supabase.table("samples").insert({"prospect_id": pid, "reference": ref, "product_name": s_prod, "status": "Envoyé"}).execute()
                add_log(pid, "Sample", f"Envoi échantillon {s_prod} ({ref})")
                st.rerun()
        
        samples = get_sub_data("samples", pid)
        if not samples.empty:
            st.dataframe(samples[["date_sent", "product_name", "reference", "status", "feedback"]], use_container_width=True, hide_index=True)

    # TAB 3
    with tab3:
        with st.form("act_form", clear_on_submit=True):
            note = st.text_area("Nouvelle note...")
            if st.form_submit_button("Ajouter Note"):
                add_log(pid, "Note", note)
                st.rerun()
        
        with st.expander("🎙️ Dictaphone IA"):
            audio = st.audio_input("Enregistrer")
            if audio:
                with st.spinner("Transcription..."):
                    text = transcribe_audio(audio)
                    st.success("Terminé !")
                    if st.button("Sauvegarder"):
                        add_log(pid, "Meeting", text)
                        st.rerun()

        st.markdown("### Timeline")
        activities = get_sub_data("activities", pid)
        if not activities.empty:
            for _, row in activities.iterrows():
                icon = "📦" if row['type'] == 'Sample' else "🎙️" if row['type'] == 'Meeting' else "📝"
                with st.chat_message(name="user", avatar=icon):
                    st.caption(f"{row['date'][:10]} | {row['type']}")
                    st.write(row['content'])

# --- 6. MAIN UI ---
with st.sidebar:
    st.image("favicon.png", width=60)
    st.title("Ingood Growth")
    # Обновили название вкладки
    page = st.radio("Navigation", ["Dashboard", "Pipeline", "Contacts"], label_visibility="collapsed")
    st.divider()
    if st.button("➕ Nouveau Prospect", use_container_width=True):
        res = supabase.table("prospects").insert({"company_name": "NOUVEAU CLIENT"}).execute()
        show_prospect_card(res.data[0]['id'], res.data[0])

# PAGE: DASHBOARD
if page == "Dashboard":
    st.title("Tableau de Bord")
    df = get_data()
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Projets", len(df))
        c2.metric("Tests R&D", len(df[df['status'] == 'Test R&D']))
        c3.metric("Volume (T)", f"{df['potential_volume'].sum():.0f}")
        c4.metric("Gagnés", len(df[df['status'] == 'Client']))
        st.markdown("---")
        cl, cr = st.columns(2)
        with cl:
            fig = px.pie(df, names='segment', color_discrete_sequence=['#046c4e', '#059669', '#10b981', '#34d399'], hole=0.5)
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            cnt = df['status'].value_counts().reset_index()
            fig = px.bar(cnt, x='status', y='count', color_discrete_sequence=['#046c4e'])
            fig.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

# PAGE: PIPELINE
elif page == "Pipeline":
    st.title("Pipeline Food & Ingrédients")
    df = get_data()
    if not df.empty:
        search = st.text_input("Recherche...", placeholder="Société, produit...")
        with st.expander("Filtres", expanded=False):
            f1, f2, f3, f4 = st.columns(4)
            p_fil = f1.multiselect("Produit", df["product_interest"].unique())
            s_fil = f2.multiselect("Statut", df["status"].unique())
            c_fil = f3.multiselect("Pays", df["country"].unique())
            
        if search: df = df[df.apply(lambda x: search.lower() in str(x.values).lower(), axis=1)]
        if p_fil: df = df[df["product_interest"].isin(p_fil)]
        if s_fil: df = df[df["status"].isin(s_fil)]
        if c_fil: df = df[df["country"].isin(c_fil)]

        df['company_name'] = df['company_name'].str.upper()
        
        st.dataframe(
            df,
            column_order=("company_name", "country", "product_interest", "status", "last_action_date", "cfia_priority"),
            column_config={
                "company_name": st.column_config.TextColumn("Société", width="medium"),
                "status": st.column_config.SelectboxColumn("Statut", options=["Prospection", "Client"], width="medium"),
                "last_action_date": st.column_config.DateColumn("Dernier Contact", format="DD MMM YY"),
                "cfia_priority": st.column_config.CheckboxColumn("CFIA", width="small")
            }, hide_index=True, use_container_width=True
        )
        st.markdown("---")
        col_sel, col_btn = st.columns([3, 1])
        sel_comp = col_sel.selectbox("Ouvrir dossier :", df["company_name"].unique(), label_visibility="collapsed")
        if col_btn.button("Ouvrir Fiche", type="primary", use_container_width=True):
            row = df[df["company_name"] == sel_comp].iloc[0]
            show_prospect_card(row['id'], row)

# PAGE: CONTACTS (ОБНОВЛЕННАЯ СТРАНИЦА)
elif page == "Contacts":
    st.title("Annuaire Contacts")
    
    # 1. Загрузка и объединение данных
    all_contacts = get_all_contacts()
    
    if not all_contacts.empty:
        # 2. Метрики и Поиск
        c1, c2 = st.columns([1, 3])
        c1.metric("Total Contacts", len(all_contacts))
        search_contact = c2.text_input("🔍 Rechercher un contact (Nom, Entreprise...)", placeholder="Tapez pour filtrer...")
        
        # 3. Фильтрация
        if search_contact:
            mask = all_contacts.apply(lambda x: search_contact.lower() in str(x.values).lower(), axis=1)
            filtered_contacts = all_contacts[mask]
        else:
            filtered_contacts = all_contacts
            
        # 4. Отображение таблицы
        st.dataframe(
            filtered_contacts,
            column_order=("name", "role", "company_name", "email"),
            column_config={
                "name": "Nom Complet",
                "role": "Rôle / Poste",
                "company_name": st.column_config.TextColumn("Entreprise", width="medium"),
                "email": st.column_config.LinkColumn("Email"),
            },
            hide_index=True,
            use_container_width=True
        )
        
        # 5. Экспорт в Excel
        st.markdown("---")
        col_ex1, col_ex2 = st.columns([3, 1])
        
        # Генерация файла в памяти
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            filtered_contacts.to_excel(writer, sheet_name='Contacts', index=False)
            
        col_ex2.download_button(
            label="📥 Télécharger Excel",
            data=buffer,
            file_name=f"ingood_contacts_{datetime.now().strftime('%d-%m-%y')}.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )
    else:
        st.info("Aucun contact trouvé. Ajoutez des contacts dans les Fiches Clients.")
