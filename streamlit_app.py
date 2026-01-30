import streamlit as st
import pandas as pd
import streamlit_shadcn_ui as ui
from supabase import create_client
import google.generativeai as genai
from datetime import datetime, timedelta
import plotly.express as px
import time

# --- 1. НАСТРОЙКИ И ИНИЦИАЛИЗАЦИЯ ---
st.set_page_config(page_title="Ingood Growth AI", page_icon="🧬", layout="wide")

# Подключение к базе и AI
@st.cache_resource
def init_connections():
    try:
        supa = create_client(st.secrets, st.secrets)
        genai.configure(api_key=st.secrets)
        return supa
    except Exception as e:
        st.error(f"Ошибка подключения: {e}")
        return None

supabase = init_connections()

# --- 2. AI ФУНКЦИИ (GEMINI + GROUNDING) ---

def ai_company_research(query):
    """Агент поиска новых клиентов через Gemini с доступом в Google"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    tools = 'google_search_retrieval' # Включаем поиск Google
    
    prompt = f"""
    Ты - эксперт по развитию бизнеса в пищевой индустрии.
    Твоя задача: Найти 5 потенциальных B2B клиентов по запросу: "{query}".
    Для каждой компании найди:
    1. Название
    2. Сайт
    3. Тип продукции (кратко)
    4. Почему они нам подходят (Reason to Believe)
    
    Верни ответ строго в формате JSON списка.
    """
    try:
        response = model.generate_content(prompt, tools=tools)
        return response.text
    except Exception as e:
        return f"Ошибка AI: {e}"

def ai_draft_email(company_name, product_interest, contact_name="Коллега"):
    """Генерация письма"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Напиши короткое, профессиональное холодное письмо для {contact_name} из компании {company_name}.
    Мы предлагаем пищевой ингредиент: {product_interest}.
    Сделай упор на инновации и качество. Не более 150 слов. Язык: Французский (или английский, если компания международная).
    """
    response = model.generate_content(prompt)
    return response.text

# --- 3. UI КОМПОНЕНТЫ ---

def show_kpi_metrics(df):
    """Красивые метрики сверху"""
    cols = st.columns(4)
    with cols:
        ui.metric_card(title="Всего Проектов", content=str(len(df)), description="Активные лиды", key="m1")
    with cols[1]:
        vol = int(df['potential_volume'].sum()) if 'potential_volume' in df.columns else 0
        ui.metric_card(title="Потенциал (Тонн)", content=f"{vol} T", description="Общий объем", key="m2")
    with cols[2]:
        # Считаем образцы в пути
        samples = supabase.table("samples").select("*", count="exact").eq("status", "Shipped").execute()
        ui.metric_card(title="Образцы в пути", content=str(samples.count), description="Ждем фидбек", key="m3")
    with cols[3]:
        ui.metric_card(title="AI Агент", content="Активен", description="Perplexity Monitor", key="m4")

def show_prospect_modal(row):
    """Детальная карточка клиента"""
    st.markdown(f"### 🏢 {row['company_name']}")
    
    tabs = ui.tabs(options=["Детали", "Контакты", "Образцы", "AI Письмо"], default_value="Детали", key=f"tab_{row['id']}")
    
    if tabs == "Детали":
        c1, c2 = st.columns(2)
        with c1:
            new_status = st.selectbox("Статус",, index=0, key=f"s_{row['id']}")
            st.text_area("Заметки", value=row.get('notes', ''), key=f"n_{row['id']}")
        with c2:
            st.text_input("Продукт", value=row.get('product_interest', ''), key=f"p_{row['id']}")
            st.number_input("Объем (Т)", value=row.get('potential_volume', 0.0), key=f"v_{row['id']}")
            
        if st.button("💾 Сохранить изменения", key=f"save_{row['id']}"):
            supabase.table("prospects").update({"status": new_status}).eq("id", row['id']).execute()
            st.rerun()

    elif tabs == "AI Письмо":
        st.info("Генерация персонализированного письма через Gemini")
        if st.button("✨ Написать письмо", key=f"ai_btn_{row['id']}"):
            draft = ai_draft_email(row['company_name'], row.get('product_interest', 'Ingredients'))
            st.text_area("Черновик", value=draft, height=200)

    elif tabs == "Образцы":
        # Загрузка образцов
        samples = supabase.table("samples").select("*").eq("prospect_id", row['id']).execute().data
        if samples:
            st.dataframe(pd.DataFrame(samples)[['date_sent', 'product_name', 'status', 'tracking_number']])
        
        with st.expander("Отправить новый образец"):
            s_name = st.text_input("Продукт", key=f"sn_{row['id']}")
            s_track = st.text_input("Трек-номер", key=f"st_{row['id']}")
            if st.button("Добавить", key=f"add_s_{row['id']}"):
                supabase.table("samples").insert({
                    "prospect_id": row['id'], 
                    "product_name": s_name,
                    "tracking_number": s_track,
                    "status": "Shipped"
                }).execute()
                st.rerun()

# --- 4. ГЛАВНАЯ ЛОГИКА ---

def main():
    # Боковое меню
    with st.sidebar:
        st.title("🧬 Ingood Growth")
        menu = ui.tabs(options=["Pipeline", "AI Поиск", "Образцы"], default_value="Pipeline", key="main_nav")
        st.divider()
        if st.button("➕ Новый Лид", use_container_width=True):
            supabase.table("prospects").insert({"company_name": "Новая Компания", "status": "Prospection"}).execute()
            st.rerun()

    # СТРАНИЦА 1: PIPELINE
    if menu == "Pipeline":
        df_data = supabase.table("prospects").select("*").order("created_at", desc=True).execute().data
        df = pd.DataFrame(df_data)
        
        if not df.empty:
            show_kpi_metrics(df)
            st.divider()
            
            # Фильтры
            status_filter = st.multiselect("Фильтр по статусу", options=df['status'].unique(), default=df['status'].unique())
            df_filtered = df[df['status'].isin(status_filter)]

            # Отображение списка (Shadcn Cards)
            for _, row in df_filtered.iterrows():
                with ui.card(key=f"card_{row['id']}"):
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.markdown(f"**{row['company_name']}**")
                    c1.caption(f"🌍 {row.get('country', '-')} | 📦 {row.get('product_interest', '-')}")
                    c2.markdown(f"Статус: `{row['status']}`")
                    if c3.button("Открыть", key=f"open_{row['id']}", use_container_width=True):
                        show_prospect_card(row)

    # СТРАНИЦА 2: AI ПОИСК (PROSPECTING)
    elif menu == "AI Поиск":
        st.header("🕵️‍♂️ AI Market Hunter")
        st.caption("Поиск новых клиентов с помощью Gemini + Google Search")
        
        query = st.text_input("Кого ищем?", placeholder="Например: Производители веганского мороженого во Франции")
        if st.button("Начать поиск 🚀"):
            with st.spinner("Анализирую рынок..."):
                result = ai_company_research(query)
                st.markdown(result)
                st.success("Анализ завершен! Скопируйте данные для добавления в базу.")

    # СТРАНИЦА 3: ОБРАЗЦЫ
    elif menu == "Образцы":
        st.header("🧪 Управление Образцами")
        samples = supabase.table("samples").select("*, prospects(company_name)").execute().data
        if samples:
            df_s = pd.DataFrame(samples)
            # Выравниваем данные (flatten)
            df_s['Client'] = df_s['prospects'].apply(lambda x: x['company_name'] if x else '-')
            st.data_editor(
                df_s[['date_sent', 'Client', 'product_name', 'status', 'feedback_text']],
                key="samples_editor",
                num_rows="dynamic"
            )

if __name__ == "__main__":
    main()
