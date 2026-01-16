import streamlit as st
import google.generativeai as genai
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- 試算表設定 ---
# 這是你提供的 Google Sheets 網址
SHEET_URL = "https://docs.google.com/spreadsheets/d/16niyheTwWVts9A6aKRiOx2OpJypQAIeodE08TN9cERU/edit?usp=sharing"

# --- 介面設定 (移除隱私名稱) ---
st.set_page_config(page_title="AI 全能運動教練", layout="wide")
st.title("🏃‍♂️ 跑步生理數據與 $VO_2 Max$ 永久分析系統")

# --- 欄位記憶功能 ---
if 'weight' not in st.session_state: st.session_state.weight = 80.0
if 'max_hr' not in st.session_state: st.session_state.max_hr = 190
if 'rest_hr' not in st.session_state: st.session_state.rest_hr = 55

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")

tab1, tab2 = st.tabs(["數據推算", "永久趨勢分析"])

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

            raw_data = st.text_area("請貼上 Lap 數據", height=150)

            if st.button("開始 AI 數據分析"):
                with st.spinner("AI 正在根據生理指標計算中..."):
                    prompt = f"你是教練。分析生理指標：體重{st.session_state.weight}, MHR:{st.session_state.max_hr}, RHR:{st.session_state.rest_hr}。數據：{raw_data}"
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                
                st.divider()
                final_vo2 = st.number_input("請確認推算出的 VO2 Max 數字", value=42.0, step=0.1)
                
                if st.button("確認存入 Google Sheets"):
                    # 讀取現有數據
                    existing_data = conn.read(spreadsheet=SHEET_URL, usecols=[0,1,2])
                    new_entry = pd.DataFrame([[str(run_date), final_vo2, run_type]], columns=["日期", "VO2_Max", "類型"])
                    updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                    
                    # 寫回試算表
                    conn.update(spreadsheet=SHEET_URL, data=updated_df)
                    st.success("🎉 數據已成功同步至 Google Sheets！這份紀錄將永久保存。")
                    
        except Exception as e:
            st.error(f"系統錯誤：{e}")
    else:
        st.info("請輸入 API Key 以開始使用。")

with tab2:
    st.header("📈 $VO_2 Max$ 永久成長曲線")
    try:
        # 直接從 Google Sheets 讀取最新數據
        df = conn.read(spreadsheet=SHEET_URL)
        if not df.empty:
            df = df.sort_values("日期")
            st.line_chart(df.set_index("日期")["VO2_Max"])
            st.dataframe(df, use_container_width=True)
        else:
            st.write("試算表目前是空的，快去推算第一筆數據吧！")
    except:
        st.write("目前連線不到試算表，請確認網址與權限。")
