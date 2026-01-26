import streamlit as st
from supabase import create_client

st.title("🕵️‍♀️ Проверка Связи")

# 1. Показываем, как приложение видит секреты (скрывая середину)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

st.write(f"**URL:** `{url[:8]}...{url[-5:]}`")
st.write(f"**KEY:** `{key[:5]}...{key[-5:]}`")

if " " in url or " " in key:
    st.error("🚨 ВНИМАНИЕ: Найдены пробелы в URL или Ключе! Проверьте Secrets.")
else:
    st.success("✅ Пробелов нет.")

# 2. Пробуем подключиться
try:
    supabase = create_client(url, key)
    response = supabase.table("prospects").select("*").limit(1).execute()
    st.success("🎉 УРА! База подключена! Данные получены.")
    st.write(response.data)
except Exception as e:
    st.error(f"❌ Ошибка подключения: {e}")
