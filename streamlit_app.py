import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & DESIGN SYSTEM (EMERALD THEME) ---
st.set_page_config(
    page_title="Ingood Growth CRM",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS injection (Цвета бренда из ТЗ)
st.markdown("""
    <style>
        :root {
            --primary-color: #10b981; /* Emerald 500 */
            --bg-color: #f8fafc; /* Slate 50 */
            --secondary-bg: #ffffff;
            --text-color: #0f172a;
        }
        .stApp {
            background-color: var(--bg-color);
        }
        /* Сайдбар */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e2e8f0;
        }
        /* Кнопки (Emerald) */
        div.stButton > button:first-child {
            background-color: #10b981;
            color: white;
            border-radius: 8px;
            font-weight: 600;
            border: none;
        }
        div.stButton > button:first-child:hover {
            background-color: #059669; /* Darker Emerald */
        }
        /* Заголовки */
        h1, h2, h3 { color: #064e3b; font-family: 'Helvetica', sans-serif; }
        
        /* Карточки KPI */
        div[data-testid="stMetric"] {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNEXIONS ---
@st.cache_resource
def init_connections():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase = create_client(url, key)
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        return supabase
    except Exception:
        st.error("🚨 Erreur de connexion. Vérifiez les secrets.")
        st.stop()

supabase = init_connections()

# --- 3. FONCTIONS DATA (CRUD) ---

def get_prospects():
    """Получить всех клиентов"""
    res = supabase.table("prospects").select("*").order("last_action_date", desc=True).execute()
    return pd.DataFrame(res.data)

def get_details(prospect_id, table):
    """Получить контакты, сэмплы или активность"""
    res = supabase.table(table).select("*").eq("prospect_id", prospect_id).order("id", desc=True).execute()
    return pd.DataFrame(res.data)

def update_last_action(prospect_id):
    """Обновить дату последнего контакта на СЕГОДНЯ"""
    now = datetime.now().strftime("%Y-%m-%d")
    supabase.table("prospects").update({"last_action_date": now}).eq("id", prospect_id).execute()

def add_activity(prospect_id, type_act, content):
    """Добавить заметку и обновить дату"""
    supabase.table("activities").insert({
        "prospect_id": prospect_id,
        "type": type_act,
        "content": content,
        "date": datetime.now().isoformat()
    }).execute()
    update_last_action(prospect_id)

# --- 4. FONCTIONS AI (GÉNÉRATION) ---

def process_audio(audio_file):
    """Голос в Текст (Gemini)"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = "Tu es un assistant commercial. Résume ce meeting en français. Structure: Client, Besoins, Prochaines étapes."
    res = model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_file.read()}])
    return res.text

def get_hunter_prompt(company, segment, pain, product):
    return f"""Act as Hunter AI. Write a cold email in French to the R&D Director of {company}.
Context: Sector {segment}.
Pain Point: {pain}.
Solution: Introduce {product} from Ingood by Olga.
Value Prop: Clean Label, Price Stability.
Tone: Professional & Direct."""

