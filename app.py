import streamlit as st
import google.generativeai as genai
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- 試算表設定 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/16niyheTwWVts9A6aKRiOx2OpJyp (Your URL ID) ..." # 系統會自動抓取你之前提供的網址

# --- 介面設定 ---
st.set_page_config(page_title="AI 全能運動教練", layout="wide")
st.title("🚀 AI 運動表現分析與進步預測系統")

# --- 欄位記憶功能 ---
if 'weight' not in st.session_state: st.session_state.weight = 80.0
if 'max_hr' not in st.session_state: st.session_state.max_hr = 190
if 'rest_hr' not in st.session_state: st.session_state.rest_hr = 55

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")

tab1, tab2 = st.tabs(["數據推算與分析", "長期趨勢與預測"])

with tab1:
    if api_key:
        # 第一層 Try: 確保 API 連線正常
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 生理與技術指標")
                st.session_state.weight = st.number_input("體重 (kg)", value=st.session_state.weight)
                st.session_state.max_hr = st.number_input("最大心率 (bpm)", value=st.session_state.max_hr)
                st.session_state.rest_hr = st.number_input("安靜心率 (bpm)", value=st.session_state.rest_hr)
                gct = st.number_input("觸地時間 (ms)", value=200)
                v_osc = st.number_input("垂直振幅 (cm)", value=8.0)
            
            with col2:
                st.subheader("📅 訓練內容")
                run_date = st.date_input("訓練日期", datetime.date.today())
                run_type = st.selectbox("訓練類型", ["間歇跑 (Interval)", "穩定跑 (E/M/T)"])
                raw_data = st.text_area("請貼上 Lap 數據", height=150)

            # --- AI 分析區 ---
            if st.button("啟動 AI 深度分析"):
                with st.spinner("AI 教練正在交叉比對數據..."):
                    prompt = f"分析：體重{st.session_state.weight}kg, MHR:{st.session_state.max_hr}, RHR:{st.session_state.rest_hr}, GCT:{gct}ms, 垂直振幅:{v_osc}cm。數據：{raw_data}"
                    response = model.generate_content(prompt)
                    st.session_state.last_analysis = response.text
                
            if 'last_analysis' in st.session_state:
                st.markdown(st.session_state.last_analysis)
                st.divider()
                st.subheader("💾 數據永存區")
                final_vo2 = st.number_input("確認本次推算的 VO2 Max", value=42.0, step=0.1)
                
                if st.button("確認存入 Google Sheets"):
                    # 第二層 Try: 專門處理存檔
                    try:
                        existing_data = conn.read(spreadsheet=SHEET_URL)
                        new_entry = pd.DataFrame({
                            "日期": [str(run_date)],
                            "VO2_Max": [final_vo2],
                            "類型": [run_type],
                            "GCT": [gct],
                            "垂直振幅": [v_osc]
                        })
                        updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, data=updated_df)
                        st.success("✅ 數據已成功存入雲端試算表！")
