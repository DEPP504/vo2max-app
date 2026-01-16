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

# --- 介面設定 (移除姓名) ---
st.set_page_config(page_title="AI 全能運動教練", layout="wide")
st.title("🏃‍♂️ 跑步生理數據與 $VO_2 Max$ 長期分析系統")

api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")

# --- 主畫面分頁 ---
tab1, tab2 = st.tabs(["數據推算", "趨勢分析"])

with tab1:
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            st.success("✅ 雲端引擎連線成功")
            
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                weight = st.number_input("體重 (kg)", value=70.0)
                max_hr = st.number_input("最大心率 (bpm)", value=190)
                rest_hr = st.number_input("安靜心率 (bpm)", value=55) # 新增欄位
            with col2:
                run_date = st.date_input("訓練日期", datetime.date.today())
                run_type = st.selectbox("訓練類型", ["間歇跑 (Interval)", "穩定跑 (E/M/T)"])

            raw_data = st.text_area("請貼上 Lap 數據", height=150)

            if st.button("開始 AI 數據分析"):
                with st.spinner("正在根據生理指標進行深度計算..."):
                    prompt = f"""
                    你是一位專業運動科學教練。請分析以下數據：
                    - 生理指標：體重{weight}kg, 最大心率{max_hr}bpm, 安靜心率{rest_hr}bpm。
                    - 跑步數據：{raw_data}
                    
                    請執行：
                    1. 根據心率儲備量 (HRR = MHR - RHR) 分析間歇段強度。
                    2. 使用效率法推算一個具體的 VO2 Max 數字。
                    3. 提供針對性建議。
                    """
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                
                st.divider()
                st.subheader("數據儲存確認")
                final_vo2 = st.number_input("請輸入 AI 推算的數字以便記錄", value=42.0, step=0.1)
                if st.button("點擊存入雲端數據庫"):
                    save_data(run_date, final_vo2, run_type)
                    st.success(f"紀錄已存入！請切換至『趨勢分析』分頁。")
                    
        except Exception as e:
            st.error(f"系統錯誤：{e}")
    else:
        st.info("👋 歡迎使用！請在左側輸入 API Key 以開啟 AI 教練功能。")

with tab2:
    st.header("📈 $VO_2 Max$ 進步曲線")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = df.sort_values("日期")
        st.line_chart(df.set_index("日期")["VO2_Max"])
        st.table(df)
    else:
        st.write("目前尚未有紀錄，請先完成一次分析。")
