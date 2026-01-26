import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px

# --- 1. CONFIGURATION (НАСТРОЙКИ) ---
st.set_page_config(
    page_title="Guide Biz Dev",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Убираем лишние отступы сверху
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
        h1 {margin-top: 0rem;}
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNEXION (ПОДКЛЮЧЕНИЕ) ---
@st.cache_resource
def init_connections():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase = create_client(url, key)
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        return supabase
    except Exception:
        st.error("🚨 Erreur de connexion. Vérifiez les Secrets (Supabase/Google).")
        st.stop()

supabase = init_connections()

# --- 3. FONCTIONS INTELLIGENTES (ФУНКЦИИ ИИ) ---

def load_data():
    """Загрузка базы из Supabase"""
    response = supabase.table("prospects").select("*").order("id", desc=True).execute()
    return pd.DataFrame(response.data)

def generate_email(company, contact, notes, tone, lang):
    """Генерация письма на выбранном языке"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Промпт адаптируется под выбранный язык
    prompt = f"""
    You are an expert Business Developer.
    Task: Write a cold email in {lang} language.
    
    Details:
    - Target Company: {company}
    - Contact Person: {contact}
    - Context/Notes: {notes}
    - Tone: {tone}
    - Product: Ingood plant-based ingredients (egg substitutes, texturizers).
    
    Goal: Secure a meeting or send samples.
    Constraint: Keep it professional, concise, and persuasive.
    """
    response = model.generate_content(prompt)
    return response.text

def process_audio(audio_file, output_lang):
    """Обработка аудио и отчет на выбранном языке"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are a sales assistant. Listen to this meeting recording.
    The audio might be in English, French, or mixed.
    
    Task: Create a structured Meeting Report (Compte-Rendu) in {output_lang} language.
    Structure:
    1. Summary (Résumé)
    2. Pain Points (Problèmes identifiés)
    3. Action Items (Prochaines étapes)
    """
    response = model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_file.read()}])
    return response.text

# --- 4. INTERFACE (ИНТЕРФЕЙС) ---

with st.sidebar:
    st.title("Guide Biz Dev 🌍")
    st.caption("Growth OS | v2.0")
    
    menu = st.radio(
        "Navigation", 
        ["📊 Tableau de Bord", "➕ Nouveau Prospect", "🎙️ Dictaphone CR", "✉️ Assistant Email"]
    )
    
    st.divider()
    st.success("🟢 Système Connecté")

# --- PAGE 1: DASHBOARD ---
if menu == "📊 Tableau de Bord":
    st.title("Vue d'ensemble Pipeline")
    
    df = load_data()
    
    if not df.empty:
        # KPI Метрики
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Prospects", len(df))
        
        # Считаем активные
        active_count = len(df[df['status'].isin(['Contacté', 'RDV pris', 'Echantillon envoyé', 'Test R&D', 'Négociation'])])
        c2.metric("En cours (Actifs)", active_count, "🔥")
        c3.metric("Clients Gagnés", len(df[df['status'] == 'Gagné']), "🏆")
        
        # Потенциал
        vol = df['potential_volume'].fillna(0).sum()
        c4.metric("Potentiel (Tonnes)", f"{vol:.0f} T")
        
        st.divider()

        # Таблица (Редактируемая)
        st.subheader("📋 Gestion des Prospects")
        st.caption("Double-cliquez pour modifier. N'oubliez pas de sauvegarder !")
        
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            height=500,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "company_name": st.column_config.TextColumn("Entreprise", required=True),
                "status": st.column_config.SelectboxColumn(
                    "Statut",
                    options=[
                        "À contacter", 
                        "Contacté", 
                        "RDV pris", 
                        "Echantillon envoyé", 
                        "Test R&D", 
                        "Négociation", 
                        "Gagné", 
                        "Perdu"
                    ],
                    required=True
                ),
                "tier": st.column_config.SelectboxColumn("Priorité", options=["Tier 1", "Tier 2", "Tier 3"]),
                "potential_volume": st.column_config.NumberColumn("Volume (T)"),
                "website": st.column_config.LinkColumn("Site Web"),
                "notes": st.column_config.TextColumn("Notes", width="large"),
            },
            hide_index=True
        )

        # Кнопка сохранения
        if st.button("💾 Sauvegarder les modifications", type="primary"):
            try:
                data_to_save = edited_df.to_dict(orient="records")
                supabase.table("prospects").upsert(data_to_save).execute()
                st.success("✅ Base de données mise à jour !")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erreur de sauvegarde : {e}")

    else:
        st.info("La base est vide.")

# --- PAGE 2: NOUVEAU PROSPECT ---
elif menu == "➕ Nouveau Prospect":
    st.title("Ajouter un Prospect")
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        comp = c1.text_input("Entreprise *")
        name = c2.text_input("Contact")
        
        c3, c4 = st.columns(2)
        vol = c3.number_input("Potentiel (T)", min_value=0)
        tier = c4.selectbox("Priorité", ["Tier 1", "Tier 2", "Tier 3"])
        
        note = st.text_area("Notes initiales")
        
        if st.form_submit_button("Créer la fiche") and comp:
            try:
                new_data = {
                    "company_name": comp, 
                    "contact_name": name, 
                    "potential_volume": vol, 
                    "tier": tier, 
                    "notes": note,
                    "status": "À contacter"
                }
                supabase.table("prospects").insert(new_data).execute()
                st.success(f"Ajouté : {comp}")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erreur : {e}")

# --- PAGE 3: DICTAPHONE (С ВЫБОРОМ ЯЗЫКА) ---
elif menu == "🎙️ Dictaphone CR":
    st.title("🎙️ Compte-Rendu Vocal")
    st.info("Enregistrez le résumé. L'IA rédige le rapport.")
    
    # Выбор языка отчета
    lang_report = st.selectbox("Langue du rapport écrit :", ["Français", "English"])
    
    audio = st.audio_input("Enregistrer")
    
    if audio:
        with st.spinner("Analyse en cours..."):
            res = process_audio(audio, lang_report)
            st.subheader(f"📝 Rapport ({lang_report}) :")
            st.text_area("Résultat", res, height=400)

# --- PAGE 4: EMAILS (С ВЫБОРОМ ЯЗЫКА) ---
elif menu == "✉️ Assistant Email":
    st.title("⚡ Générateur d'Emails IA")
    
    df = load_data()
    
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        comp_sel = c1.selectbox("Entreprise", df["company_name"].unique())
        tone_sel = c2.selectbox("Ton", ["Formel", "Amical", "Direct", "Relance"])
        # ВЫБОР ЯЗЫКА ПИСЬМА
        lang_sel = c3.selectbox("Langue de l'email", ["Français", "English"])
        
        row = df[df["company_name"] == comp_sel].iloc[0]
        st.markdown(f"**Contexte :** {row.get('notes', 'N/A')}")
        
        if st.button("✨ Générer le brouillon"):
            with st.spinner(f"Rédaction en {lang_sel}..."):
                res = generate_email(
                    comp_sel, 
                    row.get("contact_name", "Sir/Madam"), 
                    row.get("notes", ""), 
                    tone_sel, 
                    lang_sel
                )
                st.text_area("Brouillon :", res, height=400)
    else:
        st.warning("Ajoutez d'abord des prospects !")
