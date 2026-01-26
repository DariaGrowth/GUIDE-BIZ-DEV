import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px

# --- 1. CONFIGURATION DE LA PAGE (НАСТРОЙКИ) ---
st.set_page_config(
    page_title="Guide Biz Dev",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Убираем лишние отступы для красоты
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
        # Supabase
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase = create_client(url, key)
        # Google AI
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        return supabase
    except Exception:
        st.error("🚨 Erreur de connexion. Vérifiez les Secrets.")
        st.stop()

supabase = init_connections()

# --- 3. FONCTIONS (ФУНКЦИИ) ---

def load_data():
    """Загрузка данных из Supabase"""
    response = supabase.table("prospects").select("*").order("id", desc=True).execute()
    return pd.DataFrame(response.data)

def generate_email(company, contact, notes, tone):
    """ИИ пишет письмо на французском"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Tu es un expert en Business Development. Rédige un email de prospection en français.
    Entreprise cible : {company}.
    Contact : {contact}.
    Contexte/Notes : {notes}.
    Ton : {tone}.
    Produit : Ingrédients végétaux Ingood (substituts d'œufs, texturants).
    Objectif : Obtenir un rendez-vous ou envoyer des échantillons.
    L'email doit être percutant, professionnel et personnalisé.
    """
    response = model.generate_content(prompt)
    return response.text

def process_audio(audio_file):
    """ИИ обрабатывает аудио-отчет"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = """
    Tu es mon assistant commercial. Écoute cette note vocale prise après un rendez-vous client.
    Tâche :
    1. Résume les points clés.
    2. Identifie le Client, le Besoin (Pain point), et l'Action à suivre.
    3. Rédige le compte-rendu en français, structuré avec des puces (bullets).
    """
    response = model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_file.read()}])
    return response.text

# --- 4. INTERFACE UTILISATEUR (UI) ---

# SIDEBAR (БОКОВОЕ МЕНЮ)
with st.sidebar:
    st.title("Guide Biz Dev 🚀")
    st.caption("Plateforme de Croissance")
    
    # Меню на французском
    menu = st.radio(
        "Navigation", 
        ["📊 Tableau de Bord", "➕ Nouveau Prospect", "🎙️ Dictaphone CR", "✉️ Assistant Email"]
    )
    
    st.divider()
    st.success("🟢 Système Connecté")

# PAGE 1: DASHBOARD & BASE
if menu == "📊 Tableau de Bord":
    st.title("Vue d'ensemble Pipeline")
    
    # Загрузка
    df = load_data()
    
    if not df.empty:
        # KPI (Метрики)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Prospects", len(df))
        
        # Считаем активные сделки (не закрытые и не потерянные)
        active_count = len(df[df['status'].isin(['Contacté', 'RDV pris', 'Echantillon', 'Test R&D', 'Négociation'])])
        c2.metric("En cours (Actifs)", active_count, "🔥")
        
        c3.metric("Clients Gagnés", len(df[df['status'] == 'Gagné']), "🏆")
        
        # Потенциал
        vol = df['potential_volume'].fillna(0).sum()
        c4.metric("Potentiel (Tonnes)", f"{vol:.0f} T")
        
        st.divider()

        # TABLEAU (Таблица)
        st.subheader("📋 Gestion des Prospects")
        st.caption("Double-cliquez sur une case pour modifier. Appuyez sur 'Sauvegarder' en bas.")
        
        # Настройка колонок на французском
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            height=500,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "company_name": st.column_config.TextColumn("Entreprise", required=True),
                "contact_name": st.column_config.TextColumn("Contact"),
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
                        "Perdu/Abandonné"
                    ],
                    required=True
                ),
                "tier": st.column_config.SelectboxColumn("Priorité", options=["Tier 1", "Tier 2", "Tier 3"]),
                "potential_volume": st.column_config.NumberColumn("Volume (T)"),
                "website": st.column_config.LinkColumn("Site Web"),
                "notes": st.column_config.TextColumn("Notes & Commentaires", width="large"),
            },
            hide_index=True
        )

        # BOUTON SAUVEGARDER
        if st.button("💾 Sauvegarder les modifications", type="primary"):
            try:
                # Превращаем в словарь для Supabase
                data_to_save = edited_df.to_dict(orient="records")
                supabase.table("prospects").upsert(data_to_save).execute()
                st.success("✅ Base de données mise à jour avec succès !")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erreur de sauvegarde : {e}")

    else:
        st.info("La base est vide. Ajoutez votre premier prospect via le menu !")

# PAGE 2: AJOUTER (НОВЫЙ КЛИЕНТ)
elif menu == "➕ Nouveau Prospect":
    st.title("Ajouter un Prospect")
    with st.form("new_lead_form"):
        c1, c2 = st.columns(2)
        comp = c1.text_input("Nom de l'entreprise *")
        name = c2.text_input("Personne de contact")
        
        c3, c4 = st.columns(2)
        vol = c3.number_input("Potentiel (Tonnes)", min_value=0)
        tier = c4.selectbox("Priorité", ["Tier 1", "Tier 2", "Tier 3"])
        
        note = st.text_area("Notes initiales / Contexte")
        
        btn = st.form_submit_button("Créer la fiche")
        
        if btn and comp:
            try:
                new_data = {
                    "company_name": comp, 
                    "contact_name": name, 
                    "potential_volume": vol,
                    "tier": tier,
                    "notes": note,
                    "status": "À contacter" # Статус по умолчанию
                }
                supabase.table("prospects").insert(new_data).execute()
                st.success(f"L'entreprise {comp} a été ajoutée !")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erreur : {e}")

# PAGE 3: DICTAPHONE (ГОЛОС)
elif menu == "🎙️ Dictaphone CR":
    st.title("🎙️ Compte-Rendu Vocal")
    st.info("Enregistrez votre résumé de réunion. L'IA va le transcrire et le structurer.")
    
    audio = st.audio_input("Enregistrer")
    
    if audio:
        with st.spinner("Analyse en cours..."):
            res = process_audio(audio)
            st.subheader("📝 Compte-Rendu généré :")
            st.text_area("Résultat (Copiez-collez dans CRM)", res, height=400)

# PAGE 4: EMAIL (ПИСЬМА)
elif menu == "✉️ Assistant Email":
    st.title("⚡ Générateur d'Emails IA")
    
    df = load_data()
    
    if not df.empty:
        c1, c2 = st.columns(2)
        comp_sel = c1.selectbox("Sélectionner l'entreprise", df["company_name"].unique())
        tone_sel = c2.selectbox("Ton du message", ["Formel & Professionnel", "Amical & Direct", "Relance (Follow-up)", "Proposition d'échantillons"])
        
        # Данные клиента
        row = df[df["company_name"] == comp_sel].iloc[0]
        st.markdown(f"**Contexte :** {row.get('notes', 'Aucune note')}")
        
        if st.button("✨ Générer le brouillon"):
            with st.spinner("Rédaction en cours..."):
                res = generate_email(comp_sel, row.get("contact_name", ""), row.get("notes", ""), tone_sel)
                st.text_area("Brouillon proposé :", res, height=400)
    else:
        st.warning("Ajoutez d'abord des prospects dans la base !")
