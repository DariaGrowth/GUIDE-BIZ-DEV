import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta
import io
import numpy as np
import time

# --- 1. CONFIGURATION & STYLES ---
st.set_page_config(page_title="Ingood Growth", page_icon="favicon.png", layout="wide")

# CSS для создания профессионального интерфейса (Белый фон, компактность, акценты Ingood)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* Глобальный стиль приложения */
        .stApp { 
            background-color: #ffffff !important; 
            font-family: 'Inter', sans-serif; 
        }
        
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }

        /* Устранение лишних отступов Streamlit */
        [data-testid="stVerticalBlock"] { gap: 0rem !important; }
        
        /* Стиль кнопки "Nouveau Projet" */
        [data-testid="stSidebar"] .stButton > button {
            width: 100%; background-color: #047857 !important; color: white !important;
            border: none; border-radius: 6px; padding: 10px 16px; font-weight: 600;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1); transition: all 0.2s;
        }
        [data-testid="stSidebar"] .stButton > button:hover { background-color: #065f46 !important; transform: translateY(-1px); }

        /* Блок фильтров Pipeline */
        div[data-testid="stVerticalBlock"] > div:nth-child(1) > div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #047857 !important; border: none !important; border-radius: 8px !important;
            padding: 12px 20px !important; margin-bottom: 15px !important;
        }
        .filter-label-white { color: #ffffff !important; font-weight: 700; font-size: 14px; }

        /* Шапка таблицы (Зеленый текст Ingood) */
        .pipeline-header-row {
            background-color: transparent !important; border: none !important;
            padding: 12px 15px 8px 15px; margin-bottom: 5px; display: flex; align-items: center;
        }
        .header-text-style { 
            color: #047857 !important; font-size: 14px !important; font-weight: 800 !important; 
            text-transform: uppercase; letter-spacing: 0.5px;
        }

        /* Строки таблицы (Компактные белые карточки) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important; border: none !important;
            border-bottom: 1px solid #f1f5f9 !important; border-radius: 0px !important;
            padding: 2px 15px !important; margin-bottom: 0px !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover { background-color: #fcfdfd !important; }

        /* Название компании (Кликабельный жирный текст) */
        div[data-testid="column"]:first-child .stButton > button {
            background: transparent !important; border: none !important; padding: 0 !important;
            margin: 0 !important; color: #047857 !important; font-weight: 800 !important;
            font-size: 15px !important; text-align: left !important; box-shadow: none !important;
            min-height: 0px !important; height: 32px !important; line-height: 32px !important;
            display: inline-block !important; width: auto !important;
        }
        div[data-testid="column"]:first-child .stButton > button:hover { text-decoration: underline !important; color: #065f46 !important; }

        /* Сайдбар навигация */
        div[role="radiogroup"] label {
            display: flex; align-items: center; padding: 8px 16px; color: #475569; font-size: 14px; border-radius: 6px;
        }
        div[role="radiogroup"] label[data-checked="true"] { 
            background-color: rgba(16, 185, 129, 0.08) !important; color: #047857 !important; font-weight: 600; 
        }

        /* Бейджи и статусы */
        .badge-ui { padding: 2px 10px; border-radius: 10px; font-size: 10px; font-weight: 700; display: inline-block; }
        .bg-yellow { background: #fef9c3; color: #854d0e; }
        .bg-gray { background: #f1f5f9; color: #64748b; }
        .bg-green { background: #dcfce7; color: #166534; }
        .bg-blue { background: #eff6ff; color: #1d4ed8; border: 1px solid #dbeafe; }

        /* Мусорка в образцах (Идеальное выравнивание) */
        .trash-container { display: flex; align-items: center; justify-content: flex-end; height: 32px; }
        .trash-container button {
            background: transparent !important; border: none !important; box-shadow: none !important;
            color: #94a3b8 !important; padding: 0 !important; font-size: 18px !important;
        }
        .trash-container button:hover { color: #ef4444 !important; }

        /* Kanban карточки */
        .kanban-card {
            background: white; border: 1px solid #e2e8f0; border-radius: 8px;
            padding: 12px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNECTIONS & SETUP ---
@st.cache_resource
def init_connections():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key), genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None, None

supabase, _ = init_connections()
if not supabase: st.stop()

# --- 3. BUSINESS LOGIC & HELPERS ---
if 'pipeline_key' not in st.session_state: st.session_state['pipeline_key'] = 0

def reset_pipeline(): 
    st.session_state['pipeline_key'] += 1
    st.cache_data.clear()
    safe_del('active_prospect_id')
    safe_del('ai_draft')

def safe_del(key): 
    if key in st.session_state: del st.session_state[key]

@st.cache_data(ttl=60)
def get_data(): 
    try:
        res = supabase.table("prospects").select("*").order("last_action_date", desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def get_sub_data(t, pid):
    d = supabase.table(t).select("*").eq("prospect_id", pid).order("id", desc=True).execute().data
    df = pd.DataFrame(d)
    if df.empty:
        if t == "contacts": return pd.DataFrame(columns=["id", "name", "role", "email", "phone"])
        if t == "samples": return pd.DataFrame(columns=["id", "date_sent", "product_name", "reference", "status", "feedback"])
        if t == "activities": return pd.DataFrame(columns=["id", "date", "type", "content"])
    return df

def count_relances():
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    try:
        res = supabase.table("samples").select("id", count="exact").is_("feedback", "null").lte("date_sent", fifteen_days_ago).execute()
        return res.count if res.count else 0
    except: return 0

# --- 4. MODAL: FICHE PROSPECT ---
@st.dialog(" ", width="large")
def show_prospect_card(pid, data):
    pid = int(pid)
    st.markdown(f"<h2 style='margin-top: -30px; margin-bottom: 25px; font-size: 22px; color: #1e293b; font-weight: 800;'>{data['company_name']}</h2>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 2], gap="large")

    with c_left:
        with st.container(border=True):
            name = st.text_input("SOCIÉTÉ / CLIENT", value=data['company_name'], key=f"n_{pid}")
            opts = ["Prospection", "Qualification", "Echantillon", "Test R&D", "Essai industriel", "Négociation", "Client signé"]
            curr_stat = data.get("status", "Prospection")
            stat = st.selectbox("STATUT PIPELINE", opts, index=next((i for i, s in enumerate(opts) if s in curr_stat), 0))
            
            cl1, cl2 = st.columns(2)
            with cl1: pays = st.text_input("PAYS", value=data.get("country", ""))
            with cl2: vol = st.number_input("POTENTIEL (T)", value=float(data.get("potential_volume") or 0))
            
            last_c_str = data.get("last_action_date") or datetime.now().strftime("%Y-%m-%d")
            try: last_c_date = st.date_input("DERNIER CONTACT", value=datetime.strptime(last_c_str[:10], "%Y-%m-%d"))
            except: last_c_date = st.date_input("DERNIER CONTACT", value=datetime.now())
            
            st.markdown("---")
            st.markdown("<p style='font-size:11px; font-weight:700; color:#64748b;'>AI ASSISTANT</p>", unsafe_allow_html=True)
            tone = st.selectbox("Ton du message", ["Professionnel", "Relance amicale", "Urgent / Technique"], key=f"ai_tone_{pid}")
            if st.button("🪄 Générer l'Email", use_container_width=True):
                with st.spinner("Rédaction en cours..."):
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    ctx = f"Client: {data['company_name']}, Produit: {data.get('product_interest')}, Statut: {stat}, Ton: {tone}"
                    res = model.generate_content(f"Rédiger un email commercial B2B court et efficace en français pour ce contexte: {ctx}").text
                    st.session_state['ai_draft'] = res
            if 'ai_draft' in st.session_state:
                st.text_area("Brouillon AI", value=st.session_state['ai_draft'], height=180)

    with c_right:
        t1, t2, t3 = st.tabs(["Contexte & Technique", "Suivi Échantillons", "Journal d'Activité"])
        
        with t1:
            prod_opts = ["LENGOOD® (Substitut Œuf)", "PEPTIPEA® (Protéine)", "NEWGOOD® (Nouveauté)"]
            p_val = data.get("product_interest")
            p_idx = prod_opts.index(p_val) if p_val in prod_opts else 0
            
            app_opts = ["Boulangerie / Pâtisserie", "Sauces / Mayonnaise", "Confiserie", "Plats cuisinés", "Boissons"]
            a_val = data.get("segment")
            a_idx = app_opts.index(a_val) if a_val in app_opts else 0

            cr1, cr2 = st.columns(2)
            with cr1: prod = st.selectbox("INGRÉDIENT INGOOD", prod_opts, index=p_idx)
            with cr2: app = st.selectbox("APPLICATION FINALE", app_opts, index=a_idx)
            
            pain = st.text_area("PROBLÉMATIQUE / BESOIN (PAIN POINT)", value=data.get("notes", ""), height=80)
            tech = st.text_area("NOTES TECHNIQUES", value=data.get("tech_notes", ""), height=80)
            
            st.markdown("##### CONTACTS")
            contacts_df = st.data_editor(get_sub_data("contacts", pid), column_config={"id": None}, num_rows="dynamic", use_container_width=True, key=f"ed_con_{pid}")

        with t2:
            st.markdown("##### AJOUTER UN ÉCHANTILLON")
            cs1, cs2, cs3 = st.columns([2, 1.2, 0.8])
            with cs1: s_ref = st.text_input("Ref", key=f"sr_{pid}", label_visibility="collapsed", placeholder="Ref (ex: Lot A12)")
            with cs2: s_prod = st.selectbox("Produit", prod_opts, key=f"sp_{pid}", label_visibility="collapsed")
            with cs3: 
                if st.button("Ajouter", type="primary", key=f"sb_{pid}", use_container_width=True):
                    supabase.table("samples").insert({"prospect_id": pid, "reference": s_ref, "product_name": s_prod, "status": "En test", "date_sent": datetime.now().isoformat()}).execute()
                    st.rerun()

            st.markdown("---")
            st.markdown("##### HISTORIQUE DES ENVOIS")
            all_samples = get_sub_data("samples", pid)
            for _, r in all_samples.iterrows():
                with st.container(border=True):
                    ch1, ch2, ch3 = st.columns([3.5, 1.5, 0.5])
                    with ch1: st.markdown(f"**{r['product_name']}** {r['reference']} <span style='color:#94a3b8; font-size:12px;'>({r['date_sent'][:10]})</span>", unsafe_allow_html=True)
                    with ch2:
                        s_opts = ["En test", "Validé", "Rejeté", "En attente"]
                        curr_s = r['status']
                        new_s = st.selectbox("Status", s_opts, index=s_opts.index(curr_s) if curr_s in s_opts else 0, key=f"stat_{r['id']}", label_visibility="collapsed")
                        if new_s != curr_s: supabase.table("samples").update({"status": new_s}).eq("id", r['id']).execute()
                    with ch3:
                        st.markdown('<div class="trash-container">', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_{r['id']}"): supabase.table("samples").delete().eq("id", r['id']).execute(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    new_f = st.text_area("Feedback R&D client...", value=r.get("feedback", ""), key=f"feed_{r['id']}", height=70, placeholder="Feedback R&D client...", label_visibility="collapsed")
                    if new_f != r.get("feedback", ""): supabase.table("samples").update({"feedback": new_f}).eq("id", r['id']).execute()

        with t3:
            st.markdown("##### JOURNAL DES ACTIONS")
            note_content = st.text_area("Ajouter une note d'activité...", key=f"new_note_{pid}")
            if st.button("Enregistrer l'action", key=f"btn_note_{pid}"):
                supabase.table("activities").insert({"prospect_id": pid, "type": "Note", "content": note_content, "date": datetime.now().isoformat()}).execute()
                st.rerun()
            for _, act in get_sub_data("activities", pid).iterrows():
                st.caption(f"🗓️ {act['date'][:10]} — {act['type']}")
                st.write(act['content'])

    st.markdown("---")
    if st.button("Enregistrer & Fermer la Fiche", type="primary", use_container_width=True):
        try:
            # 1. Update Prospect
            upd = {"company_name": name, "status": stat, "country": pays, "potential_volume": float(vol), "last_action_date": last_c_date.isoformat(), "product_interest": prod, "segment": app, "notes": pain, "tech_notes": tech}
            supabase.table("prospects").update(upd).eq("id", pid).execute()
            
            # 2. Sync Contacts (Deletions + Upserts)
            if not contacts_df.empty:
                current_ids = contacts_df['id'].dropna().astype(int).tolist() if 'id' in contacts_df.columns else []
                old_cons = get_sub_data("contacts", pid)
                if not old_cons.empty:
                    to_del = [oid for oid in old_cons['id'].tolist() if oid not in current_ids]
                    if to_del: supabase.table("contacts").delete().in_("id", to_del).execute()
                for rc in contacts_df.to_dict('records'):
                    if str(rc.get("name")).strip():
                        c_payload = {"prospect_id": pid, "name": rc["name"], "role": rc.get("role",""), "email": rc.get("email",""), "phone": rc.get("phone","")}
                        if rc.get("id") and not pd.isna(rc.get("id")): supabase.table("contacts").upsert({**c_payload, "id": int(rc["id"])}).execute()
                        else: supabase.table("contacts").insert(c_payload).execute()
            
            reset_pipeline(); st.rerun()
        except Exception as e: st.error(f"Erreur technique : {e}")

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("favicon.png", width=55)
    st.write("")
    if st.button("⊕ Nouveau Projet"):
        res = supabase.table("prospects").insert({"company_name": "Nouveau Prospect", "status": "Prospection"}).execute()
        st.session_state['open_new_id'] = res.data[0]['id']; st.rerun()
    st.write("")
    
    rc_count = count_relances()
    nav = {
        "Tableau de Bord": "❒ Dashboard", 
        "Pipeline": "☰ Pipeline", 
        "Kanban": "▦ Kanban", 
        "Échantillons": "🧪 Samples", 
        "Contacts": "👤 Contacts",
        "Alertes": "🔔 Alerts"
    }
    sel = st.radio("Navigation", list(nav.keys()), format_func=lambda x: nav[x], label_visibility="collapsed", index=1)
    
    if rc_count > 0:
         st.markdown(f"""<style>div[role="radiogroup"] label:nth-child(6)::after {{content: '{rc_count}'; background: #fee2e2; color: #ef4444; display: inline-block; font-size: 10px; font-weight: 700; padding: 1px 7px; border-radius: 10px; margin-left: auto;}}</style>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("👤 Daria Growth • Ingood")

# --- 6. ROUTING LOGIC ---
if 'open_new_id' in st.session_state:
    st.session_state['active_prospect_id'] = st.session_state.pop('open_new_id'); reset_pipeline()
if 'active_prospect_id' in st.session_state:
    try: 
        row = supabase.table("prospects").select("*").eq("id", st.session_state['active_prospect_id']).execute().data[0]
        show_prospect_card(st.session_state['active_prospect_id'], row)
    except: safe_del('active_prospect_id')

# --- 7. PAGES ---

if sel == "Pipeline":
    df_raw = get_data()
    # Фильтры
    with st.container(border=True):
        f1, f2, f3, f4 = st.columns(4)
        with f1: p_f = st.selectbox("Produit", ["Produit: Tous"] + sorted(list(df_raw['product_interest'].dropna().unique())), label_visibility="collapsed")
        with f2: s_f = st.selectbox("Statut", ["Statut: Tous", "Prospection", "Qualification", "Echantillon", "Test R&D", "Client signé"], label_visibility="collapsed")
        with f3: py_f = st.selectbox("Pays", ["Pays: Tous"] + sorted(list(df_raw['country'].dropna().unique())), label_visibility="collapsed")
        with f4: st.markdown('<div class="filter-label-white" style="text-align:right; padding-top:8px;">▽ Filtres actifs</div>', unsafe_allow_html=True)

    df = df_raw.copy()
    if p_f != "Produit: Tous": df = df[df['product_interest'] == p_f]
    if s_f != "Statut: Tous": df = df[df['status'].str.contains(s_f, na=False)]
    if py_f != "Pays: Tous": df = df[df['country'] == py_f]
    
    st.write("")
    # Шапка
    w = [3.5, 1.2, 1.2, 1.8, 1.8, 2.2, 1.8]
    st.markdown('<div class="pipeline-header-row">', unsafe_allow_html=True)
    h_cols = st.columns(w)
    labels = ["SOCIÉTÉ", "PAYS", "PRODUIT", "STATUT", "CONTACT", "SOURCE", "SAMPLES"]
    for i, l in enumerate(labels): h_cols[i].markdown(f'<span class="header-text-style">{l}</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    samples_map = pd.DataFrame(supabase.table("samples").select("prospect_id").execute().data)
    for _, row in df.iterrows():
        with st.container(border=True):
            r = st.columns(w)
            if r[0].button(row['company_name'], key=f"btn_{row['id']}"):
                st.session_state['active_prospect_id'] = row['id']; st.rerun()
            r[1].markdown(f"<span class='text-small-muted'>{row['country'] or '-'}</span>", unsafe_allow_html=True)
            r[2].markdown(f"<span style='color:#047857; font-weight:700; font-size:13px;'>{row['product_interest'] or '-'}</span>", unsafe_allow_html=True)
            st_val = row['status'] or "Prospection"
            b_cls = "bg-green" if "Client" in st_val else "bg-yellow" if "Test" in st_val else "bg-gray"
            r[3].markdown(f"<span class='badge-ui {b_cls}'>{st_val}</span>", unsafe_allow_html=True)
            if row['last_action_date']:
                dt = datetime.strptime(row['last_action_date'][:10], "%Y-%m-%d")
                color = "#ef4444" if (datetime.now() - dt).days > 30 else "#64748b"
                r[4].markdown(f"<span style='color:{color}; font-weight:700; font-size:13px;'>{dt.strftime('%d %b %y')}</span>", unsafe_allow_html=True)
            else: r[4].write("-")
            r[5].markdown(f"<span class='text-small-muted'>{row.get('last_salon') or '-'}</span>", unsafe_allow_html=True)
            has_s = not samples_map.empty and row['id'] in samples_map['prospect_id'].values
            if has_s: r[6].markdown("<span class='badge-ui bg-blue'>🧪 En test</span>", unsafe_allow_html=True)
            else: r[6].write("-")

elif sel == "Kanban":
    st.title("Board Commercial ▦")
    df = get_data()
    stages = ["Prospection", "Qualification", "Echantillon", "Test R&D", "Négociation", "Client signé"]
    cols = st.columns(len(stages))
    for i, s_name in enumerate(stages):
        with cols[i]:
            st.markdown(f"<p style='font-weight:800; color:#047857; font-size:12px; border-bottom:3px solid #047857; padding-bottom:5px;'>{s_name.upper()}</p>", unsafe_allow_html=True)
            mask = df['status'].str.contains(s_name, na=False)
            for _, row in df[mask].iterrows():
                with st.container():
                    st.markdown(f"""<div class='kanban-card'>
                        <div style='font-weight:700; color:#1e293b;'>{row['company_name']}</div>
                        <div style='font-size:11px; color:#64748b; margin: 4px 0;'>🌍 {row['country'] or 'N/A'}</div>
                        <div style='font-size:11px; font-weight:600; color:#047857;'>📦 {row['product_interest'] or 'N/A'}</div>
                    </div>""", unsafe_allow_html=True)
                    if st.button("Ouvrir", key=f"kb_btn_{row['id']}", use_container_width=True):
                        st.session_state['active_prospect_id'] = row['id']; st.rerun()

elif sel == "Tableau de Bord":
    st.title("Analytics Growth ❒")
    df = get_data()
    if not df.empty:
        c1, c2, c3, f4 = st.columns(4)
        c1.metric("Projets Actifs", len(df))
        c2.metric("Potentiel Total (T)", f"{int(df['potential_volume'].sum())} T")
        c3.metric("Taux de Conversion", f"{int(len(df[df['status']=='Client signé'])/len(df)*100)}%")
        f4.metric("Échantillons en R&D", len(df[df['status'].str.contains('Test', na=False)]))
        
        col_a, col_b = st.columns(2)
        with col_a:
            fig1 = px.pie(df, names='product_interest', hole=.4, title="Mix Produits Strategique", color_discrete_sequence=px.colors.sequential.Greens_r)
            st.plotly_chart(fig1, use_container_width=True)
        with col_b:
            # Tunnel de vente
            status_counts = df['status'].value_counts().reindex(stages).fillna(0)
            fig2 = px.bar(status_counts, title="Tunnel de Vente (Pipeline)", color_discrete_sequence=['#047857'])
            st.plotly_chart(fig2, use_container_width=True)

elif sel == "Contacts":
    st.title("Annuaire Global 👤")
    search = st.text_input("🔍 Rechercher un contact...", placeholder="Nom, Entreprise, Email...")
    cons = pd.DataFrame(supabase.table("contacts").select("*, prospects(company_name)").execute().data)
    if not cons.empty:
        # Улучшенное отображение через dataframe с фильтрацией
        cons['Entreprise'] = cons['prospects'].apply(lambda x: x['company_name'] if x else 'N/A')
        display_df = cons[['name', 'role', 'email', 'phone', 'Entreprise']]
        if search: display_df = display_df[display_df.apply(lambda r: search.lower() in r.astype(str).str.lower().values, axis=1)]
        st.dataframe(display_df, use_container_width=True, height=600)
    else: st.info("Aucun contact enregistré.")

elif sel == "Échantillons":
    st.title("Gestion des Échantillons 🧪")
    samp = pd.DataFrame(supabase.table("samples").select("*, prospects(company_name)").execute().data)
    if not samp.empty:
        samp['Client'] = samp['prospects'].apply(lambda x: x['company_name'] if x else 'N/A')
        st.dataframe(samp[['date_sent', 'product_name', 'reference', 'status', 'Client', 'feedback']], use_container_width=True)
    else: st.info("Aucun envoi d'échantillon répertorié.")

elif sel == "Alertes":
    st.title("Relances Prioritaires 🔔")
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    # Находим образцы без фидбека дольше 15 дней
    alerts = pd.DataFrame(supabase.table("samples").select("*, prospects(company_name)").is_("feedback", "null").lte("date_sent", fifteen_days_ago).execute().data)
    if not alerts.empty:
        st.warning(f"Vous avez {len(alerts)} relances en attente depuis plus de 15 jours.")
        alerts['Client'] = alerts['prospects'].apply(lambda x: x['company_name'] if x else 'N/A')
        for _, al in alerts.iterrows():
            with st.container(border=True):
                a1, a2 = st.columns([4, 1])
                a1.markdown(f"**{al['Client']}** — {al['product_name']} ({al['reference']}) envoyé le {al['date_sent'][:10]}")
                if a2.button("Ouvrir Fiche", key=f"al_{al['id']}"):
                    st.session_state['active_prospect_id'] = al['prospect_id']; st.rerun()
    else: st.success("Félicitations ! Toutes vos relances sont à jour.")
