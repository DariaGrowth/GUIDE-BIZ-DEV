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
st.set_page_config(page_title="Ingood Growth AI", page_icon="🧬", layout="wide")

# Профессиональный CSS для премиального интерфейса (белый фон, зеленые акценты Ingood)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* Общие настройки страницы */
        .stApp { background-color: #ffffff !important; font-family: 'Inter', sans-serif; }
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        [data-testid="stVerticalBlock"] { gap: 0rem !important; }
        
        /* Кнопка "Nouveau Projet" в сайдбаре */
        [data-testid="stSidebar"] .stButton > button {
            width: 100%; background-color: #047857 !important; color: white !important;
            border: none; border-radius: 6px; padding: 10px 16px; font-weight: 600;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1); transition: all 0.2s;
        }
        [data-testid="stSidebar"] .stButton > button:hover { background-color: #065f46 !important; transform: translateY(-1px); }

        /* Контейнер фильтров в Pipeline */
        div[data-testid="stVerticalBlock"] > div:nth-child(1) > div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #047857 !important; border: none !important; border-radius: 8px !important;
            padding: 12px 20px !important; margin-bottom: 15px !important;
        }
        .filter-label-white { color: #ffffff !important; font-weight: 700; font-size: 14px; }

        /* Оформление строк таблицы Pipeline */
        .pipeline-header-row {
            padding: 12px 15px 8px 15px; margin-bottom: 5px; display: flex; align-items: center;
        }
        .header-text-style { 
            color: #047857 !important; font-size: 14px !important; font-weight: 800 !important; 
            text-transform: uppercase; letter-spacing: 0.5px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important; border: none !important;
            border-bottom: 1px solid #f1f5f9 !important; border-radius: 0px !important;
            padding: 2px 15px !important; margin-bottom: 0px !important;
        }
        
        /* Стилизация названий компаний как ссылок */
        div[data-testid="column"]:first-child .stButton > button {
            background: transparent !important; border: none !important; padding: 0 !important;
            margin: 0 !important; color: #047857 !important; font-weight: 800 !important;
            font-size: 15px !important; text-align: left !important; box-shadow: none !important;
            min-height: 0px !important; height: 32px !important; line-height: 32px !important;
            display: inline-block !important; width: auto !important;
        }
        div[data-testid="column"]:first-child .stButton > button:hover { text-decoration: underline !important; color: #065f46 !important; }

        /* ИДЕАЛЬНОЕ ВЫРАВНИВАНИЕ МУСОРКИ (Метод центрирования 38px) */
        .trash-container { 
            display: flex; align-items: center; justify-content: center; height: 38px; 
        }
        .trash-container button {
            background: transparent !important; border: none !important; box-shadow: none !important;
            color: #94a3b8 !important; padding: 0 !important; font-size: 18px !important;
            width: 32px !important; height: 32px !important; margin-top: 0px !important;
        }
        .trash-container button:hover { color: #ef4444 !important; background: #fee2e2 !important; border-radius: 4px !important; }

        /* Бейджи статусов */
        .badge-ui { padding: 2px 10px; border-radius: 10px; font-size: 10px; font-weight: 700; display: inline-block; }
        .bg-yellow { background: #fef9c3; color: #854d0e; }
        .bg-gray { background: #f1f5f9; color: #64748b; }
        .bg-green { background: #dcfce7; color: #166534; }
        .bg-blue { background: #eff6ff; color: #1d4ed8; border: 1px solid #dbeafe; }

        /* Заголовки полей в форме */
        .contact-label { font-size: 11px; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin-bottom: 5px; display: block; }
        .field-label { font-size: 11px !important; font-weight: 700 !important; color: #64748b !important; text-transform: uppercase; margin-bottom: 4px; }

        /* Оформление карточек Kanban */
        .kanban-card { 
            background: white; border: 1px solid #e2e8f0; border-radius: 8px; 
            padding: 12px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); 
        }
        .kanban-card:hover { border-color: #047857; }
        .kanban-potential { font-size: 11px; font-weight: 800; color: #047857; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNECTIONS ---
@st.cache_resource
def init_connections():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key), genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Erreur de connexion: {e}")
        return None, None

supabase, _ = init_connections()
if not supabase: st.stop()

# --- 3. AI CORE (GROUNDING & RESEARCH) ---
def ai_generate_smart_email(company, product, tone, country):
    """Использует Gemini 1.5 Flash с инструментами поиска Google для генерации контекстного письма"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Rôle : Manager commercial technique pour Ingood Growth (ingrédients alimentaires innovants).
    Cible : Entreprise {company} située en {country}.
    Produit d'intérêt : {product}.
    Ton souhaité : {tone}.

    Instructions :
    1. Utilise la recherche Google pour trouver des informations récentes sur {company} (nouveaux produits, rapports financiers, engagements RSE).
    2. Rédige un email de prospection personnalisé et percutant en français.
    3. Fais le lien entre leurs besoins actuels et les avantages techniques de {product}.
    4. Garde l'email sous les 150 mots.
    """
    try:
        # Включаем инструмент Google Search для актуализации данных
        response = model.generate_content(prompt, tools=[{ "google_search": {} }])
        return response.text
    except Exception as e:
        # Запасной вариант без поиска, если сервис недоступен
        res_fallback = model.generate_content(prompt)
        return res_fallback.text

# --- 4. DATA HELPERS ---
if 'pipeline_key' not in st.session_state: st.session_state['pipeline_key'] = 0

def reset_pipeline(): 
    """Сбрасывает состояние сессии для обновления данных"""
    st.session_state['pipeline_key'] += 1
    st.cache_data.clear()
    safe_del('active_prospect_id')
    safe_del('ai_draft')
    if 'editing_contacts' in st.session_state: del st.session_state['editing_contacts']

def safe_del(key): 
    if key in st.session_state: del st.session_state[key]

def clean_prod_name(name):
    """Очищает название продукта от пояснений в скобках для компактности UI"""
    if not name or name == "-" or str(name) == "nan": return "-"
    return str(name).split(' (')[0].split('(')[0].strip()

@st.cache_data(ttl=60)
def get_data(): 
    """Загружает основной список проспектов"""
    try:
        res = supabase.table("prospects").select("*").order("last_action_date", desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def get_sub_data(t, pid):
    """Загружает связанные данные (контакты, образцы) для конкретного проспекта"""
    try:
        d = supabase.table(t).select("*").eq("prospect_id", pid).order("id", desc=True).execute().data
        return pd.DataFrame(d)
    except: return pd.DataFrame()

def count_relances():
    """Считает количество активных алертов (образцы без фидбека > 15 дней)"""
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    try:
        res = supabase.table("samples").select("id", count="exact").is_("feedback", "null").lte("date_sent", fifteen_days_ago).execute()
        return res.count if res.count else 0
    except: return 0

# --- 5. MODAL: FICHE PROSPECT (ПОЛНАЯ ЛОГИКА) ---
@st.dialog(" ", width="large")
def show_prospect_card(pid, data):
    pid = int(pid)
    st.markdown(f"<h2 style='margin-top: -30px; margin-bottom: 25px; font-size: 24px; color: #1e293b; font-weight: 800; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px;'>{data['company_name']}</h2>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 2], gap="large")

    # ЛЕВАЯ КОЛОНКА: ОСНОВНАЯ ИНФО И ИИ
    with c_left:
        with st.container(border=True):
            name = st.text_input("SOCIÉTÉ / CLIENT", value=data['company_name'], key=f"n_{pid}")
            opts = ["Prospection", "Qualification", "Echantillon", "Test R&D", "Essai industriel", "Négociation", "Client signé"]
            stat = st.selectbox("STATUT PIPELINE", opts, index=next((i for i, s in enumerate(opts) if s in data.get("status", "")), 0))
            
            cl1, cl2 = st.columns(2)
            with cl1: pays = st.text_input("PAYS", value=data.get("country", ""))
            with cl2: vol = st.number_input("POTENTIEL (T)", value=float(data.get("potential_volume") or 0))
            
            web_url = st.text_input("SITE WEB (URL)", value=data.get("website_url", ""), placeholder="https://...")
            
            last_c_str = data.get("last_action_date") or datetime.now().strftime("%Y-%m-%d")
            try: last_c_date = st.date_input("DERNIER CONTACT", value=datetime.strptime(last_c_str[:10], "%Y-%m-%d"))
            except: last_c_date = st.date_input("DERNIER CONTACT", value=datetime.now())
            
            st.markdown("---")
            st.markdown("<p class='field-label'>🪄 AI SMART RESEARCH & EMAIL</p>", unsafe_allow_html=True)
            tone = st.selectbox("Ton du message", ["Professionnel", "Amical / Relance", "Urgent / Technique"], key=f"ai_tone_{pid}")
            if st.button("✨ Rechercher & Rédiger", use_container_width=True):
                with st.spinner("Analyse du web et rédaction en cours..."):
                    res = ai_generate_smart_email(data['company_name'], data.get('product_interest'), tone, data.get('country'))
                    st.session_state['ai_draft'] = res
            if 'ai_draft' in st.session_state:
                st.text_area("Черновик на основе новостей", value=st.session_state['ai_draft'], height=200)

    # ПРАВАЯ КОЛОНКА: ТАБЫ (ДЕТАЛИ, КОНТАКТЫ, ОБРАЗЦЫ)
    with c_right:
        t1, t2, t3 = st.tabs(["Contexte & Техника", "Suivi Échantillons", "Journal d'Activité"])
        
        with t1:
            prod_opts = ["LENGOOD® (Substitut Œuf)", "PEPTIPEA® (Protéine)", "NEWGOOD® (Nouveauté)"]
            app_opts = ["Boulangerie / Pâtisserie", "Sauces / Mayonnaise", "Confiserie", "Plats cuisinés", "Boissons"]
            
            cr1, cr2 = st.columns(2)
            with cr1: prod = st.selectbox("INGRÉDIENT INGOOD", prod_opts, index=prod_opts.index(data.get("product_interest")) if data.get("product_interest") in prod_opts else 0)
            with cr2: app = st.selectbox("APPLICATION FINALE", app_opts, index=app_opts.index(data.get("segment")) if data.get("segment") in app_opts else 0)
            
            pain = st.text_area("PROBLÉMATIQUE / BESOIN", value=data.get("notes", ""), height=70)
            tech = st.text_area("NOTES TECHNIQUES / R&D", value=data.get("tech_notes", ""), height=70)
            
            st.markdown("---")
            # --- УПРАВЛЕНИЕ КОНТАКТАМИ (ИНДИВИДУАЛЬНЫЕ СТРОКИ) ---
            if 'editing_contacts' not in st.session_state:
                st.session_state['editing_contacts'] = get_sub_data("contacts", pid).to_dict('records')

            # Заголовки (всегда видны)
            hc1, hc2, hc3, hc4, hc5 = st.columns([1.2, 1.2, 1.5, 1.2, 0.4])
            hc1.markdown('<span class="contact-label">Nom</span>', unsafe_allow_html=True)
            hc2.markdown('<span class="contact-label">Poste</span>', unsafe_allow_html=True)
            hc3.markdown('<span class="contact-label">Email</span>', unsafe_allow_html=True)
            hc4.markdown('<span class="contact-label">Téléphone</span>', unsafe_allow_html=True)

            for i, c in enumerate(st.session_state['editing_contacts']):
                r1, r2, r3, r4, r5 = st.columns([1.2, 1.2, 1.5, 1.2, 0.4])
                st.session_state['editing_contacts'][i]['name'] = r1.text_input("N", value=c.get('name',''), key=f"c_n_{i}", label_visibility="collapsed")
                st.session_state['editing_contacts'][i]['role'] = r2.text_input("P", value=c.get('role',''), key=f"c_r_{i}", label_visibility="collapsed")
                st.session_state['editing_contacts'][i]['email'] = r3.text_input("E", value=c.get('email',''), key=f"c_e_{i}", label_visibility="collapsed")
                st.session_state['editing_contacts'][i]['phone'] = r4.text_input("T", value=c.get('phone',''), key=f"c_p_{i}", label_visibility="collapsed")
                with r5:
                    st.markdown('<div class="trash-container">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_c_{i}"):
                        if c.get('id'):
                            if 'contacts_to_delete' not in st.session_state: st.session_state['contacts_to_delete'] = []
                            st.session_state['contacts_to_delete'].append(c['id'])
                        st.session_state['editing_contacts'].pop(i); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            if st.button("⊕ Ajouter un contact"):
                st.session_state['editing_contacts'].append({"id": None, "name": "", "email": "", "role": "", "phone": ""})
                st.rerun()

        with t2:
            st.markdown("<p class='field-label'>ENVOYER UN NOUVEL ÉCHANTILLON</p>", unsafe_allow_html=True)
            cs1, cs2, cs3 = st.columns([2, 1.2, 0.8])
            with cs1: s_ref = st.text_input("Référence / Lot", key=f"sr_{pid}", label_visibility="collapsed", placeholder="Ref (ex: A-240)")
            with cs2: s_prod = st.selectbox("Produit", prod_opts, key=f"sp_{pid}", label_visibility="collapsed")
            with cs3: 
                if st.button("Ajouter", type="primary", use_container_width=True):
                    supabase.table("samples").insert({"prospect_id": pid, "reference": s_ref, "product_name": s_prod, "status": "En test", "date_sent": datetime.now().isoformat()}).execute()
                    st.rerun()
            
            st.markdown("---")
            all_s = get_sub_data("samples", pid)
            for _, r in all_s.iterrows():
                with st.container(border=True):
                    ch1, ch2, ch3 = st.columns([3.5, 1.5, 0.5])
                    with ch1: st.markdown(f"**{clean_prod_name(r['product_name'])}** {r['reference']} <span style='color:#94a3b8; font-size:11px;'>({r['date_sent'][:10]})</span>", unsafe_allow_html=True)
                    with ch2:
                        s_opt = ["En test", "Validé", "Rejeté", "En attente"]
                        new_s = st.selectbox("Status", s_opt, index=s_opt.index(r['status']) if r['status'] in s_opt else 0, key=f"st_{r['id']}", label_visibility="collapsed")
                        if new_s != r['status']: supabase.table("samples").update({"status": new_s}).eq("id", r['id']).execute()
                    with ch3:
                        st.markdown('<div class="trash-container" style="height:32px;">', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"ds_{r['id']}"): supabase.table("samples").delete().eq("id", r['id']).execute(); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    new_f = st.text_area("Feedback R&D...", value=r.get("feedback", ""), key=f"f_{r['id']}", height=60, placeholder="Retour client...", label_visibility="collapsed")
                    if new_f != r.get("feedback", ""): supabase.table("samples").update({"feedback": new_f}).eq("id", r['id']).execute()

        with t3:
            st.markdown("<p class='field-label'>LOG DES ACTIONS</p>", unsafe_allow_html=True)
            note_content = st.text_area("Nouvelle note...", key=f"note_{pid}", label_visibility="collapsed", placeholder="Compte rendu d'appel...")
            if st.button("Enregistrer l'action"):
                supabase.table("activities").insert({"prospect_id": pid, "type": "Note", "content": note_content, "date": datetime.now().isoformat()}).execute()
                st.rerun()
            for _, act in get_sub_data("activities", pid).iterrows():
                st.caption(f"🗓️ {act['date'][:10]}")
                st.write(act['content'])

    st.markdown("---")
    if st.button("Enregistrer & Fermer la Fiche", type="primary", use_container_width=True):
        try:
            # 1. Update Prospect
            upd = {"company_name": name, "status": stat, "country": pays, "potential_volume": float(vol), "website_url": web_url, "last_action_date": last_c_date.isoformat(), "product_interest": prod, "segment": app, "notes": pain, "tech_notes": tech}
            supabase.table("prospects").update(upd).eq("id", pid).execute()
            
            # 2. Deletions (Contacts)
            if 'contacts_to_delete' in st.session_state:
                supabase.table("contacts").delete().in_("id", st.session_state.pop('contacts_to_delete')).execute()
            
            # 3. Upserts (Contacts)
            for rc in st.session_state.get('editing_contacts', []):
                if str(rc.get("name")).strip():
                    payload = {"prospect_id": pid, "name": rc["name"], "role": rc.get("role",""), "email": rc.get("email",""), "phone": rc.get("phone","")}
                    if rc.get("id"): supabase.table("contacts").upsert({**payload, "id": int(rc["id"])}).execute()
                    else: supabase.table("contacts").insert(payload).execute()
            reset_pipeline(); st.rerun()
        except Exception as e: st.error(f"Erreur technique: {e}")

# --- 6. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("favicon.png", width=55)
    st.write("")
    if st.button("⊕ Nouveau Projet"):
        res = supabase.table("prospects").insert({"company_name": "Nouveau Prospect", "status": "Prospection"}).execute()
        st.session_state['open_new_id'] = res.data[0]['id']; st.rerun()
    st.write("")
    
    rc_count = count_relances()
    nav_opts = {
        "Tableau de Bord": "❒ Dashboard", 
        "Pipeline": "☰ Pipeline", 
        "Kanban": "▦ Kanban", 
        "Échantillons": "🧪 Samples", 
        "Contacts": "👤 Contacts",
        "Alertes": "🔔 Alerts"
    }
    sel = st.radio("Navigation", list(nav_opts.keys()), format_func=lambda x: nav_opts[x], label_visibility="collapsed", index=1)
    
    if rc_count > 0:
         st.markdown(f"""<style>div[role="radiogroup"] label:nth-child(6)::after {{content: '{rc_count}'; background: #fee2e2; color: #ef4444; display: inline-block; font-size: 10px; font-weight: 700; padding: 1px 7px; border-radius: 10px; margin-left: auto;}}</style>""", unsafe_allow_html=True)
    st.markdown("---"); st.caption("👤 Daria • Ingood Growth")

# --- 7. ROUTING LOGIC ---
if 'open_new_id' in st.session_state:
    st.session_state['active_prospect_id'] = st.session_state.pop('open_new_id'); reset_pipeline()
if 'active_prospect_id' in st.session_state:
    try: 
        row_data = supabase.table("prospects").select("*").eq("id", st.session_state['active_prospect_id']).execute().data[0]
        show_prospect_card(st.session_state['active_prospect_id'], row_data)
    except: safe_del('active_prospect_id')

# --- 8. PAGES ---

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
    # Таблица Pipeline
    w = [3.5, 1.2, 1.2, 1.8, 1.8, 2.2, 1.8]
    st.markdown('<div class="pipeline-header-row">', unsafe_allow_html=True)
    h_c = st.columns(w)
    labels = ["SOCIÉTÉ", "PAYS", "PRODUIT", "STATUT", "CONTACT", "SOURCE", "SAMPLES"]
    for i, l in enumerate(labels): h_c[i].markdown(f'<span class="header-text-style">{l}</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    s_map = pd.DataFrame(supabase.table("samples").select("prospect_id").execute().data)
    for _, row in df.iterrows():
        with st.container(border=True):
            r = st.columns(w)
            if r[0].button(row['company_name'], key=f"b_{row['id']}"):
                st.session_state['active_prospect_id'] = row['id']; st.rerun()
            r[1].markdown(f"<span style='color:#64748b; font-size:13px;'>{row['country'] or '-'}</span>", unsafe_allow_html=True)
            r[2].markdown(f"<span style='color:#047857; font-weight:700; font-size:13px;'>{clean_prod_name(row['product_interest'])}</span>", unsafe_allow_html=True)
            st_v = row['status'] or "Prospection"
            b_c = "bg-green" if "Client" in st_v else "bg-yellow" if "Test" in st_v else "bg-gray"
            r[3].markdown(f"<span class='badge-ui {b_c}'>{st_v}</span>", unsafe_allow_html=True)
            if row['last_action_date']:
                try:
                    dt = datetime.strptime(row['last_action_date'][:10], "%Y-%m-%d")
                    color = "#ef4444" if (datetime.now() - dt).days > 30 else "#64748b"
                    r[4].markdown(f"<span style='color:{color}; font-weight:700; font-size:13px;'>{dt.strftime('%d %b %y')}</span>", unsafe_allow_html=True)
                except: r[4].write("-")
            else: r[4].write("-")
            r[5].markdown(f"<span style='color:#64748b; font-size:13px;'>{row.get('last_salon') or '-'}</span>", unsafe_allow_html=True)
            has_s = not s_map.empty and row['id'] in s_map['prospect_id'].values
            if has_s: r[6].markdown("<span class='badge-ui bg-blue'>🧪 En test</span>", unsafe_allow_html=True)
            else: r[6].write("-")

elif sel == "Kanban":
    st.title("Board Commercial ▦")
    df = get_data()
    stages = ["Prospection", "Qualification", "Echantillon", "Test R&D", "Négociation", "Client signé"]
    cols = st.columns(len(stages))
    for i, s_n in enumerate(stages):
        with cols[i]:
            st.markdown(f"<p style='font-weight:800; color:#047857; font-size:11px; border-bottom:3px solid #047857; padding-bottom:5px;'>{s_n.upper()}</p>", unsafe_allow_html=True)
            mask = df['status'].str.contains(s_n, na=False)
            for _, row in df[mask].iterrows():
                with st.container():
                    st.markdown(f"""<div class='kanban-card'>
                        <div style='font-weight:700; color:#1e293b;'>{row['company_name']}</div>
                        <div style='font-size:10px; color:#64748b;'>🌍 {row['country'] or 'N/A'}</div>
                        <div style='font-size:10px; font-weight:600; color:#047857;'>📦 {clean_prod_name(row['product_interest'])}</div>
                        <div class='kanban-potential'>{int(row.get('potential_volume', 0))} T</div>
                    </div>""", unsafe_allow_html=True)
                    km1, km2, km3 = st.columns([1, 2, 1])
                    with km1:
                        if i > 0 and st.button("←", key=f"prev_{row['id']}"):
                            supabase.table("prospects").update({"status": stages[i-1]}).eq("id", row['id']).execute(); reset_pipeline(); st.rerun()
                    with km2:
                        if st.button("Ouvrir", key=f"kb_{row['id']}", use_container_width=True):
                            st.session_state['active_prospect_id'] = row['id']; st.rerun()
                    with km3:
                        if i < len(stages)-1 and st.button("→", key=f"next_{row['id']}"):
                            supabase.table("prospects").update({"status": stages[i+1]}).eq("id", row['id']).execute(); reset_pipeline(); st.rerun()

elif sel == "Tableau de Bord":
    st.title("Analytics Growth ❒")
    df = get_data()
    if not df.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Projets Actifs", len(df))
        m2.metric("Potentiel (T)", f"{int(df['potential_volume'].sum())} T")
        signed = len(df[df['status']=='Client signé'])
        m3.metric("Win Rate", f"{int(signed/len(df)*100) if len(df)>0 else 0}%")
        m4.metric("Samples en R&D", len(df[df['status'].str.contains('Test', na=False)]))
        
        ca, cb = st.columns(2)
        with ca:
            st.plotly_chart(px.pie(df, names='product_interest', hole=.4, title="Mix Produits (Nombre)", color_discrete_sequence=px.colors.sequential.Greens_r), use_container_width=True)
        with cb:
            # График распределения ТОННАЖА по продуктам
            tonnage_df = df.groupby('product_interest')['potential_volume'].sum().reset_index()
            st.plotly_chart(px.bar(tonnage_df, x='product_interest', y='potential_volume', title="Potentiel Stratégique (Tons)", color_discrete_sequence=['#047857']), use_container_width=True)

elif sel == "Contacts":
    st.title("Annuaire Global 👤")
    search_q = st.text_input("🔍 Rechercher un contact...", placeholder="Nom, Poste, Entreprise...")
    # Загружаем контакты с джойном компании
    cons = pd.DataFrame(supabase.table("contacts").select("*, prospects(company_name)").execute().data)
    if not cons.empty:
        cons['Entreprise'] = cons['prospects'].apply(lambda x: x['company_name'] if x else '-')
        disp = cons[['name', 'role', 'email', 'phone', 'Entreprise']]
        if search_q: disp = disp[disp.apply(lambda r: search_q.lower() in r.astype(str).str.lower().values, axis=1)]
        st.dataframe(disp, use_container_width=True, height=600)
    else: st.info("Aucun contact enregistré.")

elif sel == "Échantillons":
    st.title("Gestion des Échantillons 🧪")
    samp = pd.DataFrame(supabase.table("samples").select("*, prospects(company_name)").execute().data)
    if not samp.empty:
        samp['Client'] = samp['prospects'].apply(lambda x: x['company_name'] if x else '-')
        st.dataframe(samp[['date_sent', 'product_name', 'reference', 'status', 'Client', 'feedback']], use_container_width=True)
    else: st.info("Aucun échantillon envoyé.")

elif sel == "Alertes":
    st.title("Relances Prioritaires 🔔")
    fifteen_days_ago = (datetime.now() - timedelta(days=15)).isoformat()
    al = pd.DataFrame(supabase.table("samples").select("*, prospects(company_name)").is_("feedback", "null").lte("date_sent", fifteen_days_ago).execute().data)
    if not al.empty:
        al['Client'] = al['prospects'].apply(lambda x: x['company_name'] if x else '-')
        for _, alert in al.iterrows():
            with st.container(border=True):
                a1, a2 = st.columns([4, 1])
                a1.markdown(f"🚨 **{alert['Client']}** — {alert['product_name']} envoyé le {alert['date_sent'][:10]}. **Pas de feedback depuis 15+ jours.**")
                if a2.button("Ouvrir Fiche", key=f"al_btn_{alert['id']}"):
                    st.session_state['active_prospect_id'] = alert['prospect_id']; st.rerun()
    else: st.success("Félicitations ! Toutes vos relances sont à jour.")
