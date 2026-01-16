import streamlit as st
import google.generativeai as genai
import pandas as pd
import datetime
import os

# --- 檔案設定 ---
DATA_FILE = "running_history.csv"

def save_data(date, vo2max, run_type):
    new_data = pd.DataFrame([[str(date), vo2max, run_type]], columns=["日期", "VO2_Max", "類型"])
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df = new_data
    df.to_csv(DATA_FILE, index=False)

# --- 介面設定 ---
st.set_page_config(page_title="建希的運動投資儀表板", layout="wide")
st.title("🏃‍♂️ 跑步數據與 $VO_2 Max$ 長期追蹤 (v2.5)")

api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")

# --- 主畫面分頁 ---
tab1, tab2 = st.tabs(["數據推算", "歷史分析與趨勢"])

with tab1:
    if api_key:
        try:
            genai.configure(api_key=api_key)
            
            # --- 核心修正：對接你清單中的 gemini-2.5-flash ---
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            st.success("✅ 已連結至 Gemini 2.5 Flash 尖端引擎！")
            
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                weight = st.number_input("體重 (kg)", value=80.0)
                max_hr = st.number_input("最大心率 (bpm)", value=190)
            with col2:
                run_date = st.date_input("訓練日期", datetime.date.today())
                run_type = st.selectbox("訓練類型", ["間歇跑 (Interval)", "穩定跑 (E/M/T)"])

            raw_data = st.text_area("請貼上 Lap 數據", height=150)

            if st.button("開始 AI 分析"):
                with st.spinner("Gemini 2.5 正在全速分析中..."):
                    prompt = f"你是一位跑者教練。分析數據並推算 VO2 Max。體重{weight}kg, 最大心率{max_hr}。數據：{raw_data}"
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                
                st.divider()
                st.subheader("確認存檔區")
                final_vo2 = st.number_input("請確認推算的 VO2 Max", value=42.0, step=0.1)
                if st.button("確認存入雲端資料庫"):
                    save_data(run_date, final_vo2, run_type)
                    st.success(f"已記錄！請到分頁查看成長曲線。")
                    
        except Exception as e:
            st.error(f"連線異常：{e}")
    else:
        st.info("👋 你好建希！請在左側邊欄輸入 API Key。")

with tab2:
    st.header("📈 $VO_2 Max$ 成長曲線")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = df.sort_values("日期")
        st.line_chart(df.set_index("日期")["VO2_Max"])
        st.table(df)
    else:
        st.write("目前尚無數據。")
