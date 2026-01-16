import streamlit as st
import google.generativeai as genai
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- 試算表設定 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/16niyheTwWVts9A6aKRiOx2OpJypQAIeodE08TN9cERU/edit?usp=sharing"

def push_to_sheets(conn, run_date, final_vo2, run_type, gct, v_osc):
    """獨立存檔函數"""
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
        return True, "數據已成功存入 Google Sheets！"
    except Exception as e:
        return False, f"存檔失敗：{e}"

# --- 介面設定 ---
st.set_page_config(page_title="AI 全能運動教練", layout="wide")
st.title("🚀 AI 運動表現分析與進步預測系統")

# --- 狀態記憶 ---
if 'weight' not in st.session_state: st.session_state.weight = 80.0
if 'max_hr' not in st.session_state: st.session_state.max_hr = 190
if 'rest_hr' not in st.session_state: st.session_state.rest_hr = 55
if 'last_analysis' not in st.session_state: st.session_state.last_analysis = ""

conn = st.connection("gsheets", type=GSheetsConnection)
api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")

tab1, tab2 = st.tabs(["數據推算與分析", "長期趨勢與預測"])

with tab1:
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 生理指標")
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

            if st.button("啟動 AI 深度分析"):
                with st.spinner("教練正在閱卷中..."):
                    prompt = f"分析生理與技術指標：體重{st.session_state.weight}, MHR:{st.session_state.max_hr}, RHR:{st.session_state.rest_hr}, GCT:{gct}ms, 垂直振幅:{v_osc}cm。數據內容：{raw_data}"
                    response = model.generate_content(prompt)
                    st.session_state.last_analysis = response.text
            
            if st.session_state.last_analysis:
                st.divider()
                st.markdown(st.session_state.last_analysis)
                st.subheader("💾 數據儲存確認")
                final_vo2 = st.number_input("確認本次推算的 VO2 Max", value=42.0, step=0.1)
                if st.button("確認存入 Google Sheets"):
                    success, msg = push_to_sheets(conn, run_date, final_vo2, run_type, gct, v_osc)
                    if success: st.success(msg)
                    else: st.error(msg)
                    
        except Exception as e:
            st.error(f"連線異常：{e}")
    else:
        st.info("👋 請輸入 API Key。")

with tab2:
    st.header("📈 $VO_2 Max$ 與技術趨勢")
    try:
        # 讀取完整數據
        df = conn.read(spreadsheet=SHEET_URL)
        if df is not None and not df.empty:
            df["日期"] = pd.to_datetime(df["日期"])
            df = df.sort_values("日期")
            
            # 1. 體能趨勢圖
            if "VO2_Max" in df.columns:
                st.subheader("體能進步趨勢 (VO2 Max)")
                st.line_chart(df.set_index("日期")["VO2_Max"])
            
            # 2. 技術指標圖
            if "GCT" in df.columns:
                st.subheader("技術指標趨勢 (觸地時間 GCT)")
                st.line_chart(df.set_index("日期")["GCT"])
            
            st.divider()
            # 3. AI 進步預測
            if len(df) >= 3:
                if st.button("生成 AI 進步預測報告"):
                    history_str = df.tail(10).to_string()
                    pred_res = model.generate_content(f"分析此數據並給予下月預測：\n{history_str}")
                    st.info(pred_res.text)
            else:
                st
