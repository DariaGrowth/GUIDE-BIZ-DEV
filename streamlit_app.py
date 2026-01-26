import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime

# --- 1. CSS & DESIGN SYSTEM (LUXURY EMERALD THEME) ---
st.set_page_config(page_title="Ingood Growth", page_icon="🌿", layout="wide")

# Новая цветовая палитра: Глубокий дорогой зеленый
# Primary: #046c4e (Deep Emerald)
# Hover:   #065f46 (Darker Teal)
# Light:   #a7f3d0 (Soft Green for accents)

st.markdown("""
    <style>
        /* Общий фон - чистый и светлый */
        .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
        
        /* Сайдбар - белый с тонкой границей */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e2e8f0;
        }

        /* ЗАГОЛОВКИ - Темный строгий цвет */
        h1, h2, h3 { color: #1e293b; font-weight: 700; letter-spacing: -0.02em; }

        /* КАРТОЧКИ KPI (Метрики) - Дорогие и чистые */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0; /* Очень тонкая рамка */
            padding: 24px;
            border-radius: 12px; /* Менее скругленные, более строгие */
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -1px rgba(0, 0, 0, 0.03); /* Очень мягкая тень */
            transition: all 0.3s ease;
        }
        div[data-testid="stMetric"]:hover {
            border-color: #a7f3d0; /* Подсветка рамки при наведении */
            box-shadow: 0 10px 15px -3px rgba(4, 108, 78, 0.1), 0 4px 6px -2px rgba(4, 108, 78, 0.05);
            transform: translateY(-2px);
        }
        div[data-testid="stMetricLabel"] {
            font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em;
        }
        div[data-testid="stMetricValue"] {
            font-size: 36px; color: #046c4e; /* Глубокий изумруд */
            font-weight: 800;
        }

        /* КНОПКИ - Глубокий градиент и благородная тень */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #046c4e 0%, #065f46 100%); /* Градиент для объема */
            color: white; border: none;
            border-radius: 8px; font-weight: 600; padding: 0.6rem 1.2rem;
            box-shadow: 0 4px 10px rgba(4, 108, 78, 0.3); /* Цветная тень */
            transition: all 0.2s ease;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(135deg, #065f46 0%, #046c4e 100%);
            box-shadow: 0 6px 15px rgba(4, 108, 78, 0.4);
            transform: translateY(-1px);
        }
        div.stButton > button:first-child:active {
            transform: translateY(0px);
            box-shadow: 0 2px 5px rgba(4, 108, 78, 0.3);
        }

        /* ТАБЛИЦЫ - Чистые и аккуратные */
        div[data-testid="stDataFrame"] {
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
        }
        
        /* Убираем лишние отступы */
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ПОДКЛЮЧЕНИЕ ---
@st.cache_resource
def init_connections():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key), genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except:
        return None, None

supabase, _ = init_connections()
if not supabase: st.stop()

# --- 3. ФУНКЦИИ ---
def get_data():
    return pd.DataFrame(supabase.table("prospects").select("*").order("last_action_date", desc=True).execute().data)

def get_details(prospect_id, table):
    return pd.DataFrame(supabase.table(table).select("*").eq("prospect_id", prospect_id).order("id", desc=True).execute().data)

def add_activity(prospect_id, type_act, content):
    supabase.table("activities").insert({
        "prospect_id": prospect_id, "type": type_act, "content": content, "date": datetime.now().isoformat()
    }).execute()
    now = datetime.now().strftime("%Y-%m-%d")
    supabase.table("prospects").update({"last_action_date": now}).eq("id", prospect_id).execute()

# --- 4. AI ---
def get_hunter_prompt(company, segment, pain, product):
    return f"""Act as Hunter AI. Write a cold email in French to the R&D Director of {company}.
Context: Sector {segment}. Pain Point: {pain}. Solution: Introduce {product} from Ingood by Olga.
Value Prop: Clean Label, Price Stability. Tone: Professional & Direct."""

# --- 5. MODAL (FICHE PROJET - Чистые вкладки без пестрых иконок) ---
@st.dialog("Fiche Projet", width="large")
def show_prospect_card(prospect_id, p_data):
    # Используем современные, монохромные иконки Material Symbols
    tab1, tab2, tab3, tab4 = st.tabs([":material/description: Contexte", ":material/group: Contacts", ":material/package_2: Échantillons", ":material/bolt: AI & Activité"])
    
    with tab1:
        with st.form("edit_main"):
            c1, c2 = st.columns(2)
            comp = c1.text_input("Société", value=p_data["company_name"])
            status = c2.selectbox("Statut", ["Prospection", "Qualification", "Envoi Echantillon", "Test R&D", "Négociation", "Client"], index=["Prospection", "Qualification", "Envoi Echantillon", "Test R&D", "Négociation", "Client"].index(p_data["status"]))
            
            c3, c4, c5 = st.columns(3)
            segment = c3.selectbox("Segment", ["Boulangerie", "Sauces", "Nutraceutique", "Viande Végétale", "Autre"], index=0 if not p_data["segment"] else ["Boulangerie", "Sauces", "Nutraceutique", "Viande Végétale", "Autre"].index(p_data["segment"]))
            product = c4.selectbox("Produit", ["LENGOOD", "PEPTIPEA", "SULFODYNE"], index=0 if not p_data["product_interest"] else ["LENGOOD", "PEPTIPEA", "SULFODYNE"].index(p_data["product_interest"]))
            vol = c5.number_input("Volume (T)", value=float(p_data["potential_volume"] or 0))
            
            pain = st.text_area("Problématique R&D", value=p_data["tech_pain_points"])
            cfia = st.checkbox("Priorité CFIA", value=p_data["cfia_priority"]) # Убрали эмодзи огня
            
            if st.form_submit_button("💾 Sauvegarder"):
                supabase.table("prospects").update({
                    "company_name": comp, "status": status, "segment": segment,
                    "product_interest": product, "potential_volume": vol,
                    "tech_pain_points": pain, "cfia_priority": cfia
                }).eq("id", prospect_id).execute()
                st.rerun()

    with tab2:
        contacts = get_details(prospect_id, "contacts")
        if not contacts.empty:
            st.dataframe(contacts[["name", "role", "email"]], hide_index=True, use_container_width=True)
        with st.expander("Ajouter un contact"): # Убрали плюс
            with st.form("add_contact"):
                c_n = st.text_input("Nom"); c_r = st.text_input("Rôle"); c_e = st.text_input("Email")
                if st.form_submit_button("Ajouter"):
                    supabase.table("contacts").insert({"prospect_id": prospect_id, "name": c_n, "role": c_r, "email": c_e}).execute(); st.rerun()

    with tab3:
        samples = get_details(prospect_id, "samples")
        if not samples.empty:
            st.dataframe(samples[["product_name", "reference", "status", "date_sent"]], hide_index=True, use_container_width=True)
        with st.expander("Nouvel Échantillon"): # Убрали коробку
            with st.form("add_sample"):
                s_p = st.selectbox("Produit", ["LENGOOD", "PEPTIPEA"]); s_r = st.text_input("Référence (Lot)")
                if st.form_submit_button("Envoyer"):
                    supabase.table("samples").insert({"prospect_id": prospect_id, "product_name": s_p, "reference": s_r}).execute()
                    add_activity(prospect_id, "Sample", f"Envoi échantillon {s_p} ({s_r})"); st.rerun()

    with tab4:
        activities = get_details(prospect_id, "activities")
        if not activities.empty:
            for _, row in activities.iterrows():
                # Используем монохромные иконки для типов активности
                icon = ":material/mail:" if row['type'] == 'Sample' else ":material/edit_note:"
                st.write(f"{icon} **{row['date'][:10]}** | {row['content']}")
        
        st.divider()
        if st.button("Générer Prompt Hunter (AI)"): # Убрали эмодзи
            prompt = get_hunter_prompt(p_data["company_name"], p_data["segment"], p_data["tech_pain_points"], p_data["product_interest"])
            st.code(prompt, language="text")
        
        with st.form("quick_note"):
            note = st.text_area("Nouvelle note")
            if st.form_submit_button("Ajouter Note"): add_activity(prospect_id, "Note", note); st.rerun()

# --- 6. MAIN UI ---
with st.sidebar:
    # Логотип можно заменить на SVG для максимальной четкости, пока оставим чистую картинку
    st.image("https://cdn-icons-png.flaticon.com/512/2921/2921222.png", width=50) 
    st.title("Ingood Growth")
    st.caption("Status: Cadre | Focus: Food")
    
    # Навигация БЕЗ пестрых иконок. Чистая типографика.
    page = st.radio("Navigation", ["Dashboard", "Pipeline", "À Relancer"], label_visibility="collapsed")
    
    st.divider()
    # Кнопка с градиентом
    if st.button("Nouveau Prospect", use_container_width=True):
        res = supabase.table("prospects").insert({"company_name": "NOUVEAU CLIENT"}).execute()
        show_prospect_card(res.data[0]['id'], res.data[0])

# PAGE: DASHBOARD
if page == "Dashboard":
    st.title("Tableau de Bord")
    st.caption("Vue d'ensemble de la performance commerciale")
    df = get_data()
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Projets", len(df))
        c2.metric("Tests R&D En Cours", len(df[df['status'] == 'Test R&D']))
        vol = df['potential_volume'].sum() if 'potential_volume' in df.columns else 0
        c3.metric("Volume Potentiel", f"{vol:.0f} T")
        c4.metric("Clients Gagnés", len(df[df['status'] == 'Client']))
        st.markdown("---")
        cl, cr = st.columns(2)
        # Новая, дорогая палитра для графиков
        luxury_colors = ['#046c4e', '#059669', '#10b981', '#34d399', '#6ee7b7']
        with cl:
            st.subheader("Répartition Segments")
            fig_pie = px.pie(df, names='segment', color_discrete_sequence=luxury_colors, hole=0.5)
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
            fig_pie.update_traces(textposition='outside', textinfo='label+percent')
            st.plotly_chart(fig_pie, use_container_width=True)
        with cr:
            st.subheader("Pipeline Statut")
            s_c = df['status'].value_counts().reset_index(); s_c.columns = ['status', 'count']
            # Барчарт в одном глубоком цвете
            fig_bar = px.bar(s_c, x='status', y='count', color_discrete_sequence=['#046c4e'], text='count')
            fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title=None, margin=dict(t=0, b=0, l=0, r=0), yaxis=dict(showgrid=True, gridcolor='#e2e8f0'))
            st.plotly_chart(fig_bar, use_container_width=True)
    else: st.info("Base vide.")

# PAGE: PIPELINE
elif page == "Pipeline":
    st.title("Pipeline Food & Ingrédients")
    df = get_data()
    if not df.empty:
        search = st.text_input("Rechercher...", placeholder="Nom, produit...")
        with st.expander("Filtres Avancés", expanded=False): # Свернули фильтры по умолчанию для чистоты
            f1, f2, f3, f4 = st.columns(4)
            s_p = f1.multiselect("Produits", df["product_interest"].unique())
            s_s = f2.multiselect("Statuts", df["status"].unique())
            s_sal = f3.multiselect("Salons", df["last_salon"].dropna().unique())
            s_c = f4.multiselect("Pays", df["country"].dropna().unique())
        
        if search: df = df[df.apply(lambda x: search.lower() in str(x.values).lower(), axis=1)]
        if s_p: df = df[df["product_interest"].isin(s_p)]
        if s_s: df = df[df["status"].isin(s_s)]
        if s_sal: df = df[df["last_salon"].isin(s_sal)]
        if s_c: df = df[df["country"].isin(s_c)]

        df['company_name'] = df['company_name'].str.upper()
        df['product_interest'] = df['product_interest'].str.upper()
        if 'sample_status' not in df.columns: df['sample_status'] = '-'
        # Используем современные монохромные иконки Material
        sample_icons = {'Envoyé': ':material/send: Envoyé', 'En test': ':material/science: En test', 'Reçu': ':material/inbox: Reçu', 'Validé': ':material/check_circle: Validé', 'Rejeté': ':material/cancel: Rejeté', '-': '-'}
        df['sample_display'] = df['sample_status'].map(sample_icons).fillna(df['sample_status'])

        st.dataframe(
            df,
            column_order=("company_name", "country", "product_interest", "status", "last_action_date", "sample_display", "cfia_priority"),
            column_config={
                "company_name": st.column_config.TextColumn("Société", width="medium"),
                "country": st.column_config.TextColumn("Pays", width="small"),
                "product_interest": st.column_config.TextColumn("Produit", width="small"),
                "status": st.column_config.SelectboxColumn("Statut", options=["Prospection", "Qualification", "Test R&D", "Négociation", "Client"], width="medium"),
                "last_action_date": st.column_config.DateColumn("Contact", format="DD.MM.YY"),
                "sample_display": st.column_config.TextColumn("Échantillons", width="medium"),
                "cfia_priority": st.column_config.CheckboxColumn("CFIA", width="small"),
            }, hide_index=True, use_container_width=True
        )
        st.markdown("---")
        c_sel, c_btn = st.columns([3, 1])
        sel_comp = c_sel.selectbox("Ouvrir le dossier de :", df["company_name"].unique(), label_visibility="collapsed")
        if c_btn.button("Accéder au dossier", type="primary", use_container_width=True):
            row = df[df["company_name"] == sel_comp].iloc[0]
            show_prospect_card(row['id'], row)
    else: st.info("Aucun résultat.")

# PAGE: A RELANCER
elif page == "À Relancer":
    st.title("Priorité Relance")
    df = get_data()
    if not df.empty:
        today = datetime.now().date(); df['last_action_date'] = pd.to_datetime(df['last_action_date']).dt.date
        mask = df.apply(lambda x: (x['status'] != 'Client') and ((today - x['last_action_date']).days > 45), axis=1)
        stale = df[mask]
        if not stale.empty:
             # Добавляем иконку предупреждения
             stale['Alerte'] = ':material/warning:'
             st.dataframe(stale[["Alerte", "company_name", "last_action_date", "tech_pain_points"]], hide_index=True, use_container_width=True, column_config={"Alerte": st.column_config.TextColumn("", width="small")})
        else: st.success("Tout est à jour.")
