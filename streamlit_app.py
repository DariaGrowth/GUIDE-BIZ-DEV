import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime
import io
import numpy as np
import time

# --- 1. CONFIGURATION & DESIGN SYSTEM ---
st.set_page_config(page_title="Ingood Growth", page_icon="favicon.png", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #046c4e 0%, #065f46 100%);
            color: white; border: none; border-radius: 6px; font-weight: 600;
            box-shadow: 0 4px 6px rgba(4, 108, 78, 0.2);
        }
        
        div[data-testid="stMetric"] {
            background-color: white; border: 1px solid #e2e8f0; border-radius: 10px;
            padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        div[data-testid="stMetricValue"] { color: #046c4e; font-weight: 800; }
        h1, h2, h3 { color: #1e293b; font-weight: 700; }
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
    
    # 1. Создаем каркас, если пусто
    if df.empty:
        if table == "contacts":
            df = pd.DataFrame(columns=["id", "name", "role", "email"])
        elif table == "samples":
            return pd.DataFrame(columns=["id", "date_sent", "product_name", "reference", "status", "feedback"])
        elif table == "activities":
            return pd.DataFrame(columns=["id", "date", "type", "content"])
            
    # 2. ЖЕСТКАЯ ТИПИЗАЦИЯ ДЛЯ КОНТАКТОВ (Исправляет баг с Email)
    if table == "contacts":
        # Гарантируем, что колонки существуют
        for col in ["name", "role", "email"]:
            if col not in df.columns:
                df[col] = ""
        
        # Принудительно делаем всё строками (избавляемся от NaN/None)
        df["name"] = df["name"].fillna("").astype(str)
        df["role"] = df["role"].fillna("").astype(str)
        df["email"] = df["email"].fillna("").astype(str)

        # Убираем текстовые артефакты "None", если они вдруг появились
        df["role"] = df["role"].replace({"None": "", "nan": ""})
        df["email"] = df["email"].replace({"None": "", "nan": ""})

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

    # TAB 1: Contexte + Contacts
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
            
            # Загрузка подготовленных данных
            contacts_df = get_sub_data("contacts", pid)
            
            # Редактор таблицы
            edited_contacts = st.data_editor(
                contacts_df,
                column_config={
                    "id": None, # Скрываем ID
                    "name": st.column_config.TextColumn("Nom", required=True),
                    "role": st.column_config.TextColumn("Rôle"),
                    "email": st.column_config.TextColumn("Email")
                },
                column_order=("name", "role", "email"), 
                num_rows="dynamic",
                use_container_width=True,
                key="contact_editor"
            )

            if st.form_submit_button("💾 Enregistrer Tout", type="primary"):
                with st.spinner("Sauvegarde..."):
                    # 1. Обновляем Проспект
                    supabase.table("prospects").update({
                        "status": stat, "country": pays, "potential_volume": vol,
                        "last_salon": salon, "cfia_priority": cfia,
                        "product_interest": prod, "segment": app,
                        "tech_pain_points": pain, "tech_notes": notes
                    }).eq("id", pid).execute()
                    
                    # 2. Обновляем Контакты (Безопасный метод)
                    if not edited_contacts.empty:
                        # Фильтруем пустые строки, если случайно создались
                        edited_contacts = edited_contacts.replace({np.nan: None})
                        
                        count = 0
                        for index, row in edited_contacts.iterrows():
                            # Берем значения как строки и чистим пробелы
                            name_val = str(row["name"]).strip()
                            role_val = str(row["role"]).strip()
                            email_val = str(row["email"]).strip()
                            
                            # Убираем артефакты "None" и "nan"
                            if role_val.lower() in ["none", "nan"]: role_val = ""
                            if email_val.lower() in ["none", "nan"]: email_val = ""

                            if name_val: # Сохраняем, только если есть имя
                                contact_data = {
                                    "prospect_id": pid, 
                                    "name": name_val,
                                    "role": role_val, 
                                    "email": email_val
                                }
                                
                                # Если есть ID (существующий контакт) -> обновляем
                                if row.get("id") and pd.notna(row["id"]):
                                     contact_data["id"] = int(row["id"])
                                     supabase.table("contacts").upsert(contact_data).execute()
                                # Если нет ID (новый) -> создаем
                                else:
                                     supabase.table("contacts").insert(contact_data).execute()
                                count += 1
                        
                    time.sleep(1.2) # Пауза для синхронизации с базой
                    
                st.toast(f"✅ Sauvegardé ! ({count if 'count' in locals() else 0} contacts mis à jour)")
                st.rerun()

    # TAB 2
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

    # TAB 3
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

# --- 6. MAIN UI ---
with st.sidebar:
    st.image("favicon.png", width=60)
    st.title("Ingood Growth")
    page = st.radio("Menu", ["Dashboard", "Pipeline", "Contacts"], label_visibility="collapsed")
    st.divider()
    if st.button("➕ Nouveau Prospect", use_container_width=True):
        res = supabase.table("prospects").insert({"company_name": "NOUVEAU CLIENT"}).execute()
        show_prospect_card(int(res.data[0]['id']), res.data[0])

if page == "Dashboard":
    st.title("Tableau de Bord")
    df = get_data()
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Projets", len(df))
        c2.metric("R&D", len(df[df['status'] == 'Test R&D']))
        c3.metric("Volume", f"{df['potential_volume'].sum():.0f}")
        c4.metric("Clients", len(df[df['status'] == 'Client']))
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

elif page == "Pipeline":
    st.title("Pipeline")
    df = get_data()
    if not df.empty:
        search = st.text_input("Recherche...", placeholder="Société...")
        with st.expander("Filtres", expanded=False):
            f1, f2, f3 = st.columns(3)
            p = f1.multiselect("Produit", df["product_interest"].unique())
            s = f2.multiselect("Statut", df["status"].unique())
            c = f3.multiselect("Pays", df["country"].unique())
        
        if search: df = df[df.apply(lambda x: search.lower() in str(x.values).lower(), axis=1)]
        if p: df = df[df["product_interest"].isin(p)]
        if s: df = df[df["status"].isin(s)]
        if c: df = df[df["country"].isin(c)]

        df['company_name'] = df['company_name'].str.upper()
        st.dataframe(df, column_order=("company_name", "country", "product_interest", "status", "last_action_date", "cfia_priority"), hide_index=True, use_container_width=True)
        
        st.markdown("---")
        c_sel, c_btn = st.columns([3, 1])
        sel = c_sel.selectbox("Dossier", df["company_name"].unique(), label_visibility="collapsed")
        if c_btn.button("Ouvrir", type="primary", use_container_width=True):
            row = df[df["company_name"] == sel].iloc[0]
            show_prospect_card(int(row['id']), row)

elif page == "Contacts":
    st.title("Contacts")
    all_c = get_all_contacts()
    if not all_c.empty:
        search = st.text_input("Recherche contact...")
        if search:
            mask = all_c.apply(lambda x: search.lower() in str(x.values).lower(), axis=1)
            all_c = all_c[mask]
        
        st.dataframe(all_c, column_order=("name", "role", "company_name", "email"), hide_index=True, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            all_c.to_excel(writer, sheet_name='Contacts', index=False)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name="contacts.xlsx", mime="application/vnd.ms-excel")
    else:
        st.info("Aucun contact.")
