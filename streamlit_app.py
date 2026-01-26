import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import datetime

# --- 1. CONFIGURATION & STYLE (ДИЗАЙН) ---
st.set_page_config(
    page_title="Ingood Growth CRM",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS для стиля Emerald (зеленый) + скрытие лишнего
st.markdown("""
    <style>
        :root {
            --primary-color: #10b981;
            --bg-color: #f8fafc;
        }
        .stApp {
            background-color: var(--bg-color);
        }
        /* Кнопки */
        div.stButton > button:first-child {
            background-color: #059669;
            color: white;
            border-radius: 8px;
            border: none;
            font-weight: 600;
        }
        div.stButton > button:first-child:hover {
            background-color: #047857;
        }
        /* Заголовки */
        h1, h2, h3 {
            color: #1e293b; 
        }
        /* Убираем отступы */
        .block-container {padding-top: 2rem;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
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
        st.error("🚨 Erreur de connexion : Vérifiez les Secrets (Supabase/Google).")
        st.stop()

supabase = init_connections()

# --- 3. INTELLIGENCE ARTIFICIELLE (AI) ---
def generate_hunter_email(company, segment, pain_point, product, lang):
    """Génère un email de prospection (Hunter)"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Agis comme un expert Business Developer (Hunter). Rédige un email de prospection à froid pour le Directeur R&D de {company}.
    Langue : {lang}.
    Contexte : Ils sont dans le secteur {segment}.
    Problème (Pain Point) : {pain_point}.
    Solution : Présenter {product} (Ingood by Olga).
    Proposition de valeur : Clean Label, Stabilité prix, Performance fonctionnelle.
    Ton : Professionnel, expert, concis, impactant.
    """
    return model.generate_content(prompt).text

def generate_rd_brief(company, segment, product, tech_notes, lang):
    """Génère un brief technique pour la R&D"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Agis comme le "Cerveau Ingood". Génère un Brief Projet R&D technique structuré.
    Langue : {lang}.
    Client : {company}.
    Produit Cible : {segment}.
    Solution Ingood envisagée : {product}.
    Contraintes Techniques / Notes : {tech_notes}.
    Objectif : Remplacement d'œuf ou amélioration de texture.
    Format : Liste structurée pour demande au labo.
    """
    return model.generate_content(prompt).text

# --- 4. GESTION DES DONNÉES ---
def load_data():
    """Charge les données depuis Supabase"""
    response = supabase.table("prospects").select("*").order("id", desc=True).execute()
    return pd.DataFrame(response.data)

def save_prospect(data, record_id=None):
    """Sauvegarde ou met à jour un prospect"""
    try:
        if record_id:
            supabase.table("prospects").update(data).eq("id", record_id).execute()
        else:
            supabase.table("prospects").insert(data).execute()
        st.toast("✅ Projet sauvegardé avec succès !", icon="💾")
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")
        return False

# --- 5. INTERFACE UTILISATEUR (UI) ---

# État de la navigation
if 'page' not in st.session_state:
    st.session_state.page = 'pipeline'
if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2921/2921222.png", width=40)
    st.markdown("### **Ingood OS**")
    
    if st.button("➕ Nouveau Projet", use_container_width=True):
        st.session_state.page = 'edit'
        st.session_state.edit_id = None
        st.rerun()
    
    st.markdown("---")
    
    if st.button("📊 Pipeline & Suivi", use_container_width=True):
        st.session_state.page = 'pipeline'
        st.rerun()

    st.markdown("---")
    st.caption("Export Données")
    
    # Bouton d'export Excel/CSV
    df = load_data()
    if not df.empty:
        st.download_button(
            label="📥 Télécharger (.csv)",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='pipeline_ingood.csv',
            mime='text/csv',
            use_container_width=True
        )

# --- PAGE 1: PIPELINE (TABLEAU) ---
if st.session_state.page == 'pipeline':
    # En-tête
    c1, c2 = st.columns([3, 1])
    c1.title("Pipeline Food & Ingrédients")
    c1.caption("Suivi des projets R&D et opportunités commerciales")
    c2.markdown("### <span style='background-color:#eff6ff; color:#1d4ed8; padding:5px 10px; border-radius:5px; border:1px solid #dbeafe;'>CFIA Ready 🚀</span>", unsafe_allow_html=True)
    
    # Filtres
    with st.expander("🔍 Filtres (Produits, Statuts, Application)", expanded=False):
        f1, f2, f3 = st.columns(3)
        df = load_data()
        if not df.empty:
            prod_filter = f1.multiselect("Ingrédient", df["product_interest"].unique())
            status_filter = f2.multiselect("Statut", df["status"].unique())
            segment_filter = f3.multiselect("Application", df["segment"].unique())
            
            # Appliquer les filtres
            if prod_filter: df = df[df["product_interest"].isin(prod_filter)]
            if status_filter: df = df[df["status"].isin(status_filter)]
            if segment_filter: df = df[df["segment"].isin(segment_filter)]

    # Tableau Principal
    if not df.empty:
        st.dataframe(
            df,
            column_order=("company_name", "status", "product_interest", "segment", "cfia_priority", "last_salon", "id"),
            column_config={
                "company_name": st.column_config.TextColumn("Société / Client", width="medium"),
                "status": st.column_config.SelectboxColumn(
                    "Statut",
                    options=["Prospection", "Qualification", "Envoi Échantillon", "Test R&D", "Négociation", "Client", "Perdu"],
                    width="medium"
                ),
                "product_interest": st.column_config.TextColumn("Produit", width="small"),
                "segment": st.column_config.TextColumn("Appli", width="small"),
                "cfia_priority": st.column_config.CheckboxColumn("Priorité CFIA", width="small"),
                "last_salon": st.column_config.TextColumn("Source / Salon", width="small"),
                "id": st.column_config.TextColumn("Réf", width="small"),
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Sélection pour ouvrir
        st.markdown("---")
        col_sel, col_btn = st.columns([3, 1])
        company_list = df["company_name"].unique()
        selected_company = col_sel.selectbox("📂 Sélectionner un dossier à ouvrir :", company_list)
        
        if col_btn.button("Ouvrir Fiche Projet >", type="primary"):
            record = df[df["company_name"] == selected_company].iloc[0]
            st.session_state.edit_id = int(record["id"])
            st.session_state.page = 'edit'
            st.rerun()

    else:
        st.info("Aucun prospect dans la base. Commencez par 'Nouveau Projet' !")


# --- PAGE 2: FICHE PROJET (ÉDITION) ---
elif st.session_state.page == 'edit':
    # Chargement des données
    if st.session_state.edit_id:
        res = supabase.table("prospects").select("*").eq("id", st.session_state.edit_id).execute()
        if res.data:
            record = res.data[0]
            page_title = f"Fiche : {record['company_name']}"
        else:
            st.error("Erreur : Projet introuvable.")
            st.stop()
    else:
        record = {}
        page_title = "Nouveau Projet"

    # Bouton Retour
    if st.button("← Retour au Pipeline"):
        st.session_state.page = 'pipeline'
        st.rerun()

    st.markdown(f"## {page_title}")
    
    # FORMULAIRE
    with st.form("prospect_form"):
        # Bloc 1 : Infos Clés
        c1, c2, c3 = st.columns(3)
        company = c1.text_input("Société / Client *", value=record.get("company_name", ""))
        status = c2.selectbox("Statut Pipeline", 
            ["Prospection", "Qualification", "Envoi Échantillon", "Test R&D", "Négociation", "Client", "Perdu"],
            index=["Prospection", "Qualification", "Envoi Échantillon", "Test R&D", "Négociation", "Client", "Perdu"].index(record.get("status", "Prospection"))
        )
        cfia = c3.checkbox("Cible Prioritaire CFIA ⭐️", value=record.get("cfia_priority", False))

        c4, c5, c6 = st.columns(3)
        contact = c4.text_input("Contact Clé (Nom)", value=record.get("contact_name", ""))
        email = c5.text_input("Email", value=record.get("email", ""))
        salon = c6.text_input("Dernier Salon / Source", value=record.get("last_salon", ""), placeholder="ex: CFIA 2026")

        st.markdown("---")

        # Onglets de Détails
        tab1, tab2, tab3 = st.tabs(["🏗 Contexte & Technique", "🧪 Échantillons", "🤖 Assistants IA"])

        with tab1:
            col_t1, col_t2 = st.columns(2)
            # Listes déroulantes
            prod_opts = ["", "LENGOOD", "PEPTIPEA", "SULFODYNE", "Autre"]
            seg_opts = ["", "Boulangerie", "Sauces", "Plats Cuisinés", "Nutraceutique", "Viande Végétale"]
            
            curr_prod = record.get("product_interest")
            curr_seg = record.get("segment")

            product = col_t1.selectbox("Ingrédient Ingood", prod_opts, index=prod_opts.index(curr_prod) if curr_prod in prod_opts else 0)
            segment = col_t2.selectbox("Application Finale", seg_opts, index=seg_opts.index(curr_seg) if curr_seg in seg_opts else 0)
            
            pain = st.text_area("Problématique / Besoin (Pain Point)", value=record.get("pain_points", ""), placeholder="Ex: Volatilité prix œuf, Texture trop sèche...")
            notes = st.text_area("Notes Techniques / Contexte", value=record.get("notes", ""), height=100)

        with tab2:
            st.info("ℹ️ Protocole R&D : Toujours valider la fiche technique avant envoi.")
            
            samp_opts = ["-", "À envoyer", "Envoyé", "Reçu", "En test", "Feedback reçu"]
            curr_samp = record.get("sample_status")
            sample_status = st.selectbox("Statut Échantillon actuel", samp_opts, index=samp_opts.index(curr_samp) if curr_samp in samp_opts else 0)
            
            tech_notes = st.text_area("Suivi Échantillons (Lots, Tracking, Feedback...)", value=record.get("tech_notes", ""))

        with tab3:
            st.markdown("### Générateurs de Contenu")
            ai_lang = st.radio("Langue de génération", ["Français", "English"], horizontal=True)
            
            c_ai1, c_ai2 = st.columns(2)
            with c_ai1:
                st.caption("Pour les Commerciaux")
                if st.form_submit_button("✨ Générer Email Hunter"):
                    if company:
                        res = generate_hunter_email(company, segment, pain, product, ai_lang)
                        st.session_state.ai_result = res
                    else:
                        st.warning("Veuillez d'abord remplir le nom de la société.")
            
            with c_ai2:
                st.caption("Pour l'équipe Technique")
                if st.form_submit_button("🧪 Générer Brief R&D"):
                    if company:
                        res = generate_rd_brief(company, segment, product, notes, ai_lang)
                        st.session_state.ai_result = res
                    else:
                        st.warning("Veuillez d'abord remplir le nom de la société.")

            # Affichage du résultat IA
            if 'ai_result' in st.session_state:
                st.text_area("Résultat IA (À copier):", value=st.session_state.ai_result, height=300)

        st.markdown("---")
        # Bouton Sauvegarde
        col_s1, col_s2 = st.columns([1, 1])
        if col_s2.form_submit_button("💾 Enregistrer le Projet", type="primary"):
            if not company:
                st.error("Le nom de la société est obligatoire.")
            else:
                new_data = {
                    "company_name": company,
                    "status": status,
                    "cfia_priority": cfia,
                    "contact_name": contact,
                    "email": email,
                    "last_salon": salon,
                    "product_interest": product,
                    "segment": segment,
                    "pain_points": pain,
                    "notes": notes,
                    "sample_status": sample_status,
                    "tech_notes": tech_notes
                }
                if save_prospect(new_data, st.session_state.edit_id):
                    st.session_state.page = 'pipeline'
                    st.rerun()
