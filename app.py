import streamlit as st
import google.generativeai as genai
import pandas as pd
import datetime
import os

# --- 設定區域 ---
# 之後我們會把 Google Sheets 的網址填在這裡
SHEET_URL = "" 

# --- 介面設定 (維持隱私) ---
st.set_page_config(page_title="AI 全能運動教練", layout="wide")
st.title("🏃‍♂️ 跑步生理數據與 $VO_2 Max$ 永久分析系統")

# --- 欄位記憶功能 ---
if 'weight' not in st.session_state: st.session_state.weight = 80.0
if 'max_hr' not in st.session_state: st.session_state.max_hr = 190
if 'rest_hr' not in st.session_state: st.session_state.rest_hr = 55
if 'history' not in st.session_state: st.session_state.history = pd.DataFrame(columns=["日期", "VO2_Max", "類型"])

api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")

tab1, tab2 = st.tabs(["數據推算", "趨勢分析"])

with tab1:
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.weight = st.number_input("體重 (kg)", value=st.session_state.weight)
                st.session_state.max_hr = st.number_input("最大心率 (bpm)", value=st.session_state.max_hr)
                st.session_state.rest_hr = st.number_input("安靜心率 (bpm)", value=st.session_state.rest_hr)
            with col2:
                run_date = st.date_input("訓練日期", datetime.date.today())
                run_type = st.selectbox("訓練類型", ["間歇跑 (Interval)", "穩定跑 (E/M/T)"])

            raw_data = st.text_area("貼上 Lap 數據", height=150)

            if st.button("開始 AI 數據分析"):
                with st.spinner("深度學習模型運算中..."):
                    prompt = f"分析生理指標：體重{st.session_state.weight}, MHR:{st.session_state.max_hr}, RHR:{st.session_state.rest_hr}。數據：{raw_data}"
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                
                st.divider()
                final_vo2 = st.number_input("確認推算數字", value=42.0, step=0.1)
                if st.button("確認存入 (本次連線有效)"):
                    new_entry = pd.DataFrame([[str(run_date), final_vo2, run_type]], columns=["日期", "VO2_Max", "類型"])
                    st.session_state.history = pd.concat([st.session_state.history, new_entry], ignore_index=True)
                    st.success("紀錄已暫存！")
                    
        except Exception as e:
            st.error(f"系統錯誤：{e}")
    else:
        st.info("請輸入 API Key 以開始使用。")

with tab2:
    st.header("📈 成長曲線")
    if not st.session_state.history.empty:
        df = st.session_state.history.sort_values("日期")
        st.line_chart(df.set_index("日期")["VO2_Max"])
        st.table(df)
    else:
        st.write("目前暫無數據。")