# --- 5. MODAL DIALOG (КАРТОЧКА ПРОЕКТА) ---
# Новая фишка Streamlit для всплывающих окон
@st.dialog("Fiche Projet 📁", width="large")
def show_prospect_card(prospect_id, prospect_data):
    # Вкладки внутри модального окна
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Contexte", "👥 Contacts", "🧪 Échantillons", "💬 Activité & AI"])
    
    # --- TAB 1: Contexte ---
    with tab1:
        with st.form("edit_main"):
            c1, c2 = st.columns(2)
            comp = c1.text_input("Société", value=prospect_data["company_name"])
            status = c2.selectbox("Statut", ["Prospection", "Qualification", "Envoi Echantillon", "Test R&D", "Essai Industriel", "Négociation", "Client"], index=["Prospection", "Qualification", "Envoi Echantillon", "Test R&D", "Essai Industriel", "Négociation", "Client"].index(prospect_data["status"]))
            
            c3, c4, c5 = st.columns(3)
            segment = c3.selectbox("Segment", ["Boulangerie", "Sauces", "Nutraceutique", "Viande Végétale", "Autre"], index=0 if not prospect_data["segment"] else ["Boulangerie", "Sauces", "Nutraceutique", "Viande Végétale", "Autre"].index(prospect_data["segment"]))
            product = c4.selectbox("Produit", ["LENGOOD", "PEPTIPEA", "SULFODYNE"], index=0 if not prospect_data["product_interest"] else ["LENGOOD", "PEPTIPEA", "SULFODYNE"].index(prospect_data["product_interest"]))
            vol = c5.number_input("Volume (T)", value=float(prospect_data["potential_volume"] or 0))
            
            pain = st.text_area("Problématique R&D (Pain Points)", value=prospect_data["tech_pain_points"])
            
            cfia = st.checkbox("🔥 Priorité CFIA", value=prospect_data["cfia_priority"])
            
            if st.form_submit_button("💾 Sauvegarder les modifications"):
                supabase.table("prospects").update({
                    "company_name": comp, "status": status, "segment": segment,
                    "product_interest": product, "potential_volume": vol,
                    "tech_pain_points": pain, "cfia_priority": cfia
                }).eq("id", prospect_id).execute()
                st.rerun()

    # --- TAB 2: Contacts ---
    with tab2:
        contacts = get_details(prospect_id, "contacts")
        if not contacts.empty:
            st.dataframe(contacts[["name", "role", "email"]], hide_index=True)
        
        with st.expander("➕ Ajouter un contact"):
            with st.form("add_contact"):
                c_name = st.text_input("Nom")
                c_role = st.text_input("Rôle")
                c_email = st.text_input("Email")
                if st.form_submit_button("Ajouter"):
                    supabase.table("contacts").insert({"prospect_id": prospect_id, "name": c_name, "role": c_role, "email": c_email}).execute()
                    st.rerun()

    # --- TAB 3: Samples ---
    with tab3:
        samples = get_details(prospect_id, "samples")
        if not samples.empty:
            st.dataframe(samples[["product_name", "reference", "status", "date_sent"]], hide_index=True)
        
        with st.expander("📦 Nouvel Échantillon"):
            with st.form("add_sample"):
                s_prod = st.selectbox("Produit", ["LENGOOD", "PEPTIPEA"])
                s_ref = st.text_input("Référence (Lot)")
                if st.form_submit_button("Envoyer"):
                    supabase.table("samples").insert({"prospect_id": prospect_id, "product_name": s_prod, "reference": s_ref}).execute()
                    add_activity(prospect_id, "Sample", f"Échantillon envoyé: {s_prod} ({s_ref})")
                    st.rerun()

    # --- TAB 4: Activity & AI ---
    with tab4:
        st.write("#### 🤖 AI Tools")
        col_ai1, col_ai2 = st.columns(2)
        if col_ai1.button("📧 Hunter AI Prompt"):
            prompt = get_hunter_prompt(prospect_data["company_name"], prospect_data["segment"], prospect_data["tech_pain_points"], prospect_data["product_interest"])
            st.code(prompt, language="text")
            st.caption("Copiez ce prompt dans ChatGPT/Claude")
        
        st.divider()
        st.write("#### 🎙️ Compte-Rendu Vocal")
        audio = st.audio_input("Enregistrer réunion")
        if audio:
            with st.spinner("Analyse..."):
                text = process_audio(audio)
                st.info(text)
                if st.button("Sauvegarder ce CR"):
                    add_activity(prospect_id, "Meeting", text)
                    st.rerun()

        st.divider()
        st.write("#### 📜 Historique")
        activities = get_details(prospect_id, "activities")
        if not activities.empty:
            for _, row in activities.iterrows():
                st.caption(f"{row['date'][:10]} | {row['type']}")
                st.info(row['content'])
        
        with st.form("new_note"):
            note = st.text_area("Nouvelle note rapide")
            if st.form_submit_button("Ajouter Note"):
                add_activity(prospect_id, "Note", note)
                st.rerun()

# --- 6. MAIN APP STRUCTURE ---

# Sidebar
with st.sidebar:
    st.title("Ingood Growth 🌿")
    st.caption("Status: Cadre | Focus: Food")
    
    menu = st.radio("Navigation", ["📊 Dashboard", "🚀 Pipeline", "⚠️ À Relancer"])
    
    st.divider()
    if st.button("➕ Nouveau Prospect", use_container_width=True):
        # Создаем пустой проект и сразу открываем его
        res = supabase.table("prospects").insert({"company_name": "NOUVEAU CLIENT"}).execute()
        new_id = res.data[0]['id']
        show_prospect_card(new_id, res.data[0])

