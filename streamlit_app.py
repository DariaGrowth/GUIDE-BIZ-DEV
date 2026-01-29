import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta
import io
import numpy as np
import time

# --- 1. КОНФИГУРАЦИЯ И СТИЛИ ---
st.set_page_config(page_title="Ingood Growth", page_icon="favicon.png", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* БАЗОВЫЕ НАСТРОЙКИ */
        .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; color: #334155; }
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        div[data-testid="stVerticalBlock"] { gap: 0rem; }
        
        /* СТИЛИЗАЦИЯ ПОЛЕЙ ВВОДА */
        .stMarkdown label p, .stTextInput label p, .stNumberInput label p, .stSelectbox label p, .stTextArea label p {
            color: #64748b !important; font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.5px;
        }

        /* КНОПКИ ГЛОБАЛЬНО */
        [data-testid="stSidebar"] .stButton > button, 
        button[kind="primary"] {
            width: 100%; background-color: #047857 !important; color: white !important;
            border: none; border-radius: 6px; padding: 10px 16px; font-weight: 600; font-size: 14px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1); transition: all 0.2s ease;
        }
        [data-testid="stSidebar"] .stButton > button:hover,
        button[kind="primary"]:hover { background-color: #065f46 !important; transform: translateY(-1px); }
        
        button[kind="secondary"] {
            background-color: white !important; border: 1px solid #fee2e2 !important; color: #ef4444 !important;
        }

        /* КАНБАН-КАРТОЧКИ */
        .kanban-card {
            background: white; border: 1px solid #e2e8f0; border-radius: 8px;
            padding: 15px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }
        .kanban-card:hover { border-color: #10b981; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .kanban-title { font-weight: 700; color: #1e293b; font-size: 14px; margin-bottom: 5px; }
        .kanban-sub { color: #64748b; font-size: 11px; margin-bottom: 10px; line-height: 1.4; }

        /* ХАКИ ДЛЯ ПАЙПЛАЙНА */
        div[data-testid="column"]:first-child .stButton > button {
            background-color: transparent !important; border: none !important;
            color: #0f172a !important; font-weight: 700 !important; font-size: 14px !important;
            text-align: left !important; padding: 0px !important; box-shadow: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. ПОДКЛЮЧЕНИЯ ---
@st.cache_resource
def init_connections():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key), genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except: return None, None

supabase, _ = init_connections()
if not supabase: st.stop()

# --- 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
if 'pipeline_key' not in st.session_state: st.session_state['pipeline_key'] = 0

def reset_pipeline(): 
    st.session_state['pipeline_key'] += 1
    st.cache_data.clear()
    safe_del('active_prospect_id')
    safe_del('ai_draft')

def safe_del(key): 
    if key in st.session_state: del st.session_state[key]

# --- 4. РАБОТА С ДАННЫМИ ---
@st.cache_data(ttl=60)
def get_data(): 
    return pd.DataFrame(supabase.table("prospects").select("*").order("last_action_date", desc=True).execute().data)

def get_sub_data(t, pid):
    d = supabase.table(t).select("*").eq("prospect_id", pid).order("id", desc=True).execute().data
    df = pd.DataFrame(d)
    if df.empty:
        if t == "contacts": return pd.DataFrame(columns=["id", "name", "role", "email", "phone"])
        if t == "samples": return pd.DataFrame(columns=["id", "date_sent", "product_name", "reference", "status", "feedback"])
        if t == "activities": return pd.DataFrame(columns=["id", "date", "type", "content"])
    return df

def count_relances():
    # Быстрый фильтр на стороне базы: нет фидбека и отправлено более 15 дней назад
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    try:
        res = supabase.table("samples").select("id", count="exact").is_("feedback", "null").lte("date_sent", fifteen_days_ago).execute()
        return res.count if res.count else 0
    except: return 0

def add_log(pid, t, c):
    supabase.table("activities").insert({"prospect_id": pid, "type": t, "content": c, "date": datetime.now().isoformat()}).execute()
    supabase.table("prospects").update({"last_action_date": datetime.now().strftime("%Y-%m-%d")}).eq("id", pid).execute()

def ai_mail(ctx):
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model.generate_content(f"Act as B2B email assistant. French language. Context: {ctx}. Short and professional.").text

# --- 5. FICHE PROSPECT (МОДАЛЬНОЕ ОКНО) ---
@st.dialog(" ", width="large")
def show_prospect_card(pid, data):
    pid = int(pid)
    st.markdown(f"<h2 style='margin-top: -30px; margin-bottom: 25px; font-size: 26px; color: #1e293b; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; font-weight: 700;'>{data['company_name']}</h2>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 2], gap="large")

    with c_left:
        with st.container(border=True):
            name = st.text_input("Société", value=data['company_name'], key=f"n_{pid}")
            # Маппинг статусов
            opts = ["🔭 Prospection", "📋 Qualification", "📦 Echantillon", "🔬 Test R&D", "🏭 Essai industriel", "⚖️ Négociation", "✅ Client signé"]
            curr = data.get("status", "Prospection")
            stat = st.selectbox("Statut", opts, index=next((i for i, s in enumerate(opts) if curr in s), 0))
            
            c1, c2 = st.columns(2)
            with c1: pays = st.text_input("Pays", value=data.get("country", ""))
            with c2: vol = st.number_input("Potentiel (T)", value=float(data.get("potential_volume") or 0))
            
            st.markdown("---")
            st.markdown("<p style='font-size:11px; font-weight:700; color:#64748b;'>AI ASSISTANT</p>", unsafe_allow_html=True)
            tone = st.selectbox("Ton", ["Professionnel", "Amical", "Relance urgente"], label_visibility="collapsed")
            if st.button("🪄 Générer l'Email", use_container_width=True):
                with st.spinner("Rédaction..."):
                    context = f"Client: {data['company_name']}, Produit: {data.get('product_interest')}, Ton: {tone}"
                    st.session_state['ai_draft'] = ai_mail(context)
            
            if 'ai_draft' in st.session_state:
                st.text_area("Brouillon AI", value=st.session_state['ai_draft'], height=150)
                st.caption("Copy-paste with Ctrl+C")

    with c_right:
        t1, t2, t3 = st.tabs(["Contexte", "Échantillons", "Journal"])
        with t1:
            # Защита от ValueError: проверка наличия значения в списке
            prod_list = ["LEN", "PEP", "NEW"]
            p_val = data.get("product_interest")
            p_idx = prod_list.index(p_val) if p_val in prod_list else 0
            
            app_list = ["Boulangerie", "Sauces", "Confiserie"]
            a_val = data.get("segment")
            a_idx = app_list.index(a_val) if a_val in app_list else 0

            c1, c2 = st.columns(2)
            with c1: prod = st.selectbox("Ingrédient", prod_list, index=p_idx)
            with c2: app = st.selectbox("Application", app_list, index=a_idx)
            
            st.markdown("---")
            st.markdown("<p style='font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase;'>CONTACTS CLÉS</p>", unsafe_allow_html=True)
            contacts = st.data_editor(get_sub_data("contacts", pid), column_config={"id": None}, num_rows="dynamic", use_container_width=True, key=f"ed_{pid}")

        with t2:
            with st.container(border=True):
                c1, c2, _, c3 = st.columns([1.5, 2, 0.1, 1.2]) 
                with c1: ref = st.text_input("Ref", key="nr")
                with c2: pr = st.selectbox("Produit", ["LEN", "PEP", "NEW"], key="np")
                with c3: 
                    st.write(""); st.write("")
                    if st.button("Enregistrer", key="ss", type="primary"): 
                        supabase.table("samples").insert({"prospect_id": pid, "reference": ref, "product_name": pr, "status": "Envoyé", "date_sent": datetime.now().isoformat()}).execute(); st.rerun()
            st.write(""); st.markdown("##### Historique")
            for _, r in get_sub_data("samples", pid).iterrows():
                with st.container(border=True):
                    st.markdown(f"**{r['product_name']}** | {r['reference']} <span style='color:gray; font-size:12px'>({r['date_sent'][:10]})</span>", unsafe_allow_html=True)
                    st.caption(f"Status: {r['status']}")

        with t3:
            n = st.text_area("Note...", key="nn")
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
                "company_name": name, "status": stat, "country": pays, "potential_volume": vol,
                "product_interest": prod, "segment": app, "last_action_date": datetime.now().isoformat()
            }).eq("id", pid).execute()
            
            # Логика обновления/удаления контактов
            if not contacts.empty:
                current_ids = [int(x) for x in contacts['id'].dropna() if str(x).isdigit()] if 'id' in contacts.columns else []
                old_contacts = get_sub_data("contacts", pid)
                if not old_contacts.empty:
                    old_ids = old_contacts['id'].tolist()
                    to_delete = [oid for oid in old_ids if oid not in current_ids]
                    if to_delete: supabase.table("contacts").delete().in_("id", to_delete).execute()

                for r in contacts.to_dict('records'):
                    if str(r.get("name")).strip():
                        d = {"prospect_id": pid, "name": r["name"], "role": r.get("role",""), "email": r.get("email",""), "phone": r.get("phone","")}
                        if r.get("id") and not pd.isna(r.get("id")):
                            supabase.table("contacts").upsert({**d, "id": int(r["id"])}).execute()
                        else:
                            supabase.table("contacts").insert(d).execute()
            
            reset_pipeline(); st.rerun()

# --- 6. SIDEBAR ---
with st.sidebar:
    st.image("favicon.png", width=65)
    if st.button("Nouveau Projet"):
        res = supabase.table("prospects").insert({"company_name": "Nouveau Prospect", "status": "🔭 Prospection"}).execute()
        st.session_state['open_new_id'] = res.data[0]['id']; st.rerun()
    st.write("")
    rc = count_relances()
    pg = st.radio("Navigation", ["Tableau de Bord", "Kanban", "Pipeline", "Contacts", "À Relancer"], 
                  format_func=lambda x: f"{'🔔' if x=='À Relancer' and rc else '≡'} {x}", index=1)
    st.markdown("---"); st.caption("👤 Daria Growth")

# --- 7. РОУТИНГ КАРТОЧЕК ---
if 'open_new_id' in st.session_state:
    st.session_state['active_prospect_id'] = st.session_state.pop('open_new_id'); reset_pipeline()

if 'active_prospect_id' in st.session_state:
    try:
        data_row = supabase.table("prospects").select("*").eq("id", st.session_state['active_prospect_id']).execute().data[0]
        show_prospect_card(st.session_state['active_prospect_id'], data_row)
    except: safe_del('active_prospect_id')

# --- 8. СТРАНИЦЫ ---
if pg == "Kanban":
    st.title("Board Commercial")
    df = get_data()
    stages = ["🔭 Prospection", "📋 Qualification", "📦 Echantillon", "🔬 Test R&D"]
    st_cols = st.columns(len(stages))
    
    for i, stage in enumerate(stages):
        with st_cols[i]:
            st.markdown(f"<p style='font-weight:700; color:#047857; border-bottom: 2px solid #e2e8f0; padding-bottom:5px; margin-bottom:15px;'>{stage.upper()}</p>", unsafe_allow_html=True)
            # Фильтр по названию стадии (после эмодзи)
            keyword = stage.split(' ')[1]
            stage_df = df[df['status'].str.contains(keyword, na=False)] if not df.empty else pd.DataFrame()
            
            for _, row in stage_df.iterrows():
                with st.container():
                    st.markdown(f"""
                        <div class="kanban-card">
                            <div class="kanban-title">{row['company_name']}</div>
                            <div class="kanban-sub">{row['country'] or 'N/A'} • {row['product_interest'] or 'N/A'}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    k1, k2 = st.columns([3, 1])
                    with k1:
                        if st.button("Détails", key=f"kan_{row['id']}", use_container_width=True):
                            st.session_state['active_prospect_id'] = row['id']; st.rerun()
                    with k2:
                        if i < len(stages) - 1:
                            if st.button("→", key=f"mov_{row['id']}"):
                                next_stage = stages[i+1]
                                supabase.table("prospects").update({"status": next_stage}).eq("id", row['id']).execute()
                                reset_pipeline(); st.rerun()

elif pg == "Tableau de Bord":
    st.title("Analyses CRM")
    df = get_data()
    if not df.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Projets Total", len(df))
        m2.metric("En Test", len(df[df['status'].str.contains('Test', na=False)]))
        m3.metric("Volume Potential", f"{int(df['potential_volume'].sum())} T")
        
        c_l, c_r = st.columns(2)
        with c_l: st.plotly_chart(px.pie(df, names='product_interest', hole=.4, title="Mix Produits", color_discrete_sequence=px.colors.sequential.Greens_r), use_container_width=True)
        with c_r: st.plotly_chart(px.bar(df['status'].value_counts(), title="Tunnel de vente", color_discrete_sequence=['#047857']), use_container_width=True)

elif pg == "Pipeline":
    st.title("Liste de Pipeline")
    df = get_data()
    for _, row in df.iterrows():
        with st.container(border=True):
            cl1, cl2, cl3 = st.columns([2, 1, 1])
            if cl1.button(row['company_name'], key=f"p_{row['id']}"):
                st.session_state['active_prospect_id'] = row['id']; st.rerun()
            cl2.write(f"🌍 {row['country']}")
            cl3.write(f"🏷️ {row['status']}")

elif pg == "Contacts":
    st.title("Annuaire Contacts")
    cont = pd.DataFrame(supabase.table("contacts").select("*").execute().data)
    if not cont.empty: st.dataframe(cont, use_container_width=True)
    else: st.info("Aucun contact trouvé.")

elif pg == "À Relancer":
    st.title("Relances prioritaires 🔔")
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    s_rel = pd.DataFrame(supabase.table("samples").select("*").is_("feedback", "null").lte("date_sent", fifteen_days_ago).execute().data)
    if not s_rel.empty: st.dataframe(s_rel, use_container_width=True)
    else: st.success("Félicitations ! Aucun retard détecté.")