# Page: Dashboard
if menu == "📊 Dashboard":
    st.title("Tableau de Bord")
    df = get_prospects()
    
    if not df.empty:
        # KPI
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Projets", len(df))
        active_rd = len(df[df['status'] == 'Test R&D'])
        c2.metric("Tests R&D Actifs", active_rd, "🧪")
        total_vol = df['potential_volume'].sum()
        c3.metric("Volume Potentiel", f"{total_vol:.0f} T")
        
        # Графики Plotly
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            fig_pie = px.pie(df, names='segment', title='Répartition par Segment', color_discrete_sequence=px.colors.sequential.Teal)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c_chart2:
            fig_bar = px.bar(df, x='status', title='Projets par Statut', color_discrete_sequence=['#10b981'])
            st.plotly_chart(fig_bar, use_container_width=True)

# Page: Pipeline
elif menu == "🚀 Pipeline":
    c1, c2 = st.columns([3, 1])
    c1.title("Pipeline Commercial")
    c2.markdown("### <span style='color:#f59e0b'>CFIA Ready 🦁</span>", unsafe_allow_html=True)
    
    df = get_prospects()
    if not df.empty:
        # Фильтры
        with st.expander("🔍 Filtres", expanded=False):
            f1, f2 = st.columns(2)
            sel_prod = f1.multiselect("Produit", df["product_interest"].unique())
            sel_stat = f2.multiselect("Statut", df["status"].unique())
            
            if sel_prod: df = df[df["product_interest"].isin(sel_prod)]
            if sel_stat: df = df[df["status"].isin(sel_stat)]

        # Логика "Просрочки" (45 дней)
        today = datetime.now().date()
        df['last_action_date'] = pd.to_datetime(df['last_action_date']).dt.date
        df['Alerte'] = df['last_action_date'].apply(lambda d: '⚠️' if d and (today - d).days > 45 else '')

        # Таблица
        st.dataframe(
            df,
            column_order=("Alerte", "company_name", "country", "product_interest", "status", "last_action_date", "cfia_priority"),
            column_config={
                "Alerte": st.column_config.TextColumn("", width="small"),
                "company_name": "Société",
                "country": "Pays",
                "product_interest": "Produit",
                "status": st.column_config.SelectboxColumn("Statut", options=["Prospection", "Client"], disabled=True),
                "last_action_date": "Dernier Contact",
                "cfia_priority": st.column_config.CheckboxColumn("CFIA", disabled=True)
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Открытие карточки
        st.caption("Sélectionnez un projet pour voir les détails")
        selected_comp = st.selectbox("Ouvrir Dossier :", df["company_name"].unique(), key="pipe_sel")
        if st.button("Ouvrir Fiche >"):
            row = df[df["company_name"] == selected_comp].iloc[0]
            show_prospect_card(row['id'], row)

# Page: À Relancer
elif menu == "⚠️ À Relancer":
    st.title("⚠️ Priorité Relance (> 45 jours)")
    st.caption("Contacts 'dormants' à réactiver avant le salon.")
    
    df = get_prospects()
    if not df.empty:
        today = datetime.now().date()
        df['last_action_date'] = pd.to_datetime(df['last_action_date']).dt.date
        
        # Фильтр: > 45 дней И НЕ Клиент
        mask = df.apply(lambda x: (x['status'] != 'Client') and ((today - x['last_action_date']).days > 45), axis=1)
        stale_df = df[mask]
        
        if not stale_df.empty:
            st.dataframe(
                stale_df[["company_name", "status", "last_action_date", "tech_pain_points"]],
                use_container_width=True,
                hide_index=True
            )
            # Быстрое действие
            target = st.selectbox("Action Rapide sur :", stale_df["company_name"].unique())
            if st.button("Générer Email Relance"):
                row = stale_df[stale_df["company_name"] == target].iloc[0]
                prompt = get_hunter_prompt(target, row['segment'], row['tech_pain_points'], row['product_interest'])
                st.code(prompt, language="text")
        else:
            st.success("Aucun retard ! Tout est à jour. 🎉")
